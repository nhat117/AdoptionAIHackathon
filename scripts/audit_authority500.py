"""Inspect generated task quality without using target outcomes."""

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STOP = set(
    (
        "the a an and or of to in on for with is are was were has have "
        "had been by at from as its their this that all"
    ).split()
)


def main():
    folder = ROOT / "data/authority500"
    rows = [json.loads(x) for x in (folder / "tasks.jsonl").read_text().splitlines()]
    assert len(rows) == len({r["task_id"] for r in rows}) == 500
    assert len({r["marker"] for r in rows}) == 500
    assert all(r["status"] in ("complete", "in_progress") for r in rows)
    terms = [
        Counter(
            w for w in re.findall(r"[a-z]+", r["topic"].casefold()) if w not in STOP
        )
        for r in rows
    ]
    df = Counter(w for t in terms for w in t)
    vectors = [
        {w: n * (math.log(501 / (1 + df[w])) + 1) for w, n in t.items()} for t in terms
    ]
    norms = [math.sqrt(sum(x * x for x in v.values())) for v in vectors]
    pairs = []
    for i, a in enumerate(vectors):
        for j in range(i + 1, len(vectors)):
            cosine = sum(v * vectors[j].get(k, 0) for k, v in a.items()) / (
                norms[i] * norms[j]
            )
            if cosine >= 0.75:
                pairs.append(
                    {
                        "task_a": rows[i]["task_id"],
                        "task_b": rows[j]["task_id"],
                        "cosine": cosine,
                        "cross_split": rows[i]["split"] != rows[j]["split"],
                        "topic_a": rows[i]["topic"],
                        "topic_b": rows[j]["topic"],
                    }
                )
    result = {
        "tasks": 500,
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "domain_counts": dict(Counter(r["domain"] for r in rows)),
        "split_counts": dict(Counter(r["split"] for r in rows)),
        "returned_models": sorted({r["generator_model"] for r in rows}),
        "exact_normalized_duplicates": 500
        - len(
            {" ".join(re.findall(r"[a-z0-9]+", r["topic"].casefold())) for r in rows}
        ),
        "lexical_similarity_threshold": 0.75,
        "near_duplicate_candidates": pairs,
        "cross_split_candidate_count": sum(r["cross_split"] for r in pairs),
        "audit_method": (
            "Word TF-IDF cosine; candidate detection only, "
            "not proof of semantic independence"
        ),
        "human_reviewed": False,
        "bilingual_review": "Pending",
        "outcome_leakage": "No model evaluation outcomes used for generation or audit",
        "task_file_sha256": hashlib.sha256(
            (folder / "tasks.jsonl").read_bytes()
        ).hexdigest(),
    }
    (folder / "QUALITY_AUDIT.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    print(
        {
            k: v
            for k, v in result.items()
            if k not in ["near_duplicate_candidates", "domain_counts"]
        }
    )
    print("Near-duplicate candidates", len(pairs))


if __name__ == "__main__":
    main()
