"""Protect the heldout boundary of the generated research dataset."""

import json
import runpy
from pathlib import Path

import pytest

from ai2ai_guard import ReportGuard

ROOT = Path(__file__).resolve().parents[1]
reference = runpy.run_path(str(ROOT / "scripts/prepare_authority500.py"))[
    "development_reference"
]


def test_heldout_task_is_rejected_before_adaption_upload():
    task = json.loads((ROOT / "data/tasks.jsonl").read_text().splitlines()[0])
    with pytest.raises(ValueError, match="Heldout tasks"):
        reference({"task": task})


def test_development_reference_satisfies_contract_without_marker():
    task = json.loads((ROOT / "data/tasks.jsonl").read_text().splitlines()[0])
    task["split"] = "development"
    row = reference(
        {
            "task": task,
            "peer_message": "Untrusted correction",
            "language": "vi",
            "authority": "authority",
            "attack": True,
        }
    )
    assert ReportGuard().check(row["response"], task).allowed
    assert task["marker"] not in row["response"]
    assert row["split"] == "development" and row["human_reviewed"] is False


def test_six_hundred_cases_balance_and_quarantine():
    from collections import Counter

    folder = ROOT / "data/authority500"
    rows = [
        json.loads(x)
        for x in (folder / "selected_600_cases.jsonl").read_text().splitlines()
    ]
    previous = [
        json.loads(x)
        for x in (folder / "selected_500_cases.jsonl").read_text().splitlines()
    ]
    assert len(rows) == len({r["trial_id"] for r in rows}) == 600
    assert Counter(r["language"] for r in rows) == {"en": 200, "vi": 200, "zh": 200}
    assert sum(r["attack"] for r in rows) == 540
    assert not {r["task"]["task_id"] for r in rows} & {
        r["task"]["task_id"] for r in previous
    }
    assert all(r["task"]["split"] == "heldout" for r in rows)
    for language in ["en", "vi", "zh"]:
        rr = [r for r in rows if r["language"] == language]
        assert Counter(r["authority"] for r in rr) == {"peer": 100, "authority": 100}
        assert sum(r["attack"] for r in rr) == 180
    grouped = {}
    for r in rows:
        grouped.setdefault(r["task"]["task_id"], set()).add(
            (r["language"], r["authority"])
        )
    assert len(grouped) == 100 and all(len(v) == 6 for v in grouped.values())
