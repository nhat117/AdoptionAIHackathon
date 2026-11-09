"""Influence study v4: authority ladder x warning, with private clues and beliefs.

Fixes method problems 1, 3 and 7. Every recipient has a 70%-accurate private
sensor and reports a 0-100 disaster belief each round. The source claims one of
four fictional authority levels, with the "labels carry no authority" warning
present or absent. Tier "pilot" runs the ladder's two ends; tier "ladder" adds
the middle two. Collection needs its own explicit spending cap.
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
from swarm_lab.evacuation.influence import (
    CLUE_ACCURACY,
    DECISION_SCHEMA_V4,
    LADDER,
    InfluenceGame,
    instructions,
    pack,
)
from swarm_lab.evacuation.language import TextPolicy, append
from swarm_lab.evacuation.openrouter import OpenRouterBackend
from swarm_lab.settings import Settings

_spec = importlib.util.spec_from_file_location(
    "extensions_v2", Path(__file__).parents[1] / "overnight-experiments/extensions.py"
)
v2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v2)

DATA = Path("data/influence-v4")
TIERS = {
    "pilot": ("teammate", "emergency_agency"),
    "ladder": ("team_lead", "emergency_officer"),
}


def build_jobs():
    scenarios = load_dataset(DATA / "scenarios.jsonl")
    result = []
    for tier, levels in TIERS.items():
        batch = [
            dict(
                id=f"v4-{tier}-{s.id}-{model}-{level}-{'warn' if warn else 'nowarn'}",
                section=tier,
                scenario=asdict(s),
                model_tag=model,
                language="en",
                authority=level,
                warning=warn,
            )
            for s in scenarios
            for model in v2.MODELS
            for level in levels
            for warn in (True, False)
        ]
        random.Random("influence-v4-" + tier).shuffle(batch)
        result.extend(batch)
    return result


def jobs():
    rows = [json.loads(x) for x in (DATA / "conditions.jsonl").read_text().splitlines()]
    if rows != build_jobs():
        raise ValueError("Committed conditions differ from the balanced design")
    return rows


def claims():
    return json.loads(Path("data/experiment1/languages.json").read_text())["en"][
        "claims"
    ]


def freeze(cap):
    paths = [
        Path("src/swarm_lab/evacuation") / p
        for p in [
            "engine.py",
            "dataset.py",
            "language.py",
            "influence.py",
            "stance.py",
            "openrouter.py",
        ]
    ]
    paths += [
        Path(__file__).relative_to(Path.cwd()),
        Path("reports/influence-v4/analyze.py"),
        Path("reports/overnight-experiments/extensions.py"),
        DATA / "scenarios.jsonl",
        DATA / "conditions.jsonl",
    ]
    return dict(
        protocol="influence-v4",
        cap_usd=cap,
        per_call_reservation_usd=v2.RESERVATION,
        reasoning="low",
        temperature="provider_controlled",
        output_tokens=2048,
        input_byte_cap=64000,
        max_calls_per_game=54,
        concurrency=4,
        retries=0,
        models=v2.MODELS,
        clue_accuracy=CLUE_ACCURACY,
        ladder=LADDER,
        jobs=jobs(),
        schema=DECISION_SCHEMA_V4,
        instructions={"warning": instructions(True), "no_warning": instructions(False)},
        claims=claims(),
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
        analysis_plan_sha256=hashlib.sha256(
            Path("reports/influence-v4/ANALYSIS_PLAN.md").read_bytes()
        ).hexdigest(),
    )


async def main(args):
    if args.cap_usd is not None and args.cap_usd <= 0:
        raise ValueError("Cap must be positive")
    selected = [
        j
        for j in jobs()
        if j["section"] == args.tier
        and (args.model is None or j["model_tag"] == args.model)
    ]
    if args.plan_only:
        print(json.dumps(dict(games=len(jobs()), selected=len(selected))))
        return
    if args.cap_usd is None:
        raise ValueError("Paid collection needs an explicitly authorized --cap-usd")
    args.root.mkdir(parents=True, exist_ok=True)
    plan = freeze(args.cap_usd)
    path = args.root / "plan.json"
    if path.exists() and json.loads(path.read_text()) != json.loads(json.dumps(plan)):
        raise RuntimeError("Frozen v4 sources/plan changed; create a new version")
    path.write_text(json.dumps(plan, indent=2))
    load_dotenv()
    key = os.environ["OPENROUTER_API_KEY"]
    budget = v2.Budget(args.root, plan["cap_usd"])
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

            game_pack = pack(j["warning"], plan["claims"])
            backend = OpenRouterBackend(
                key,
                Settings(model=model, max_output_tokens=2048),
                record,
                reasoning_effort="low",
                max_prompt_bytes=64000,
                response_schema=DECISION_SCHEMA_V4,
                provider_only=provider,
                provider_ignore=["openai/flex", "openai/fast"]
                if j["model_tag"] == "terra"
                else None,
                before_request=before,
            )
            scenario = Scenario(**j["scenario"])
            game = InfluenceGame(
                scenario,
                "en",
                game_pack,
                authority=j["authority"],
                warning=j["warning"],
            )
            policy = TextPolicy(game_pack, backend, 54, record)
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
                print(j["id"], m["status"], f"v4=${budget.spent:.4f}", flush=True)

    await asyncio.gather(*(job(j) for j in selected))
    print(
        "TIER",
        args.tier,
        "v4 cost",
        budget.spent,
        "pending",
        len(budget.pending),
        "halted",
        budget.halted,
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("runs/influence-v4"))
    p.add_argument("--tier", choices=list(TIERS), default="pilot")
    p.add_argument("--model", choices=list(v2.MODELS))
    p.add_argument(
        "--cap-usd",
        type=float,
        help="Newly authorized v4 spend; separate from the exhausted US$35 cap",
    )
    p.add_argument("--plan-only", action="store_true")
    asyncio.run(main(p.parse_args()))
