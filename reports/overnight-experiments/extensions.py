"""Versioned Terra comparison and authenticated-evidence diagnostics (40 games)."""

import argparse
import asyncio
import hashlib
import json
import math
import os
import random
import socket
import subprocess
import threading
import urllib.error
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from swarm_lab.evacuation.dataset import Scenario, load_dataset
from swarm_lab.evacuation.evidence import EVIDENCE_INSTRUCTIONS, EvidenceGame
from swarm_lab.evacuation.language import (
    DECISION_SCHEMA,
    LanguageGame,
    TextPolicy,
    append,
)
from swarm_lab.evacuation.openrouter import OpenRouterBackend
from swarm_lab.settings import Settings

MODELS = {
    "sonnet": ("anthropic/claude-sonnet-5.5", "google-vertex/global", "Google", 2, 10),
    "terra": ("openai/gpt-6.1-terra", "openai", "OpenAI", 1, 5),
}
RESERVATION = 0.20


def now():
    return datetime.now(timezone.utc).isoformat()


def build_jobs():
    result = []
    scenarios = load_dataset(Path("data/diagnostics-v2/scenarios.jsonl"))
    for section in ("terra", "4", "5"):
        batch = []
        for s in scenarios:
            if section == "terra" and s.seed != 1000:
                continue
            if section != "terra" and s.accurate:
                continue
            models = ["terra"] if section == "terra" else list(MODELS)
            langs = ["en", "vi"] if section == "terra" else ["en"]
            arms = (
                ["baseline"]
                if section == "terra"
                else ["none", "broadcast"]
                if section == "4"
                else ["private_text", "private_proof"]
            )
            for model in models:
                for lang in langs:
                    for arm in arms:
                        batch.append(
                            dict(
                                id=f"{section}-{s.id}-{model}-{arm}-{lang}",
                                section=section,
                                scenario=asdict(s),
                                model_tag=model,
                                language=lang,
                                arm=arm,
                            )
                        )
        random.Random("diagnostics-20261109-" + section).shuffle(batch)
        result.extend(batch)
    return result


def jobs():
    rows = [
        json.loads(x)
        for x in Path("data/diagnostics-v2/conditions.jsonl").read_text().splitlines()
    ]
    if rows != build_jobs():
        raise ValueError("Committed conditions differ from the balanced design")
    return rows


def freeze(original):
    entries = [
        json.loads(x) for x in (original / "budget.jsonl").read_text().splitlines()
    ]
    pending = set()
    spent = 0
    for e in entries:
        if e["type"] == "reserve":
            pending.add(e["ticket"])
        if e["type"] == "settle":
            pending.remove(e["ticket"])
            spent += e["cost"]
    if pending:
        raise ValueError("Original collection has unresolved billing")
    paths = [
        Path("src/swarm_lab/evacuation") / p
        for p in [
            "engine.py",
            "dataset.py",
            "language.py",
            "conditions.py",
            "evidence.py",
            "openrouter.py",
        ]
    ]
    paths.append(Path(__file__).relative_to(Path.cwd()))
    paths += [
        Path("data/diagnostics-v2/scenarios.jsonl"),
        Path("data/diagnostics-v2/conditions.jsonl"),
    ]
    return dict(
        protocol="evidence-diagnostics-v2",
        original_reported_usd=spent,
        original_ledger_sha256=hashlib.sha256(
            (original / "budget.jsonl").read_bytes()
        ).hexdigest(),
        global_cap_usd=35,
        extension_cap_usd=35 - spent,
        per_call_reservation_usd=RESERVATION,
        reasoning="low",
        temperature="provider_controlled",
        output_tokens=2048,
        input_byte_cap=64000,
        max_calls_per_game=54,
        concurrency=4,
        retries=0,
        models=MODELS,
        jobs=jobs(),
        review="Exploratory; draft language packs",
        schema=DECISION_SCHEMA,
        evidence_instructions=EVIDENCE_INSTRUCTIONS,
        packs_sha256=hashlib.sha256(
            Path("data/experiment1/languages.json").read_bytes()
        ).hexdigest(),
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
        hypotheses=dict(
            experiment4=(
                "Broadcast authenticated truth changes appropriate action "
                "relative to same-prompt no-evidence control"
            ),
            control_criterion=(
                "For each model/seed: >=8/9 evacuate on verified Danger "
                "and <=1/9 evacuate on verified Safe"
            ),
            experiment5=(
                "Proof-preserving local transport improves non-witness action "
                "relative to private-evidence text-only forwarding"
            ),
            inference=(
                "Descriptive pilot; no general safety, equivalence or novelty claim"
            ),
        ),
    )


class Budget:
    def __init__(self, root, cap):
        self.path, self.cap, self.lock = root / "budget.jsonl", cap, threading.Lock()
        self.spent, self.pending, self.halted = 0.0, {}, False
        if self.path.exists():
            for e in [json.loads(x) for x in self.path.read_text().splitlines()]:
                if e["type"] == "reserve":
                    self.pending[e["ticket"]] = RESERVATION
                elif e["type"] == "settle":
                    self.pending.pop(e["ticket"])
                    self.spent += e["cost"]
                elif e["type"] == "halt":
                    self.halted = True
        self.halted |= bool(self.pending)

    def reserve(self, ticket, payload, model):
        with self.lock:
            if (
                self.halted
                or self.spent + sum(self.pending.values()) + RESERVATION > self.cap
            ):
                raise RuntimeError("Budget guard: cap or uncertain billing")
            _, _, _, prompt, completion = MODELS[model]
            payload["provider"]["max_price"] = dict(
                prompt=prompt, completion=completion
            )
            self.pending[ticket] = RESERVATION
            append(
                self.path,
                dict(type="reserve", ticket=ticket, at=now(), usd=RESERVATION),
            )

    def settle(self, ticket, cost, **detail):
        with self.lock:
            if (
                not isinstance(cost, (int, float))
                or not math.isfinite(cost)
                or not 0 <= cost <= RESERVATION
            ):
                self.halted = True
                append(
                    self.path,
                    dict(type="halt", ticket=ticket, at=now(), reason="invalid cost"),
                )
                raise RuntimeError("Invalid provider cost")
            self.pending.pop(ticket)
            self.spent += cost
            append(
                self.path,
                dict(type="settle", ticket=ticket, at=now(), cost=cost, **detail),
            )


async def main(args):
    args.root.mkdir(parents=True, exist_ok=True)
    plan = freeze(args.original)
    path = args.root / "plan.json"
    if path.exists() and json.loads(path.read_text()) != json.loads(json.dumps(plan)):
        raise RuntimeError(
            "Frozen extension sources/plan changed; create a new version"
        )
    path.write_text(json.dumps(plan, indent=2))
    if args.plan_only:
        print(
            json.dumps(
                dict(
                    games=len(plan["jobs"]),
                    original_usd=plan["original_reported_usd"],
                    remaining_cap=plan["extension_cap_usd"],
                )
            )
        )
        return
    load_dotenv()
    key = os.environ["OPENROUTER_API_KEY"]
    packs = json.loads(Path("data/experiment1/languages.json").read_text())
    budget = Budget(args.root, plan["extension_cap_usd"])
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
                started_at=now(),
                decision_attempts=0,
                git_commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                protocol=plan["protocol"],
            )
            manifest = folder / "manifest.json"
            manifest.write_text(json.dumps(m, indent=2))
            model, provider, returned_provider, _, _ = MODELS[j["model_tag"]]
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
                                at=now(),
                                reason="routing/generation mismatch",
                            ),
                        )
                        raise RuntimeError("Routing/generation mismatch")

            pack = dict(packs[j["language"]])
            if j["section"] != "terra":
                pack["instructions"] += "\n\n" + EVIDENCE_INSTRUCTIONS
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
            if j["section"] == "terra":
                game = LanguageGame(scenario, j["language"], pack)
            else:
                evidence = "private" if j["section"] == "5" else j["arm"]
                forwarding = "proof" if j["arm"] == "private_proof" else "text_only"
                game = EvidenceGame(
                    scenario,
                    j["language"],
                    pack,
                    evidence=evidence,
                    forwarding=forwarding,
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
                                at=now(),
                                reason="uncertain request outcome",
                            ),
                        )
            finally:
                m.update(decision_attempts=policy.calls, finished_at=now())
                manifest.write_text(json.dumps(m, indent=2))
                print(
                    j["id"], m["status"], f"extension=${budget.spent:.4f}", flush=True
                )

    await asyncio.gather(
        *(job(j) for j in plan["jobs"] if j["section"] == args.section)
    )
    print(
        "SECTION",
        args.section,
        "extension cost",
        budget.spent,
        "pending",
        len(budget.pending),
        "halted",
        budget.halted,
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("runs/evidence-diagnostics-v2"))
    p.add_argument("--original", type=Path, default=Path("runs/overnight-v1"))
    p.add_argument("--section", choices=["terra", "4", "5"], default="terra")
    p.add_argument("--plan-only", action="store_true")
    asyncio.run(main(p.parse_args()))
