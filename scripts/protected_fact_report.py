"""Run the opt-in trusted-facts contract with a local authoritative JSON record."""

import argparse
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from ai2ai_guard.context import contextual_annotations, contextual_fact_report
from ai2ai_injection.adaption_provider import AdaptionClient, load_key

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task", type=Path, default=ROOT / "configs/fact_report_demo.json"
    )
    parser.add_argument("--model", default="gemma-4-26b-a4b-it")
    parser.add_argument("--audit", type=Path)
    parser.add_argument(
        "--history",
        type=Path,
        help="External rounds JSON, imported only as untrusted data",
    )
    parser.add_argument(
        "--feedback",
        type=Path,
        help="External validator feedback JSON; cannot authorize release",
    )
    args = parser.parse_args()
    task = json.loads(args.task.read_text())
    annotations = task.pop("annotations", [])
    if not isinstance(annotations, list):
        parser.error("annotations must be a JSON list")
    for key in ("task_id", "status", "topic", "milestone", "marker"):
        if not isinstance(task.get(key), str) or not task[key]:
            parser.error(f"{key} must be a nonempty string")
    facts = task.get("facts", {})
    if type(facts.get("budget")) is not int or facts["budget"] < 0:
        parser.error("facts.budget must be a nonnegative integer")
    if facts.get("risk") not in ("low", "medium", "high"):
        parser.error("facts.risk must be low, medium or high")
    try:
        date.fromisoformat(facts["deadline"])
    except (ValueError, TypeError, KeyError):
        parser.error("facts.deadline must be an ISO date")
    dialogue = json.loads(args.history.read_text()) if args.history else None
    feedback = json.loads(args.feedback.read_text()) if args.feedback else None
    try:
        contextual_annotations(annotations, dialogue=dialogue, feedback=feedback)
    except ValueError as error:
        parser.error(str(error))
    client = AdaptionClient(args.model, load_key("adaption"), max_output_tokens=4096)
    try:
        result = contextual_fact_report(
            task, annotations, client, dialogue=dialogue, feedback=feedback
        )
    finally:
        client.close()
    if args.audit:
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.audit.write_text(json.dumps(asdict(result), indent=2) + "\n")
    print(
        json.dumps(
            {
                "released": result.released,
                "report": result.report,
                "attempts": result.attempts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
