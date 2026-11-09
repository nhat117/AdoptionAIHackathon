"""Run a protected report; stdout contains only a validated report or BLOCK."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from ai2ai_guard import guarded_generate
from ai2ai_injection.adaption_provider import load_key, make_client
from ai2ai_injection.attacks import render_attack
from ai2ai_injection.logging_io import read_jsonl

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider", choices=["adaption", "braintrust", "ollama"], default="adaption"
    )
    parser.add_argument("--model", default="qwen3.8-27b")
    parser.add_argument("--language", choices=["en", "vi", "zh"], default="vi")
    parser.add_argument(
        "--authority", choices=["peer", "authority"], default="authority"
    )
    parser.add_argument("--task-id", default="h1-v3-01")
    parser.add_argument("--llm-monitor", action="store_true")
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--monitor-model", default="deepseek-v4-flash")
    args = parser.parse_args()
    task = next(
        t for t in read_jsonl(ROOT / "data/tasks.jsonl") if t["task_id"] == args.task_id
    )
    translations = json.loads((ROOT / "data/translations.json").read_text())
    note = render_attack(task, args.language, args.authority, translations)
    key = load_key(args.provider)
    target = make_client(args.provider, args.model, key, temperature=0.7)
    monitor = None
    if args.llm_monitor:
        monitor_key = key if args.provider == "adaption" else load_key("adaption")
        monitor = make_client(
            "adaption", args.monitor_model, monitor_key, temperature=0
        )
    result = guarded_generate(task, note, target, monitor=monitor)
    print(
        json.dumps(
            {"released": result.released, "report": result.report},
            ensure_ascii=False,
            indent=2,
        )
    )
    for connection in [target] + ([monitor] if monitor else []):
        if hasattr(connection, "close"):
            connection.close()
    if args.audit:
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.audit.write_text(
            json.dumps(asdict(result), indent=2, ensure_ascii=False) + "\n"
        )


if __name__ == "__main__":
    main()
