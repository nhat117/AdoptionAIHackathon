"""Run a protected report; stdout contains only a validated report or BLOCK."""

import argparse
import getpass
import json
import os
from dataclasses import asdict
from pathlib import Path

from ai2ai_guard import guarded_generate
from ai2ai_injection.attacks import render_attack
from ai2ai_injection.logging_io import read_jsonl
from ai2ai_injection.providers import Client

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider", choices=["braintrust", "ollama"], default="ollama"
    )
    parser.add_argument("--model", default="qwen2.5:0.5b")
    parser.add_argument("--language", choices=["en", "vi", "zh"], default="vi")
    parser.add_argument(
        "--authority", choices=["peer", "authority"], default="authority"
    )
    parser.add_argument("--task-id", default="h1-v3-01")
    parser.add_argument("--llm-monitor", action="store_true")
    parser.add_argument("--audit", type=Path)
    args = parser.parse_args()
    task = next(
        t for t in read_jsonl(ROOT / "data/tasks.jsonl") if t["task_id"] == args.task_id
    )
    translations = json.loads((ROOT / "data/translations.json").read_text())
    note = render_attack(task, args.language, args.authority, translations)
    key = ""
    if args.provider == "braintrust" or args.llm_monitor:
        key = os.environ.get("BRAINTRUST_API_KEY") or getpass.getpass(
            "Braintrust key (not saved): "
        )
    target = Client(args.provider, args.model, key, temperature=0.7)
    monitor = (
        Client("braintrust", "gpt-4o", key, temperature=0) if args.llm_monitor else None
    )
    result = guarded_generate(task, note, target, monitor=monitor)
    print(
        json.dumps(
            {"released": result.released, "report": result.report},
            ensure_ascii=False,
            indent=2,
        )
    )
    if args.audit:
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.audit.write_text(
            json.dumps(asdict(result), indent=2, ensure_ascii=False) + "\n"
        )


if __name__ == "__main__":
    main()
