import json
import runpy
from pathlib import Path


def test_contract_validation_is_paired_and_disjoint(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "scripts"))
    module = runpy.run_path(str(root / "scripts/run_contract_validation.py"))
    rows = module["validation_design"]()
    assert len(rows) == len({r["trial_id"] for r in rows}) == 216
    assert {r["cluster"] for r in rows} == {45, 46, 47}
    pairs = {}
    for row in rows:
        key = (
            row["cluster"],
            row["authority"],
            row["language"],
            row["record_access"],
            row["attack"],
        )
        pairs.setdefault(key, {})[row["contract"]] = row
        if row["record_access"] != "correct":
            assert str(row["verified_budget"]) not in json.dumps(row["messages"])
    for pair in pairs.values():
        a, b = pair["neutral"], pair["operational"]
        assert a["messages"][1] == b["messages"][1]
        assert (
            b["messages"][0]["content"]
            == a["messages"][0]["content"] + module["POLICY"]
        )


def test_corrupted_current_record_withholds_true_budget(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "scripts"))
    rows = runpy.run_path(str(root / "scripts/run_corrupt_record_validation.py"))[
        "corruption_design"
    ]()
    assert len(rows) == len({r["trial_id"] for r in rows}) == 72
    for row in rows:
        body = json.loads(row["messages"][1]["content"])
        assert body["trusted_record"] == {
            "budget": row["verified_budget"] - 1000,
            "freshness": "current",
        }
        assert str(row["verified_budget"]) not in json.dumps(row["messages"])
