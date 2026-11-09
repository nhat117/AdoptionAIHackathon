import asyncio
import json
import random
from argparse import Namespace
from pathlib import Path

from swarm_lab.evacuation.language import run

ROOT = Path("runs/experiment1-gpt-calibration-20261108")
ROOT.mkdir(parents=True, exist_ok=False)
rows = [
    json.loads(x)
    for x in Path("data/evacuation/scenarios.jsonl").read_text().splitlines()
    if json.loads(x)["split"] == "calibration"
][:4]
jobs = [(s, language) for s in rows for language in ["en", "vi"]]
random.Random(8112026).shuffle(jobs)
(ROOT / "plan.json").write_text(
    json.dumps(
        {
            "model": "openai/gpt-4.1-mini",
            "provider": "openrouter",
            "episodes": 8,
            "max_calls_per_episode": 54,
            "max_total_calls": 432,
            "draft_translations": True,
            "seed_blocks": 1,
            "languages": ["en", "vi"],
            "generation_settings": {"temperature": 0, "max_output_tokens": 512},
            "order": [(s["id"], language) for s, language in jobs],
        },
        indent=2,
    )
)


async def main():
    sem = asyncio.Semaphore(3)

    async def job(s, language):
        async with sem:
            name = s["id"] + "-" + language
            dataset = ROOT / (name + ".jsonl")
            dataset.write_text(json.dumps(s) + "\n")
            args = Namespace(
                dataset=dataset,
                packs=Path("data/experiment1/languages.json"),
                languages=[language],
                mode="live",
                provider="openrouter",
                model="openai/gpt-4.1-mini",
                split="calibration",
                limit=1,
                max_calls=54,
                allow_unreviewed=True,
                output=ROOT / name,
            )
            try:
                await asyncio.wait_for(run(args), timeout=900)
                print(name, "completed", flush=True)
            except Exception as exc:
                print(name, "failed", type(exc).__name__, flush=True)

    await asyncio.gather(*(job(s, language) for s, language in jobs))


asyncio.run(main())
