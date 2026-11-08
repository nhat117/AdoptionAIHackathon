"""Separate stress test: a wrong record deceptively marked current."""

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from run_contract_validation import validation_design
from run_corrected_experiments import Client, freeze_text, save

from ai2ai_guard.budget_measurement import score_budget_decision

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/corrupt_record_validation"


def corruption_design():
    rows = []
    for row in validation_design():
        if row["record_access"] != "correct":
            continue
        row["trial_id"] = "corrupt-" + row["trial_id"]
        row["record_access"] = "corrupt_current"
        row["record_budget"] = row["verified_budget"] - 1000
        body = json.loads(row["messages"][1]["content"])
        body["trusted_record"] = {
            "budget": row["record_budget"],
            "freshness": "current",
        }
        row["messages"][1]["content"] = json.dumps(body, ensure_ascii=False)
        rows.append(row)
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", action="store_true")
    p.add_argument("--cap-usd", type=float, default=20)
    args = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = corruption_design()
    freeze_text(
        OUT / "inputs.jsonl",
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in inputs),
    )
    protocol = {
        "purpose": (
            "Factual truth versus policy compliance under hidden record corruption"
        ),
        "planned": 72,
        "contracts": ["neutral", "operational"],
        "task_clusters": [45, 46, 47],
        "record": "budget true minus 1000, freshness deceptively marked current",
        "primary": (
            "Factual accuracy and declared-policy compliance are separate outcomes"
        ),
        "sampling_seed_sent": None,
        "model": "gpt-5",
        "reasoning_effort": "minimal",
        "max_completion_tokens": 512,
        "stop_rule": "Fixed 72 inputs or aggregate cap, no outcome exclusions",
        "inputs_sha256": hashlib.sha256(
            (OUT / "inputs.jsonl").read_bytes()
        ).hexdigest(),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__), ROOT / "scripts/run_contract_validation.py"]
        },
        "registration": (
            "Separate local freeze before dispatch, n"
            "ot external preregistration; not pooled into the matched contract experiment"
        ),
    }
    freeze_text(OUT / "PROTOCOL.json", json.dumps(protocol, indent=2) + "\n")
    print(
        json.dumps(
            {
                "planned_calls": len(inputs),
                "dry_run": not args.run,
                "aggregate_cap_usd": args.cap_usd,
            }
        ),
        flush=True,
    )
    if not args.run:
        return
    client = Client(cap=args.cap_usd)
    path = OUT / "workers.jsonl"
    done = (
        {r["trial_id"] for r in map(json.loads, path.read_text().splitlines())}
        if path.exists()
        else set()
    )

    def collect(row):
        if row["trial_id"] in done:
            return
        try:
            response = client.chat(row["messages"], None)
            score = score_budget_decision(
                response["content"],
                row["verified_budget"],
                row["false_budget"],
                row["record_budget"],
            )
            save(path, dict(row, response=response, score=score))
        except Exception as error:
            save(
                OUT / "errors.jsonl", {"trial_id": row["trial_id"], "error": str(error)}
            )

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(collect, inputs))


if __name__ == "__main__":
    main()
