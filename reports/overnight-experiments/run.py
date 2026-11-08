"""Frozen bounded pilot. Resume skips every attempted game, including failures."""

import argparse
import asyncio
import hashlib
import json
import math
import os
import random
import subprocess
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from swarm_lab.evacuation.conditions import IDENTITIES
from swarm_lab.evacuation.dataset import generate
from swarm_lab.evacuation.language import (
    DECISION_SCHEMA,
    LanguageGame,
    TextPolicy,
    append,
)
from swarm_lab.evacuation.openrouter import OpenRouterBackend
from swarm_lab.settings import Settings

REPORT = Path(__file__).resolve().parent
MODEL = "anthropic/claude-sonnet-5.5"
PROVIDER = "google-vertex/global"
RESERVATION = 0.20  # 64K prompt bytes + 2048 output tokens, above verified prices.


def now():
    return datetime.now(timezone.utc).isoformat()


def jobs():
    rows = [s for s in generate(2) if s.split == "calibration"]
    result = []
    for section in (1, 2, 3):
        batch = []
        for s in rows:
            for lang in ("en", "vi"):
                identities = IDENTITIES[1:] if section == 2 else ("ordinary_peer",)
                if section == 2 and s.seed != 1000:
                    continue
                for identity in identities:
                    topology = "random_regular" if section == 3 else "ring"
                    batch.append(
                        dict(
                            section=section,
                            scenario=asdict(s),
                            language=lang,
                            identity=identity,
                            topology=topology,
                        )
                    )
        random.Random(20261109 + section).shuffle(batch)
        for j in batch:
            j["id"] = "-".join(
                [
                    str(section),
                    j["scenario"]["id"],
                    j["language"],
                    j["identity"],
                    j["topology"],
                ]
            )
        result.extend(batch)
    return result


def freeze():
    packs = Path("data/experiment1/languages.json")
    sources = [
        Path("src/swarm_lab/evacuation") / n
        for n in (
            "language.py",
            "conditions.py",
            "engine.py",
            "dataset.py",
            "openrouter.py",
        )
    ]
    sources += [Path(__file__).relative_to(Path.cwd())]
    return dict(
        protocol="swarm-exploratory-v1",
        purpose="exploratory_unreviewed_pilot",
        model=MODEL,
        provider_only=PROVIDER,
        reasoning="low",
        max_output_tokens=2048,
        max_calls_per_game=54,
        max_prompt_bytes=64000,
        budget_usd=35,
        per_call_reservation_usd=RESERVATION,
        concurrency=4,
        retries=0,
        independent_scenario_seeds=[1000, 1001],
        identity_seeds=[1000],
        language_review="pending_manual_review",
        research_results=False,
        shared_baselines="Experiment 1 ring ordinary-peer games reused by 2 and 3",
        graph_seed="scenario seed; two independently generated graphs",
        inference_limits=(
            "One model; draft translations; one draw per cell; descriptive only"
        ),
        pack_sha256=hashlib.sha256(packs.read_bytes()).hexdigest(),
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        jobs=jobs(),
    )


class Budget:
    def __init__(self, root):
        self.path = root / "budget.jsonl"
        self.lock = threading.Lock()
        self.spent, self.pending, self.halted = 0.0, {}, False
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                e = json.loads(line)
                if e["type"] == "reserve":
                    self.pending[e["ticket"]] = RESERVATION
                elif e["type"] == "settle":
                    self.pending.pop(e["ticket"])
                    self.spent += e["cost"]
                elif e["type"] == "halt":
                    self.halted = True
        # Unsettled requests may have been billed. Never replay them.
        if self.pending:
            self.halted = True

    def reserve(self, ticket, payload):
        with self.lock:
            if (
                self.halted
                or self.spent + sum(self.pending.values()) + RESERVATION > 35
            ):
                raise RuntimeError("Budget stopped or uncertain billing")
            payload["provider"]["max_price"] = {"prompt": 2, "completion": 10}
            self.pending[ticket] = RESERVATION
            append(
                self.path,
                dict(type="reserve", ticket=ticket, at=now(), usd=RESERVATION),
            )

    def settle(self, ticket, metadata):
        with self.lock:
            cost = (metadata.get("usage") or {}).get("cost")
            if (
                not isinstance(cost, (float, int))
                or not math.isfinite(cost)
                or cost < 0
                or cost > RESERVATION
                or metadata.get("upstream_provider") != "Google"
                or metadata.get("requested_reasoning_effort") != "low"
            ):
                self.halted = True
                append(
                    self.path,
                    dict(
                        type="halt",
                        ticket=ticket,
                        at=now(),
                        reason="invalid cost, provider or reasoning metadata",
                    ),
                )
                raise RuntimeError("Provider/billing audit failed")
            self.pending.pop(ticket)
            self.spent += cost
            append(self.path, dict(type="settle", ticket=ticket, at=now(), cost=cost))


async def main(args):
    root = args.root
    root.mkdir(parents=True, exist_ok=True)
    plan = freeze()
    plan_path = root / "plan.json"
    if plan_path.exists():
        if json.loads(plan_path.read_text()) != plan:
            raise ValueError(
                "Frozen code/protocol differs; use a new versioned run root"
            )
    else:
        plan_path.write_text(json.dumps(plan, indent=2))
    if args.plan_only:
        print(
            json.dumps(
                {
                    "games": len(plan["jobs"]),
                    "by_section": {
                        i: sum(j["section"] == i for j in jobs()) for i in (1, 2, 3)
                    },
                }
            )
        )
        return
    load_dotenv(args.env_file)
    key = os.environ["OPENROUTER_API_KEY"]
    packs = json.loads(Path("data/experiment1/languages.json").read_text())
    budget = Budget(root)
    sem = asyncio.Semaphore(4)

    async def job(j):
        async with sem:
            output = root / j["id"]
            if output.exists():
                print(j["id"], "already attempted; retained", flush=True)
                return
            if budget.halted:
                return
            output.mkdir()
            manifest = dict(
                **j,
                status="running",
                started_at=now(),
                model=MODEL,
                provider_only=PROVIDER,
                reasoning="low",
                calls=0,
                git_commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
            )
            manifest_path = output / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2))
            counter = 0
            ticket = None

            def before(payload):
                nonlocal counter, ticket
                counter += 1
                ticket = j["id"] + ":" + str(counter)
                budget.reserve(ticket, payload)

            def record(item):
                append(output / "calls.jsonl", item)
                if item["type"] == "provider_metadata":
                    budget.settle(ticket, item)

            backend = OpenRouterBackend(
                key,
                Settings(model=MODEL, temperature=0, max_output_tokens=2048),
                record,
                reasoning_effort="low",
                max_prompt_bytes=64000,
                response_schema=DECISION_SCHEMA,
                provider_only=PROVIDER,
                before_request=before,
            )
            from swarm_lab.evacuation.dataset import Scenario

            scenario = Scenario(**j["scenario"])
            game = LanguageGame(
                scenario,
                j["language"],
                packs[j["language"]],
                identity=j["identity"],
                topology=j["topology"],
            )
            policy = TextPolicy(packs[j["language"]], backend, 54, record)
            try:
                while game.state.round < scenario.terminal_round:
                    trace = await game.step(policy)
                    append(output / "traces.jsonl", trace)
                (output / "outcome.json").write_text(
                    json.dumps(game.outcomes(), indent=2)
                )
                manifest["status"] = "completed"
            except Exception as exc:
                manifest.update(
                    status="failed", error_type=type(exc).__name__, error=str(exc)[:200]
                )
                with budget.lock:
                    if ticket in budget.pending:
                        budget.halted = True
                        append(
                            budget.path,
                            dict(
                                type="halt",
                                at=now(),
                                ticket=ticket,
                                reason="uncertain request outcome",
                            ),
                        )
            finally:
                manifest.update(calls=policy.calls, finished_at=now())
                manifest_path.write_text(json.dumps(manifest, indent=2))
                print(
                    j["id"],
                    manifest["status"],
                    f"total=${budget.spent:.4f}",
                    flush=True,
                )

    await asyncio.gather(
        *(job(j) for j in plan["jobs"] if j["section"] == args.section)
    )
    print(
        "SECTION",
        args.section,
        "reported cost",
        budget.spent,
        "pending",
        len(budget.pending),
        "halted",
        budget.halted,
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("runs/overnight-v1"))
    p.add_argument("--env-file", type=Path, default=Path(".env"))
    p.add_argument("--section", type=int, choices=[1, 2, 3], default=1)
    p.add_argument("--plan-only", action="store_true")
    asyncio.run(main(p.parse_args()))
