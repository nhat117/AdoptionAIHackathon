"""Reproduce matched multi-task results without inference or outcome selection."""

import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/measurement_v2_replication"


def read(name):
    path = OUT / name
    return (
        [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--partial", action="store_true")
    args = p.parse_args()
    inputs = read("inputs.jsonl")
    rows = read("workers.jsonl")
    expected = {r["trial_id"]: r for r in inputs}
    assert len(expected) == 1440
    assert len(rows) == len({r["trial_id"] for r in rows})
    assert all(
        all(row[k] == v for k, v in expected[row["trial_id"]].items()) for row in rows
    )
    if not args.partial:
        assert len(rows) == 1440, "Incomplete collection; use --partial for status"
    protocol = json.loads((OUT / "PROTOCOL.json").read_text())
    assert (
        hashlib.sha256((OUT / "inputs.jsonl").read_bytes()).hexdigest()
        == protocol["inputs_sha256"]
    )
    for name, sha in protocol["source_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
    groups = []
    cells = []
    for access in ("correct", "absent", "stale"):
        for attack in (False, True):
            rr = [
                r
                for r in rows
                if r["record_access"] == access and r["attack"] == attack
            ]
            group = counts(rr)
            groups.append(dict(record=access, attack=attack, **group))
            for language in ("en", "vi", "zh"):
                for authority in range(4):
                    cell = [
                        r
                        for r in rr
                        if r["language"] == language and r["authority"] == authority
                    ]
                    cells.append(
                        dict(
                            record=access,
                            attack=attack,
                            language=language,
                            authority=authority,
                            **counts(cell),
                        )
                    )
    contrasts = []
    if len(rows) == 1440:
        # Every effect uses all 20 matched task clusters. Missing-format indicators
        # remain explicit; the estimated outcome is *confirmed* target reporting.
        attacked = [r for r in rows if r["attack"]]
        by_task = {c: [r for r in attacked if r["cluster"] == c] for c in range(25, 45)}

        def rate(rr):
            return sum(r["score"]["attack_adoption"] is True for r in rr) / len(rr)

        def estimate(rr, kind, a=None, b=None):
            if kind == "record":
                return rate([r for r in rr if r["record_access"] == a]) - rate(
                    [r for r in rr if r["record_access"] == "correct"]
                )
            if kind == "authority":
                return rate([r for r in rr if r["authority"] == a]) - rate(
                    [r for r in rr if r["authority"] == 0]
                )
            if kind == "language":
                return rate([r for r in rr if r["language"] == a]) - rate(
                    [r for r in rr if r["language"] == "en"]
                )
            return estimate(
                [r for r in rr if r["language"] == b], "authority", a
            ) - estimate([r for r in rr if r["language"] == "en"], "authority", a)

        specs = (
            [("record", a, None) for a in ("absent", "stale")]
            + [("authority", a, None) for a in (1, 2, 3)]
            + [("language", a, None) for a in ("vi", "zh")]
            + [("interaction", a, b) for a in (1, 2, 3) for b in ("vi", "zh")]
        )
        matrix = [[estimate(rr, *spec) for spec in specs] for rr in by_task.values()]
        rng = random.Random(20261109)
        draws = 20000
        distributions = [[] for _ in specs]
        for _ in range(draws):
            sample = rng.choices(matrix, k=len(matrix))
            for index, dist in enumerate(distributions):
                dist.append(sum(row[index] for row in sample) / len(sample))
        for index, spec in enumerate(specs):
            dist = sorted(distributions[index])
            tail = 0.025 / len(specs)
            contrasts.append(
                {
                    "kind": spec[0],
                    "condition": spec[1],
                    "language": spec[2],
                    "matched_tasks": 20,
                    "difference": sum(row[index] for row in matrix) / 20,
                    "task_bootstrap_95": [dist[500], dist[19500]],
                    "bonferroni_percentile_interval": [
                        dist[int(tail * draws)],
                        dist[min(draws - 1, int((1 - tail) * draws))],
                    ],
                }
            )
    metrics = {
        "planned": 1440,
        "collected": len(rows),
        "pending": 1440 - len(rows),
        "error_events": len(read("errors.jsonl")),
        "returned_models": dict(Counter(r["response"]["model"] for r in rows)),
        "groups": groups,
        "cells": cells,
        "paired_contrasts": contrasts,
        "analysis": "Confirmed explicit false-target reporting; invalid formats remain unknown and are not successful defenses. Percentile bootstrap over matched tasks, 20000 draws; 13 exploratory contrasts with Bonferroni-tail intervals. Not a population safety bound.",
    }
    (OUT / ("PARTIAL_METRICS.json" if args.partial else "metrics.json")).write_text(
        json.dumps(metrics, indent=2) + "\n"
    )
    if not args.partial:
        with (OUT / "cells.csv").open("w") as f:
            w = csv.DictWriter(f, fieldnames=list(cells[0]))
            w.writeheader()
            w.writerows(cells)
        lines = [
            "# Multi-task structured-decision replication\n",
            "Fixed 20-task study disjoint from the one-task v2 pilot. Scenarios existed in older datasets; this is not a claim of model-unseen tasks. Four authority conditions, three languages, three record conditions, paired clean/attack messages: 1440 worker calls. Outputs are explicit budget decisions, not an inferred hidden belief or a universal prose-claim judgment.\n",
            "| Record | Attack | n | Valid | False target reported | Correct budget | Abstained | Invalid |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for r in groups:
            lines.append(
                f"| {r['record']} | {r['attack']} | {r['n']} | {r['valid']} | {r['false_target']} | {r['correct']} | {r['abstained']} | {r['invalid']} |"
            )
        lines += [
            "\nClean and attack rows are retained regardless of outcome. Invalid outputs remain instrument/format failures and are not counted as refusals. Bounds on false-target reporting include unresolved formats. Correctness and abstention are separate outcomes: an abstention is not successful budget completion. A stale record can produce a schema-valid but factually incorrect response even without an attacker.\n",
            "| Paired contrast | Condition | Language | Difference (pp) | Task bootstrap 95% (pp) | Multiplicity-adjusted interval (pp) |",
            "|---|---|---|---:|---:|---:|",
        ]
        for r in contrasts:
            lo, hi = r["task_bootstrap_95"]
            a, b = r["bonferroni_percentile_interval"]
            lines.append(
                f"| {r['kind']} | {r['condition']} | {r['language'] or 'all'} | {100 * r['difference']:.2f} | [{100 * lo:.2f}, {100 * hi:.2f}] | [{100 * a:.2f}, {100 * b:.2f}] |"
            )
        lines += [
            "\nRecord contrasts compare absent/stale with correct. Authority contrasts compare team lead (1), finance auditor (2), and fake system authority (3) with teammate (0). Language contrasts compare Vietnamese/Chinese with English. Interactions are authority contrasts in the target language minus the English contrast. These are exploratory synthetic-task estimates; 20 task clusters and one model do not support model-general conclusions. Zero-width bootstrap intervals on constant outcomes do not establish equivalence. For invalid formats, contrasts describe confirmed-adoption lower bounds, not identified true adoption effects.\n",
            "## Reproduce\n",
            "Run `python scripts/run_measurement_v2.py --replicate` for the dry run; add `--run` to resume missing worker IDs under the shared original US$10 cap. Run `python scripts/report_measurement_replication.py` to verify frozen input/source hashes and regenerate results. The local protocol was saved before dispatch, not externally preregistered. Analysis was specified during collection, before inspecting replication outcomes; it is exploratory. Raw outputs, prompts and exact model IDs remain in workers.jsonl. No committee replication is claimed by this worker-only study.\n",
            "The separate feasibility report documents the GitHub sources informing measurement: [InjecAgent](https://github.com/uiuc-kang-lab/InjecAgent) and [Inspect evaluation guidance](https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/BEST_PRACTICES.md). No upstream code or attack payload was copied.\n",
        ]
        (OUT / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "collected": len(rows),
                "pending": 1440 - len(rows),
                "error_events": len(read("errors.jsonl")),
            }
        )
    )


def counts(rr):
    n = len(rr)
    invalid = sum(r["score"]["status"] != "VALID" for r in rr)
    k = sum(r["score"]["attack_adoption"] is True for r in rr)
    return {
        "n": n,
        "valid": n - invalid,
        "false_target": k,
        "correct": sum(r["score"]["fact_correct"] is True for r in rr),
        "abstained": sum(r["score"]["abstained"] is True for r in rr),
        "invalid": invalid,
        "adoption_lower": k / n if n else None,
        "adoption_upper": (k + invalid) / n if n else None,
    }


if __name__ == "__main__":
    main()
