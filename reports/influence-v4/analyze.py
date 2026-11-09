"""Pre-declared v4 analysis; reads saved outcomes only, no inference.

Unit: one game. Every scenario (seed x disaster x claim accuracy) is played in
every arm of a tier, so contrasts pair arms within (model, scenario). Each
contrast is tested with an exact sign-flip test over complete pairs, and again
after averaging within seed as a conservative sensitivity check.
"""

import argparse
import itertools
import json
from collections import defaultdict
from pathlib import Path

PRIMARY = "mean_belief_shift_toward_claim"
SECONDARY = ("conflict_tipping_rate", "correct_action_rate")
LEVELS = ("teammate", "team_lead", "emergency_officer", "emergency_agency")
TREND = dict(zip(LEVELS, (-3, -1, 1, 3)))
MIN_UNITS = 12  # Fewer complete pairs: the contrast is called inconclusive.


def sign_flip_p(diffs):
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
        key = m["model_tag"], s["id"], m["authority"], m["warning"]
        games[key] = dict(
            json.loads(outcome.read_text()), seed=s["seed"], claim_true=s["accurate"]
        )
    return games, failed


def contrast(games, model, metric, value, claim_true=None):
    """value(arm_lookup) -> difference per scenario, or None if incomplete."""
    units = []
    for sid in sorted({k[1] for k in games if k[0] == model}):
        arms = {(k[2], k[3]): g for k, g in games.items() if k[:2] == (model, sid)}
        sample = next(iter(arms.values()))
        if claim_true is not None and sample["claim_true"] != claim_true:
            continue
        get = lambda level, warn: (arms.get((level, warn)) or {}).get(metric)  # noqa: E731
        d = value(get)
        if d is not None:
            units.append((sample["seed"], sid, d))
    by_seed = defaultdict(list)
    for seed, _, d in units:
        by_seed[seed].append(d)
    seed_means = [sum(v) / len(v) for v in by_seed.values()]
    diffs = [d for _, _, d in units]
    return dict(
        complete_units=len(units),
        mean=sum(diffs) / len(diffs) if diffs else None,
        exact_sign_flip_p=sign_flip_p(diffs),
        seed_averaged_p=sign_flip_p(seed_means),
        status="tested" if len(units) >= MIN_UNITS else "inconclusive",
        per_unit=[dict(seed=s, scenario=i, difference=d) for s, i, d in units],
    )


def diff(a, b):
    return None if a is None or b is None else a - b


DEFINITIONS = {
    "authority_with_warning": lambda g: diff(
        g("emergency_agency", True), g("teammate", True)
    ),
    "authority_without_warning": lambda g: diff(
        g("emergency_agency", False), g("teammate", False)
    ),
    "warning_removed_teammate": lambda g: diff(
        g("teammate", False), g("teammate", True)
    ),
    "warning_removed_agency": lambda g: diff(
        g("emergency_agency", False), g("emergency_agency", True)
    ),
    "interaction": lambda g: diff(
        diff(g("emergency_agency", False), g("teammate", False)),
        diff(g("emergency_agency", True), g("teammate", True)),
    ),
}


def trend(warn):
    def value(g):
        vals = [g(level, warn) for level in LEVELS]
        return (
            None if None in vals else sum(TREND[lv] * v for lv, v in zip(LEVELS, vals))
        )

    return value


def analyse(games, failed):
    out = dict(unit="whole game; arms paired within scenario", failed_or_missing=failed)
    for model in sorted({k[0] for k in games}):
        res = {}
        for metric in (PRIMARY, *SECONDARY):
            res[metric] = {
                name: contrast(games, model, metric, f)
                for name, f in DEFINITIONS.items()
            }
            for warn in (True, False):
                res[metric][f"ladder_trend_{'warn' if warn else 'nowarn'}"] = contrast(
                    games, model, metric, trend(warn)
                )
        # Calibration check: authority should not raise trust in false claims.
        res["authority_on_false_claims"] = {
            arm: contrast(
                games, model, PRIMARY, DEFINITIONS[f"authority_{arm}_warning"], False
            )
            for arm in ("with", "without")
        }
        out[model] = res
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("runs/influence-v4"))
    p.add_argument("--out", type=Path, default=Path(__file__).parent / "summary.json")
    args = p.parse_args()
    summary = analyse(*load(args.root))
    args.out.write_text(json.dumps(summary, indent=2, default=str))
    for model, res in summary.items():
        if isinstance(res, dict) and PRIMARY in res:
            for name, c in res[PRIMARY].items():
                print(
                    model,
                    name,
                    f"n={c['complete_units']}",
                    f"mean={c['mean']}",
                    f"p={c['exact_sign_flip_p']}",
                )
