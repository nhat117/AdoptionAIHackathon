"""v3 analysis plan and the split decision rates, on synthetic and saved data."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


analyze = module("reports/evidence-controls-v3/analyze.py", "v3analyze")
rates = module("reports/overnight-experiments/decision_rates.py", "rates")


def test_sign_flip_matches_hand_counts():
    assert analyze.sign_flip_p([1] * 8) == 2 / 256
    assert analyze.sign_flip_p([1, -1]) == 1
    assert analyze.sign_flip_p([]) is None


def write_game(root, section, arm, seed, value, status="completed"):
    folder = root / f"{section}-{seed}-{arm}"
    folder.mkdir()
    scenario = dict(disaster=True, seed=seed)
    (folder / "manifest.json").write_text(
        json.dumps(
            dict(
                id=folder.name,
                section=section,
                model_tag="sonnet",
                arm=arm,
                scenario=scenario,
                status=status,
            )
        )
    )
    if status == "completed":
        (folder / "outcome.json").write_text(
            json.dumps({analyze.OUTCOME[section]: value})
        )


def test_pairs_by_seed_and_drops_failed_games(tmp_path):
    for seed in range(2000, 2008):
        write_game(tmp_path, "5b", "private_proof", seed, 1.0)
        write_game(tmp_path, "5b", "private_unverified", seed, 0.25)
        failed = seed == 2007
        write_game(
            tmp_path,
            "5b",
            "private_text",
            seed,
            0.0,
            "failed" if failed else "completed",
        )
    out = analyze.analyse(*analyze.load(tmp_path))
    by = {(c["treatment"], c["control"]): c for c in out["contrasts"]}
    proof = by["private_proof", "private_unverified"]
    assert proof["complete_pairs"] == 8 and proof["mean_difference"] == 0.75
    assert proof["exact_sign_flip_p"] == 2 / 256 and proof["status"] == "tested"
    assert by["private_unverified", "private_text"]["complete_pairs"] == 7
    assert out["failed_or_missing"] == [
        dict(id="5b-2007-private_text", status="failed")
    ]


def test_too_few_pairs_is_inconclusive(tmp_path):
    for seed in range(2000, 2003):
        write_game(tmp_path, "5b", "private_proof", seed, 1.0)
        write_game(tmp_path, "5b", "private_unverified", seed, 0.0)
    out = analyze.analyse(*analyze.load(tmp_path))
    assert {c["status"] for c in out["contrasts"] if c["complete_pairs"]} == {
        "inconclusive"
    }


def test_rates_separate_opposite_failures():
    # A false "Safe" claim in a disaster: staying follows the claim and misses.
    always_stay = dict(disaster="True", accurate="False", correct_action_rate="0.0")
    follows = dict(disaster="False", accurate="False", correct_action_rate="0.0")
    assert rates.rates(always_stay) == dict(
        evacuated=0.0, miss=1.0, false_alarm=None, claim_following=1.0
    )
    assert rates.rates(follows)["false_alarm"] == 1.0
    assert rates.rates(follows)["claim_following"] == 1.0
    # Scenario IDs carry accuracy when the CSV has no accurate column.
    assert rates.claim_true(dict(scenario="calibration-000-1-0")) is False


def test_saved_games_show_opposite_model_patterns():
    summary = rates.model_summary(rates.table())
    assert summary["sonnet"]["follows_danger"]["rate"] == 0
    assert summary["sonnet"]["follows_safe"]["rate"] == 1
    assert summary["terra"]["follows_danger"]["rate"] == 1
    assert summary["terra"]["follows_safe"]["rate"] == 1
