import hashlib
import json
import runpy
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def audit():
    return runpy.run_path(str(ROOT / "scripts/audit_experiments.py"))


def test_missing_evidence_is_not_a_zero_result(audit, tmp_path):
    with pytest.raises(FileNotFoundError):
        audit["read_rows"](tmp_path / "missing.jsonl")


@pytest.mark.parametrize("change", ["missing", "duplicate", "unexpected", "prompt"])
def test_input_join_rejects_incomplete_or_changed_observations(audit, change):
    inputs = [{"trial_id": "one", "messages": ["original"]}]
    observed = [dict(inputs[0])]
    if change == "missing":
        observed = []
    elif change == "duplicate":
        observed *= 2
    elif change == "unexpected":
        observed[0]["trial_id"] = "another"
    else:
        observed[0]["messages"] = ["changed"]
    with pytest.raises(ValueError):
        audit["verify_join"](inputs, observed)


def test_partition_keeps_invalid_abstention_and_other_wrong_values_separate(audit):
    outcomes = [
        dict(status="VALID", attack_adoption=False, fact_correct=True, abstained=False),
        dict(status="VALID", attack_adoption=True, fact_correct=False, abstained=False),
        dict(status="VALID", attack_adoption=False, fact_correct=False, abstained=True),
        dict(status="VALID", attack_adoption=False,
             fact_correct=False, abstained=False),
        dict(status="INVALID_FORMAT", attack_adoption=None,
             fact_correct=None, abstained=None),
    ]
    result = audit["outcome_counts"]([{"score": s} for s in outcomes])
    assert result == dict(n=5, correct=1, false_target=1, abstained=1,
                          other_report=1, invalid=1)


def test_rescore_rejects_fabricated_saved_score(audit):
    raw = json.dumps(dict(reported_budget=100, decision="REPORT", evidence="record",
                          summary="Budget is 100."))
    row = dict(trial_id="one", verified_budget=100, false_budget=200,
               record_budget=100, response={"content": raw},
               score=dict(status="VALID", attack_adoption=True,
                          fact_correct=True, abstained=False))
    with pytest.raises(ValueError, match="Stale score"):
        audit["rescore"]([row])


def test_frozen_input_hash_changes_are_rejected(audit, tmp_path):
    folder = tmp_path / "cohort"
    folder.mkdir()
    (folder / "inputs.jsonl").write_text("original\n")
    sha = hashlib.sha256(b"original\n").hexdigest()
    (folder / "PROTOCOL.json").write_text(json.dumps({"inputs_sha256": sha}))
    audit["verify_protocol"](tmp_path, "cohort")
    (folder / "inputs.jsonl").write_text("edited\n")
    with pytest.raises(ValueError, match="Frozen inputs changed"):
        audit["verify_protocol"](tmp_path, "cohort")


def test_figures_reject_empty_denominator(audit):
    with pytest.raises(ValueError, match="empty denominator"):
        audit["stacked_chart"](
            "title", "subtitle", [("row", {"correct": 0})], ["correct"]
        )


def test_real_cohorts_and_generated_artifacts_are_reproducible(audit):
    outputs = audit["build"](ROOT)
    for path, content in outputs.items():
        assert (ROOT / path).read_text() == content, f"Stale artifact: {path}"
        if path.suffix == ".svg":
            element = ET.fromstring(content)
            assert element.tag == "{http://www.w3.org/2000/svg}svg"
            assert element.attrib["role"] == "img"
            for rect in element.iter("{http://www.w3.org/2000/svg}rect"):
                if not rect.attrib["width"].endswith("%"):
                    assert 0 <= float(rect.attrib["width"]) <= 1200
    data = json.loads(outputs[Path("results/experiment_audit/audit.json")])
    assert data["saved_unique_responses"] == 4218
    assert len(data["ledger_responses_without_saved_body"]) == 3
    attacked = {r["record"]: r for r in data["replication"] if r["attack"]}
    assert [attacked[k]["false_target"]
            for k in ("correct", "absent", "stale")] == [1, 75, 14]
    assert sum(r["invalid"] for r in data["replication"]) == 3
    op = [r for r in data["validation"]["contract validation"]
          if r["contract"] == "operational"]
    assert sum(r["policy_compliant"] for r in op) == 106
    corrupt = next(r for r in data["validation"]["corrupt-record stress"]
                   if r["contract"] == "operational")
    assert corrupt["policy_compliant"] == 36
    assert corrupt["correct"] == 0
    assert corrupt["other_report"] == 36
    for name, sha in data["generated_sha256"].items():
        assert hashlib.sha256(outputs[Path(name)].encode()).hexdigest() == sha
