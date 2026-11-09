"""Draw a hand-labelling sample, or score hand labels against the stance rule.

sample: writes a seeded, stratified sample of delivered peer messages from
restored games to a CSV with a blank human_label column. No inference.
agreement: reads that CSV once human_label is filled and reports Cohen's kappa
and the confusion table. Use the rule in analysis only if kappa >= 0.7.
"""

import argparse
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from swarm_lab.evacuation.stance import LABELS, cohen_kappa, stance  # noqa: E402

FIELDS = ["message_id", "game", "claim", "signal", "text", "rule_label", "human_label"]


def messages(roots):
    for root in roots:
        for manifest in sorted(root.glob("*/manifest.json")):
            m = json.loads(manifest.read_text())
            traces = manifest.parent / "traces.jsonl"
            if m.get("status") != "completed" or not traces.exists():
                continue
            s = m["scenario"]
            claim = (
                ("Danger" if s["disaster"] else "Safe")
                if s["accurate"]
                else ("Safe" if s["disaster"] else "Danger")
            )
            source = s["informant"]
            for line in traces.read_text().splitlines():
                for sender, msg in json.loads(line)["messages"].items():
                    if int(sender) != source:
                        yield dict(
                            message_id=msg["id"],
                            game=m["id"],
                            claim=claim,
                            signal=msg["signal"],
                            text=msg["text"],
                            rule_label=stance(msg, claim),
                            human_label="",
                        )


def sample(roots, n, seed):
    """Stratify by rule label so rare labels are checked too."""
    by = {}
    for row in messages(roots):
        by.setdefault(row["rule_label"], []).append(row)
    rng = random.Random(seed)
    per = max(1, n // len(by)) if by else 0
    rows = []
    for label in sorted(by):
        rows += rng.sample(by[label], min(per, len(by[label])))
    rng.shuffle(rows)
    return rows[:n]


def agreement(path):
    rows = [r for r in csv.DictReader(open(path)) if r["human_label"].strip()]
    bad = {r["human_label"] for r in rows} - set(LABELS)
    if bad:
        raise ValueError(f"Unknown human labels: {sorted(bad)}")
    rule = [r["rule_label"] for r in rows]
    human = [r["human_label"] for r in rows]
    return dict(
        labelled=len(rows),
        kappa=round(cohen_kappa(rule, human), 4),
        usable=cohen_kappa(rule, human) >= 0.7,
        confusion={f"{a}->{b}": c for (a, b), c in Counter(zip(rule, human)).items()},
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--roots", type=Path, nargs="+", required=True)
    s.add_argument("--n", type=int, default=50)
    s.add_argument("--seed", type=int, default=20261109)
    s.add_argument("--out", type=Path, default=Path(__file__).parent / "sample.csv")
    a = sub.add_parser("agreement")
    a.add_argument("--csv", type=Path, default=Path(__file__).parent / "sample.csv")
    args = p.parse_args()
    if args.command == "sample":
        rows = sample(args.roots, args.n, args.seed)
        with open(args.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        print(json.dumps(dict(rows=len(rows), out=str(args.out))))
    else:
        print(json.dumps(agreement(args.csv), indent=2))
