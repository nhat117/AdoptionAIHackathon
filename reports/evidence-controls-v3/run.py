"""Evidence controls v3 (72 games): unverified-capsule and delayed-truth arms.

Section 5b reruns Experiment 5 with a content-matched unverified capsule on
held-out seeds. Section 6 delivers authenticated truth one round after the
false claim. Both reuse the v2 budget guard, routes and reservation rules.
"""

import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
import random
import socket
import subprocess
import urllib.error
from dataclasses import asdict
from pathlib import Path

from dotenv import load_dotenv

from swarm_lab.evacuation.dataset import Scenario, load_dataset
from swarm_lab.evacuation.evidence_v3 import EVIDENCE_INSTRUCTIONS_V3, EvidenceGameV3
from swarm_lab.evacuation.language import DECISION_SCHEMA, TextPolicy, append
from swarm_lab.evacuation.openrouter import OpenRouterBackend
from swarm_lab.settings import Settings

_spec = importlib.util.spec_from_file_location(
    "extensions_v2", Path(__file__).parents[1] / "overnight-experiments/extensions.py"
)
v2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v2)

DATA = Path("data/evidence-controls-v3")
GLOBAL_CAP = 35
ARMS = {
    "5b": {
        "private_text": ("private", "text_only"),
        "private_unverified": ("private", "unverified"),
        "private_proof": ("private", "proof"),
    },
    "6": {"none": ("none", "text_only"), "delayed": ("delayed", "text_only")},
}


def build_jobs():
    scenarios = load_dataset(DATA / "scenarios.jsonl")
    result = []
    for section in ("5b", "6"):
        batch = []
        for s in scenarios:
            if section == "5b" and not s.disaster:
                continue  # Truthful-capsule effect is only visible under Danger.
            if section == "6" and s.seed > 2003:
                continue
            for model in ["sonnet", "terra"]:
                if section == "6" and model == "sonnet" and not s.disaster:
                    # Sonnet stayed in every unverified false-Danger game, so
                    # late Safe truth has nothing to change; spend on Terra.
                    continue
                for arm in ARMS[section]:
                    batch.append(
                        dict(
                            id=f"{section}-{s.id}-{model}-{arm}-en",
                            section=section,
                            scenario=asdict(s),
                            model_tag=model,
                            language="en",
                            arm=arm,
                        )
                    )
        random.Random("evidence-controls-v3-" + section).shuffle(batch)
        result.extend(batch)
    return result


def jobs():
    rows = [json.loads(x) for x in (DATA / "conditions.jsonl").read_text().splitlines()]
    if rows != build_jobs():
        raise ValueError("Committed conditions differ from the balanced design")
    return rows


def ledger_spent(path):
    """Settled spend of a prior collection; refuse unresolved reservations."""
    pending, spent = set(), 0.0
    for e in [json.loads(x) for x in path.read_text().splitlines()]:
        if e["type"] == "reserve":
            pending.add(e["ticket"])
        elif e["type"] == "settle":
            pending.remove(e["ticket"])
            spent += e["cost"]
    if pending:
        raise ValueError(f"{path} has unresolved billing")
    return spent


def freeze(ledgers):
    prior = {str(p): ledger_spent(p) for p in ledgers}
    paths = [
        Path("src/swarm_lab/evacuation") / p
        for p in [
            "engine.py",
            "dataset.py",
            "language.py",
            "conditions.py",
            "evidence.py",
            "evidence_v3.py",
            "openrouter.py",
        ]
    ]
    paths += [
        Path(__file__).relative_to(Path.cwd()),
        Path("reports/overnight-experiments/extensions.py"),
        DATA / "scenarios.jsonl",
        DATA / "conditions.jsonl",
    ]
    return dict(
        protocol="evidence-controls-v3",
        prior_reported_usd=prior,
        global_cap_usd=GLOBAL_CAP,
        v3_cap_usd=GLOBAL_CAP - sum(prior.values()),
        per_call_reservation_usd=v2.RESERVATION,
        reasoning="low",
        temperature="provider_controlled",
        output_tokens=2048,
        input_byte_cap=64000,
        max_calls_per_game=54,
        concurrency=4,
        retries=0,
        models=v2.MODELS,
        jobs=jobs(),
        review="Exploratory; English only",
        schema=DECISION_SCHEMA,
        evidence_instructions=EVIDENCE_INSTRUCTIONS_V3,
        packs_sha256=hashlib.sha256(
            Path("data/experiment1/languages.json").read_bytes()
        ).hexdigest(),
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
        hypotheses=dict(
            section_5b=(
                "Under Danger, non-witness correct action is higher with "
                "authenticated capsules than with content-matched unverified "
                "capsules; unverified is compared with text-only to separate "
                "content from authentication"
            ),
            section_6=(
                "Authenticated truth delivered in round two reverses round-one "
                "stays under Danger and prevents later unnecessary evacuation "
                "under Safe, relative to the same-prompt no-evidence control"
            ),
            unit="Whole game; seeds are the replication unit",
            inference="Descriptive with exact permutation test over seeds",
        ),
    )


async def main(args):
    args.root.mkdir(parents=True, exist_ok=True)
    plan = freeze(args.ledger)
    path = args.root / "plan.json"
    if path.exists() and json.loads(path.read_text()) != json.loads(json.dumps(plan)):
        raise RuntimeError("Frozen v3 sources/plan changed; create a new version")
    path.write_text(json.dumps(plan, indent=2))
    selected = [
        j
        for j in plan["jobs"]
        if j["section"] == args.section
        and (args.model is None or j["model_tag"] == args.model)
    ]
    if args.plan_only:
        print(
            json.dumps(
                dict(
                    games=len(plan["jobs"]),
                    selected=len(selected),
                    prior_usd=plan["prior_reported_usd"],
                    remaining_cap=plan["v3_cap_usd"],
                )
            )
        )
        return
    load_dotenv()
    key = os.environ["OPENROUTER_API_KEY"]
    packs = json.loads(Path("data/experiment1/languages.json").read_text())
    budget = v2.Budget(args.root, plan["v3_cap_usd"])
    sem = asyncio.Semaphore(4)

    async def job(j):
        async with sem:
            folder = args.root / j["id"]
            if folder.exists() or budget.halted:
                return
            folder.mkdir()
            m = dict(
                **j,
                status="running",
                started_at=v2.now(),
                decision_attempts=0,
                git_commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                protocol=plan["protocol"],
            )
            manifest = folder / "manifest.json"
            manifest.write_text(json.dumps(m, indent=2))
            model, provider, returned_provider, _, _ = v2.MODELS[j["model_tag"]]
            count, ticket = 0, None

            def before(payload):
                nonlocal count, ticket
                count += 1
                ticket = j["id"] + ":" + str(count)
                budget.reserve(ticket, payload, j["model_tag"])

            def record(item):
                append(folder / "calls.jsonl", item)
                if item["type"] == "provider_metadata":
                    budget.settle(ticket, (item.get("usage") or {}).get("cost"))
                    if (
                        item["upstream_provider"] != returned_provider
                        or item["model"] != model
                        or item["requested_reasoning_effort"] != "low"
                        or item["requested_provider"].get("only") != [provider]
                        or "max_price" not in item["requested_provider"]
                    ):
                        budget.halted = True
                        append(
                            budget.path,
                            dict(
                                type="halt",
                                at=v2.now(),
                                reason="routing/generation mismatch",
                            ),
                        )
                        raise RuntimeError("Routing/generation mismatch")

            pack = dict(packs[j["language"]])
            pack["instructions"] += "\n\n" + EVIDENCE_INSTRUCTIONS_V3
            backend = OpenRouterBackend(
                key,
                Settings(model=model, max_output_tokens=2048),
                record,
                reasoning_effort="low",
                max_prompt_bytes=64000,
                response_schema=DECISION_SCHEMA,
                provider_only=provider,
                provider_ignore=["openai/flex", "openai/fast"]
                if j["model_tag"] == "terra"
                else None,
                before_request=before,
            )
            scenario = Scenario(**j["scenario"])
            evidence, forwarding = ARMS[j["section"]][j["arm"]]
            game = EvidenceGameV3(
                scenario, j["language"], pack, evidence=evidence, forwarding=forwarding
            )
            policy = TextPolicy(pack, backend, 54, record)
            try:
                while game.state.round < scenario.terminal_round:
                    append(folder / "traces.jsonl", await game.step(policy))
                (folder / "outcome.json").write_text(
                    json.dumps(game.outcomes(), indent=2)
                )
                m["status"] = "completed"
            except Exception as exc:
                m.update(
                    status="failed", error_type=type(exc).__name__, error=str(exc)[:240]
                )
                if ticket in budget.pending:
                    if isinstance(exc, urllib.error.URLError) and isinstance(
                        exc.reason, socket.gaierror
                    ):
                        budget.settle(
                            ticket,
                            0,
                            reconciliation="verified_preconnect_dns",
                            errno=exc.reason.errno,
                        )
                    else:
                        budget.halted = True
                        append(
                            budget.path,
                            dict(
                                type="halt",
                                ticket=ticket,
                                at=v2.now(),
                                reason="uncertain request outcome",
                            ),
                        )
            finally:
                m.update(decision_attempts=policy.calls, finished_at=v2.now())
                manifest.write_text(json.dumps(m, indent=2))
                print(j["id"], m["status"], f"v3=${budget.spent:.4f}", flush=True)

    await asyncio.gather(*(job(j) for j in selected))
    print(
        "SECTION",
        args.section,
        "v3 cost",
        budget.spent,
        "pending",
        len(budget.pending),
        "halted",
        budget.halted,
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("runs/evidence-controls-v3"))
    p.add_argument(
        "--ledger",
        type=Path,
        nargs="+",
        default=[
            Path("runs/restored-review/original/budget.jsonl"),
            Path("runs/restored-review/extensions/budget.jsonl"),
        ],
        help="Every prior budget ledger that counts toward the US$35 cap",
    )
    p.add_argument("--section", choices=list(ARMS), default="5b")
    p.add_argument("--model", choices=list(v2.MODELS))
    p.add_argument("--plan-only", action="store_true")
    asyncio.run(main(p.parse_args()))
