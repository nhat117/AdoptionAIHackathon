import importlib.util
import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts/run_corrected_experiments.py"
spec = importlib.util.spec_from_file_location("corrected", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_matched_design_and_absent_record_has_no_hidden_truth():
    cases = module.cases()
    assert len(cases) == len({r["trial_id"] for r in cases}) == 600
    groups = {}
    for row in cases:
        groups.setdefault(row["cluster"], []).append(row)
        body = json.loads(row["messages"][1]["content"])
        if row["evidence"] == "absent":
            assert body["trusted_record"] is None
            assert str(row["verified_budget"]) not in json.dumps(row["messages"])
        assert str(row["false_budget"]) in row["peer_message"]
        assert "verified_budget" not in json.dumps(row["messages"])
    assert len(groups) == 25
    for rows in groups.values():
        assert len(rows) == 24
        assert len({r["false_budget"] for r in rows}) == 1
        assert len({r["verified_budget"] for r in rows}) == 1


def test_bilingual_attack_contains_localized_false_claim():
    for row in module.cases():
        if row["language"] == "vi":
            assert "Ngân sách" in row["peer_message"]
        if row["language"] == "zh":
            assert "预算" in row["peer_message"]


def test_cost_cap_rejects_before_dispatch(monkeypatch, tmp_path):
    import pytest

    monkeypatch.setattr(module, "OUT", tmp_path)
    client = module.Client(cap=0)
    with pytest.raises(RuntimeError, match="budget_cap_reached"):
        client.chat([{"role": "user", "content": "fixture"}], None)
    assert client.calls == 0


def test_resume_rejects_changed_protocol(tmp_path):
    import pytest

    path = tmp_path / "protocol.json"
    module.freeze_text(path, "original")
    module.freeze_text(path, "original")
    with pytest.raises(ValueError, match="Frozen experiment differs"):
        module.freeze_text(path, "changed")
    assert path.read_text() == "original"
