"""Pre-declared v3 analysis: per-seed paired contrasts and exact sign-flip tests.

Reads saved manifests and outcomes only; makes no inference calls. One game is
one unit; seeds are the replication unit. Failed or missing games break their
pair and are counted, never imputed.
"""

import argparse
import itertools
import json
from pathlib import Path

CONTRASTS = {
    "5b": [
        ("private_proof", "private_unverified", "verification beyond content"),
        ("private_unverified", "private_text", "content beyond testimony"),
        ("private_proof", "private_text", "full v2 contrast on held-out seeds"),
    ],
    "6": [("delayed", "none", "late authenticated truth")],
}
MIN_PAIRS = {"5b": 6, "6": 0}  # Below this, a 5b contrast is called inconclusive.
OUTCOME = {"5b": "other_recipients_correct_action_rate", "6": "correct_action_rate"}


def sign_flip_p(diffs):
    """Exact two-sided p for mean difference under random sign flips."""
    if not diffs:
        return None
    observed = abs(sum(diffs))
    hits = sum(
        abs(sum(s * d for s, d in zip(signs, diffs))) >= observed - 1e-12
        for signs in itertools.product((1, -1), repeat=len(diffs))
    )
    return hits / 2 ** len(diffs)


def load(root):
    games, failed = {}, []
    for manifest in sorted(root.glob("*/manifest.json")):
        m = json.loads(manifest.read_text())
        outcome = manifest.parent / "outcome.json"
        if m["status"] != "completed" or not outcome.exists():
            failed.append(dict(id=m["id"], status=m["status"]))
            continue
        s = m["scenario"]
        key = m["section"], m["model_tag"], s["disaster"], s["seed"], m["arm"]
        games[key] = json.loads(outcome.read_text())
    return games, failed


def analyse(games, failed):
    results = []
    cells = sorted({k[:4] for k in games})
    for section, contrasts in CONTRASTS.items():
        for model, disaster in sorted({(m, d) for s, m, d, _ in cells if s == section}):
            seeds = sorted({k[3] for k in cells if k[:3] == (section, model, disaster)})
            for treat, control, meaning in contrasts:
                pairs = [
                    (
                        seed,
                        games[section, model, disaster, seed, treat][OUTCOME[section]],
                        games[section, model, disaster, seed, control][
                            OUTCOME[section]
                        ],
                    )
                    for seed in seeds
                    if (section, model, disaster, seed, treat) in games
                    and (section, model, disaster, seed, control) in games
                ]
                diffs = [t - c for _, t, c in pairs]
                results.append(
                    dict(
                        section=section,
                        model=model,
                        disaster=disaster,
                        treatment=treat,
                        control=control,
                        meaning=meaning,
                        complete_pairs=len(pairs),
                        per_seed=[
                            dict(seed=s, treatment=t, control=c) for s, t, c in pairs
                        ],
                        mean_difference=sum(diffs) / len(diffs) if diffs else None,
                        same_direction=sum(d > 0 for d in diffs),
                        exact_sign_flip_p=sign_flip_p(diffs),
                        min_attainable_p=2 / 2 ** len(diffs) if diffs else None,
                        status="descriptive"
                        if section == "6"
                        else "inconclusive"
                        if len(pairs) < MIN_PAIRS[section]
                        else "tested",
                    )
                )
    reversals = [
        dict(
            model=k[1],
            disaster=k[2],
            seed=k[3],
            round1_wrong=o["round1_wrong"],
            reversals=o["reversals"],
            irreversible_round1_errors=o["irreversible_round1_errors"],
        )
        for k, o in sorted(games.items())
        if k[0] == "6" and k[4] == "delayed"
    ]
    return dict(
        contrasts=results,
        delayed_truth=reversals,
        failed_or_missing=failed,
        unit="whole game; seeds are replicates",
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("runs/evidence-controls-v3"))
    p.add_argument("--out", type=Path, default=Path(__file__).parent / "summary.json")
    args = p.parse_args()
    summary = analyse(*load(args.root))
    args.out.write_text(json.dumps(summary, indent=2))
    for c in summary["contrasts"]:
        print(
            c["section"],
            c["model"],
            "disaster" if c["disaster"] else "safe",
            f"{c['treatment']} - {c['control']}",
            f"n={c['complete_pairs']}",
            f"mean={c['mean_difference']}",
            f"p={c['exact_sign_flip_p']}",
        )
