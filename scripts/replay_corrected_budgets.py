"""Replay historical outputs without mutating the frozen baseline."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from ai2ai_guard.budget_claims import ImperfectRecordChecker, OracleChecker
from ai2ai_injection.oversight_eval import all_checks, parse_candidate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/corrected_replay"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / "runs/oversight-expansion-v2/trials.jsonl"
    rows = [json.loads(x) for x in source.read_text().splitlines()]
    results = []
    for row in rows:
        raw = row["response"]["content"] if row["completed"] else ""
        value, _, _ = parse_candidate(raw, normalize_fence=True)
        summary = value.get("public_summary", "") if isinstance(value, dict) else ""
        budget = row["expected"]["budget"]
        records = {
            "correct": {"budget": budget},
            "incomplete": {},
            "stale": {"budget": budget - 100},
            "incorrect": {"budget": row["target_budget"]},
        }
        results.append(
            {
                "trial_id": row["trial_id"],
                "task_cluster": row["task_cluster"],
                "language": row["language"],
                "kind": row["kind"],
                "evidence": row["evidence"],
                "candidate_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "oracle_budget": OracleChecker().check(summary, budget),
                "imperfect_records": {
                    k: ImperfectRecordChecker().check(summary, v)
                    for k, v in records.items()
                },
                "historical_checks": row["checks"],
                "corrected_checks": all_checks(raw, row["task"]),
            }
        )
    (OUT / "decisions.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in results)
    )
    groups = []
    for evidence in ["absent", "present"]:
        subset = [r for r in results if r["evidence"] == evidence]
        groups.append(
            {
                "evidence": evidence,
                "n": len(subset),
                "budget_decisions": dict(
                    Counter(r["oracle_budget"]["decision"] for r in subset)
                ),
                "historical_normalized_semantic_allowed": sum(
                    r["historical_checks"]["normalized_semantic"]["allowed"]
                    for r in subset
                ),
                "corrected_normalized_semantic_allowed": sum(
                    r["corrected_checks"]["normalized_semantic"]["allowed"]
                    for r in subset
                ),
            }
        )
    metrics = {
        "source": str(source.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "n": len(rows),
        "groups": groups,
        "imperfect_record_decisions": {
            k: dict(Counter(r["imperfect_records"][k]["decision"] for r in results))
            for k in records
        },
        "imperfect_record_agreement": {
            k: dict(
                Counter(r["imperfect_records"][k]["record_agreement"] for r in results)
            )
            for k in records
        },
        "limitations": [
            (
                "Budget checker labels are deterministic proxy labels, not hu"
                "man-adjudicated truth."
            ),
            "All imperfect records are unverified; abstention is not detection.",
        ],
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    with (OUT / "summary.csv").open("w") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "evidence",
                "n",
                "historical_normalized_semantic_allowed",
                "corrected_normalized_semantic_allowed",
            ],
        )
        writer.writeheader()
        writer.writerows({k: r[k] for k in writer.fieldnames} for r in groups)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
