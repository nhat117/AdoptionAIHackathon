"""One diagnostic request per routable planned model; never retry."""

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from swarm_lab.evacuation.language import TextPolicy, validate
from swarm_lab.evacuation.openrouter import OpenRouterBackend
from swarm_lab.settings import Settings

OUT = Path("reports/2026-11-08-model-preflight")


async def main():
    load_dotenv()
    packs = json.loads(Path("data/experiment1/languages.json").read_text())
    roster = [
        ("openai/gpt-4.1-mini", "en", None),
        ("anthropic/claude-haiku-4.5", "vi", "low"),
        ("qwen/qwen3.8-27b", "zh", "low"),
        ("deepseek/deepseek-v4-flash", "zh", "low"),
        ("mistralai/mistral-small-3.2-24b-instruct", "fr", None),
    ]

    async def check(model, lang, effort):
        path = OUT / (model.replace("/", "_") + ".json")
        if path.exists():
            raise ValueError("Existing check; do not repeat")
        records = []
        result = {
            "model": model,
            "language": lang,
            "requested_reasoning": effort,
            "temperature": 0,
            "max_output_tokens": 512,
            "attempts": 1,
        }
        view = {
            "agent": 0,
            "round": 3,
            "neighbours": [1, 2, 8, 9],
            "language": lang,
            "history": [
                {
                    "id": "r2-a1",
                    "sender": 1,
                    "source_label": packs[lang]["peer_label"],
                    "signal": "Danger",
                    "text": packs[lang]["claims"]["Danger"],
                    "parents": [],
                    "authenticated": False,
                }
            ],
        }
        backend = OpenRouterBackend(
            os.environ["OPENROUTER_API_KEY"],
            Settings(model=model, temperature=0, max_output_tokens=512),
            records.append,
            reasoning_effort=effort,
        )
        try:
            data = await TextPolicy(packs[lang], backend, 1, records.append).decide(
                view
            )
            validate(data, view)
            result.update(status="valid_response", decision=data)
        except Exception as exc:
            result.update(status="failed", error_type=type(exc).__name__)
            if hasattr(exc, "code"):
                result["http_status"] = exc.code
        result["records"] = records
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(model, result["status"], result.get("error_type", ""), flush=True)

    await asyncio.gather(*(check(*r) for r in roster))


if __name__ == "__main__":
    asyncio.run(main())
