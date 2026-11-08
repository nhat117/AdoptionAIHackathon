"""Run with python -m swarm_lab.evacuation --help."""

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from adaption import AsyncAdaption
from dotenv import load_dotenv

from ..backend import AdaptionBackend
from ..settings import Settings
from .dataset import generate, load_dataset, write_dataset
from .engine import A_ARMS, C_ARMS, Game, state_hash
from .openrouter import OpenRouterBackend
from .policies import INSTRUCTIONS, FixturePolicy, LivePolicy
from .stimuli import load_stimulus


def append(path, record):
    with path.open("a") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


async def execute(args, policy, output):
    rows = [s for s in load_dataset(args.dataset) if s.split == args.split]
    if args.scenario_id:
        rows = [s for s in rows if s.id == args.scenario_id]
    if args.study == "C":
        rows = [s for s in rows if not s.accurate]
    rows = rows[: args.limit]
    if not rows:
        raise ValueError("No matching scenarios")
    stimulus = None
    if args.stimuli:
        stimulus = load_stimulus(
            args.stimuli, args.stimulus_index, args.split, args.allow_unreviewed_stimuli
        )
    completed = 0
    for scenario in rows:
        if args.study == "A":
            arms = [args.arm] if args.arm else A_ARMS
            games = [(arm, Game(scenario, "A", arm, stimulus), None) for arm in arms]
        else:
            exposure = Game(scenario, "C", "none", stimulus)
            # Build ONE shared exposure, then copy it for every intervention.
            for _ in range(2):
                trace = await exposure.step(policy)
                append(
                    output / "traces.jsonl",
                    {"scenario": scenario.id, "arm": "shared_exposure", **trace},
                )
            snapshot = state_hash(exposure.state)
            (output / f"{scenario.id}-fork.json").write_text(
                json.dumps(
                    {"hash": snapshot, "state": asdict(exposure.state)},
                    default=lambda x: sorted(x),
                    sort_keys=True,
                )
            )
            arms = [args.arm] if args.arm else C_ARMS
            games = [(arm, exposure.fork(arm), snapshot) for arm in arms]
        for arm, game, snapshot in games:
            while game.state.round < scenario.terminal_round:
                trace = await game.step(policy)
                append(
                    output / "traces.jsonl",
                    {"scenario": scenario.id, "arm": arm, **trace},
                )
            append(
                output / "outcomes.jsonl",
                {
                    "scenario": asdict(scenario),
                    "study": args.study,
                    "arm": arm,
                    "mode": args.mode,
                    "shared_snapshot_hash": snapshot,
                    "status": "completed",
                    **game.outcomes(),
                },
            )
            completed += 1
            print(f"Completed {scenario.id} {arm}", flush=True)
    return completed


async def run(args):
    if args.limit < 1 or args.max_calls < 1:
        raise ValueError("Limits must be positive")
    if args.arm and args.arm not in (A_ARMS if args.study == "A" else C_ARMS):
        raise ValueError("Arm does not belong to selected study")
    settings = Settings.load(args.config)
    # Refuse existing directories: no silent overwrite or mixed trials.
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "args": {
            k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()
        },
        "settings": asdict(settings),
        "adaption_sdk_version": version("adaption"),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "prompt_sha256": hashlib.sha256(INSTRUCTIONS.encode()).hexdigest(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "working_tree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        ),
        "stimuli_sha256": hashlib.sha256(args.stimuli.read_bytes()).hexdigest()
        if args.stimuli
        else None,
        "status": "running",
        "research_results": False,
    }
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    policy = FixturePolicy()
    try:
        if args.mode == "live":
            load_dotenv()

            def record(item):
                append(args.output / "calls.jsonl", item)

            if args.provider == "openrouter":
                key = os.getenv("OPENROUTER_API_KEY")
                if not key:
                    raise ValueError("Configure OPENROUTER_API_KEY in local .env")
                policy = LivePolicy(
                    OpenRouterBackend(key, settings, record), args.max_calls, record
                )
                count = await execute(args, policy, args.output)
            else:
                if not os.getenv("ADAPTION_API_KEY"):
                    raise ValueError("Configure ADAPTION_API_KEY in local .env")
                async with AsyncAdaption(max_retries=0, timeout=30) as client:
                    policy = LivePolicy(
                        AdaptionBackend(client, settings, record),
                        args.max_calls,
                        record,
                    )
                    count = await execute(args, policy, args.output)
        else:
            count = await execute(args, policy, args.output)
        manifest.update(status="completed", completed_episodes=count)
    except Exception as exc:
        manifest.update(status="failed", error_type=type(exc).__name__)
        raise
    finally:
        manifest["model_calls"] = policy.calls
        manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
        manifest_path.write_text(json.dumps(manifest, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("dataset")
    build.add_argument(
        "--output", type=Path, default=Path("data/evacuation/scenarios.jsonl")
    )
    build.add_argument("--blocks", type=int, default=5)
    runner = sub.add_parser("run")
    runner.add_argument(
        "--dataset", type=Path, default=Path("data/evacuation/scenarios.jsonl")
    )
    runner.add_argument("--config", type=Path, default=Path("examples/evacuation.json"))
    runner.add_argument("--study", choices=["A", "C"], required=True)
    runner.add_argument(
        "--provider", choices=["adaption", "openrouter"], default="adaption"
    )
    runner.add_argument("--arm")
    runner.add_argument("--scenario-id")
    runner.add_argument("--stimuli", type=Path)
    runner.add_argument("--stimulus-index", type=int, default=0)
    runner.add_argument("--allow-unreviewed-stimuli", action="store_true")
    runner.add_argument("--mode", choices=["offline", "live"], default="offline")
    runner.add_argument(
        "--split", choices=["calibration", "evaluation"], default="calibration"
    )
    runner.add_argument("--limit", type=int, default=1)
    runner.add_argument("--max-calls", type=int, default=100)
    runner.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "dataset":
        if args.blocks < 1:
            parser.error("blocks must be positive")
        write_dataset(args.output, generate(args.blocks))
        print(f"Wrote {args.blocks * 8} synthetic scenarios to {args.output}")
    else:
        asyncio.run(run(args))


if __name__ == "__main__":
    main()
