"""Descriptive cell summaries; episodes, not agents, are the observations."""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


def summarize(path):
    groups = defaultdict(list)
    for line in path.read_text().splitlines():
        row = json.loads(line)
        s = row["scenario"]
        key = (
            row["mode"],
            row["study"],
            row["arm"],
            s["split"],
            s["disaster"],
            s["accurate"],
            s["source_label"],
        )
        groups[key].append(row)
    report = []
    for key, rows in sorted(groups.items()):
        cell = dict(
            zip(
                (
                    "mode",
                    "study",
                    "arm",
                    "split",
                    "disaster",
                    "accurate",
                    "source_label",
                ),
                key,
                strict=True,
            )
        )
        cell["episodes"] = len(rows)
        for metric in (
            "missed_evacuation_rate",
            "unnecessary_evacuation_rate",
            "correct_action_rate",
            "source_selection_rate",
            "total_payoff",
        ):
            values = [r[metric] for r in rows if r[metric] is not None]
            cell[metric] = mean(values) if values else None
        report.append(cell)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outcomes", type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.outcomes), indent=2))
