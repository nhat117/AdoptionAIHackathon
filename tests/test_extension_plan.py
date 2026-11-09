"""Matched diagnostic design and shared remaining-budget accounting."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "extension",
    Path(__file__).parents[1] / "reports/overnight-experiments/extensions.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_extension_plan_has_balanced_complete_pairs():
    jobs = module.jobs()
    assert len(jobs) == len({j["id"] for j in jobs}) == 40
    assert {s: sum(j["section"] == s for j in jobs) for s in ["terra", "4", "5"]} == {
        "terra": 8,
        "4": 16,
        "5": 16,
    }
    for section, arms in [
        ("4", {"none", "broadcast"}),
        ("5", {"private_text", "private_proof"}),
    ]:
        groups = {}
        for j in jobs:
            if j["section"] == section:
                key = j["model_tag"], j["scenario"]["id"]
                groups.setdefault(key, set()).add(j["arm"])
                assert not j["scenario"]["accurate"]
                assert j["language"] == "en"
        assert len(groups) == 8
        assert all(group == arms for group in groups.values())


def test_extension_reservation_limits_and_reload(tmp_path):
    budget = module.Budget(tmp_path, 0.5)
    payload = {"provider": {}}
    budget.reserve("a", payload, "terra")
    assert payload["provider"]["max_price"] == {"prompt": 1, "completion": 5}
    budget.reserve("b", payload, "sonnet")
    with pytest.raises(RuntimeError):
        budget.reserve("c", payload, "sonnet")
    budget.settle("a", 0.02)
    budget.settle("b", 0.03)
    resumed = module.Budget(tmp_path, 0.5)
    assert resumed.spent == 0.05 and not resumed.pending and not resumed.halted
