"""Split pooled correctness into miss, false-alarm and claim-following rates.

Reads only the saved per-game CSVs; makes no inference calls. A pooled
correct-action rate hides opposite failures: an agent that always stays and an
agent that always follows the source both score 50% over balanced cases.
"""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
SECTIONS = {
    "1": "experiment-1",
    "2": "experiment-2",
    "3": "experiment-3",
    "terra": "terra-comparison",
    "4": "experiment-4",
    "5": "experiment-5",
}


def claim_true(row):
    if "accurate" in row:
        return row["accurate"] == "True"
    # Scenario IDs end in -<disaster>-<accurate>, e.g. calibration-000-1-0.
    return row["scenario"].rsplit("-", 1)[1] == "1"


def rates(row):
    """Per-game rates over the nine recipients; None where undefined."""
    disaster = row["disaster"] == "True"
    correct = float(row["correct_action_rate"])
    evacuated = correct if disaster else 1 - correct
    claim_danger = disaster == claim_true(row)
    return dict(
        evacuated=evacuated,
        miss=1 - correct if disaster else None,
        false_alarm=1 - correct if not disaster else None,
        claim_following=evacuated if claim_danger else 1 - evacuated,
    )


def condition(section, row):
    model = row.get("model", "sonnet")
    if section in {"1", "2", "3"}:
        arm = f"{row['language']}/{row['identity']}/{row['topology']}"
    else:
        arm = f"{row['language']}/{row['arm']}"
    return section, model, arm


def table(root=ROOT):
    groups = defaultdict(list)
    for section, folder in SECTIONS.items():
        with open(root / folder / "games.csv") as f:
            for row in csv.DictReader(f):
                if row["status"] != "completed":
                    continue
                key = (*condition(section, row), row["disaster"] == "True")
                groups[key + (claim_true(row),)].append(rates(row))
    out = []
    for (section, model, arm, disaster, true_claim), rs in sorted(groups.items()):

        def mean(k):
            vals = [r[k] for r in rs if r[k] is not None]
            return round(sum(vals) / len(vals), 4) if vals else None

        out.append(
            dict(
                section=section,
                model=model,
                condition=arm,
                disaster=disaster,
                claim_true=true_claim,
                claim="Danger" if disaster == true_claim else "Safe",
                games=len(rs),
                miss_rate=mean("miss"),
                false_alarm_rate=mean("false_alarm"),
                claim_following_rate=mean("claim_following"),
            )
        )
    return out


def model_summary(rows):
    """Claim-following per model and claim direction, original-protocol games.

    Split by direction because a model that always stays follows every "Safe"
    claim and no "Danger" claim; pooled, that also looks like 50%.
    """
    acc = defaultdict(lambda: [0.0, 0])
    for r in rows:
        if r["section"] in {"1", "2", "3", "terra"}:
            a = acc[r["model"], r["claim"]]
            a[0] += r["claim_following_rate"] * r["games"]
            a[1] += r["games"]
    summary = defaultdict(dict)
    for (model, claim), (total, n) in sorted(acc.items()):
        summary[model][f"follows_{claim.lower()}"] = dict(
            games=n, rate=round(total / n, 4)
        )
    return dict(summary)


def markdown(rows):
    head = (
        "| Section | Model | Condition | Disaster | Claim | Claim true | Games "
        "| Miss | False alarm | Claim-following |\n"
        "|---|---|---|---|---|---|---:|---:|---:|---:|\n"
    )
    fmt = lambda v: "–" if v is None else f"{v:.0%}"  # noqa: E731
    return head + "".join(
        f"| {r['section']} | {r['model']} | {r['condition']} | {r['disaster']} "
        f"| {r['claim']} | {r['claim_true']} | {r['games']} | {fmt(r['miss_rate'])} "
        f"| {fmt(r['false_alarm_rate'])} | {fmt(r['claim_following_rate'])} |\n"
        for r in rows
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--outdir", type=Path, default=ROOT)
    args = p.parse_args()
    rows = table()
    summary = model_summary(rows)
    (args.outdir / "decision-rates.json").write_text(
        json.dumps(dict(model_summary=summary, cells=rows), indent=2)
    )
    with open(args.outdir / "decision-rates.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (args.outdir / "decision-rates.md").write_text(markdown(rows))
    print(json.dumps(summary))
