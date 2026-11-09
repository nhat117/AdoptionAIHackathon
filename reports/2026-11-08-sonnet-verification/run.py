"""Bounded four-game technical implementation verification, not inference research."""

import asyncio
import json
from argparse import Namespace
from pathlib import Path

from swarm_lab.evacuation.language import run

ROOT = Path("runs/sonnet-verification-20261108")


async def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    rows = [
        json.loads(x)
        for x in Path("data/evacuation/scenarios.jsonl").read_text().splitlines()
    ]
    rows = [
        s for s in rows if s["id"] in ["calibration-000-0-0", "calibration-000-1-1"]
    ]
    plan = {
        "goal": "Verify the matched four-game protocol on a second model",
        "purpose": "technical_implementation_verification",
        "model": "anthropic/claude-sonnet-5.5",
        "reasoning": "low",
        "temperature": "provider_controlled",
        "max_output_tokens": 2048,
        "games": 4,
        "max_calls_per_game": 45,
        "max_total_calls": 180,
        "languages": ["en", "vi"],
        "reported_cost_stop_usd": 3,
        "note": (
            "Legacy split calibration; purpose technical verification. "
            "Draft translations; no language-ranking claims."
        ),
    }
    (ROOT / "plan.json").write_text(json.dumps(plan, indent=2))
    # Two games concurrently. Refuse further games if recorded spend reaches $3.
    sem = asyncio.Semaphore(2)

    async def job(s, lang):
        async with sem:
            cost = 0
            for path in ROOT.glob("*/calls.jsonl"):
                for line in path.read_text().splitlines():
                    item = json.loads(line)
                    if item["type"] == "provider_metadata":
                        cost += (item.get("usage") or {}).get("cost", 0) or 0
            if cost >= 3:
                return
            name = s["id"] + "-" + lang
            dataset = ROOT / (name + ".jsonl")
            dataset.write_text(json.dumps(s) + "\n")
            args = Namespace(
                dataset=dataset,
                packs=Path("data/experiment1/languages.json"),
                languages=[lang],
                mode="live",
                provider="openrouter",
                model="anthropic/claude-sonnet-5.5",
                split="calibration",
                limit=1,
                max_calls=45,
                max_output_tokens=2048,
                allow_unreviewed=True,
                output=ROOT / name,
            )
            try:
                await asyncio.wait_for(run(args), timeout=900)
                print(name, "completed", flush=True)
            except Exception as exc:
                print(name, "failed", type(exc).__name__, flush=True)

    await asyncio.gather(*(job(s, language) for s in rows for language in ["en", "vi"]))


if __name__ == "__main__":
    asyncio.run(main())
