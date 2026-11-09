import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_csv_export_preserves_interaction_only_fields(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = runpy.run_path(str(ROOT / "scripts/run_research_pipeline.py"))
    result = module["csv_text"]([
        {"kind": "language", "difference": .1},
        {"kind": "interaction", "difference": .2, "record_reference": "correct"},
    ])
    assert "record_reference" in result and "correct" in result
    assert "\r\n" not in result


def test_original_blind_monitor_class_is_unchanged():
    import ast
    import subprocess

    filename = "src/ai2ai_guard/budget_claims.py"
    old = subprocess.check_output(
        ["git", "show", f"1dcf401:{filename}"], cwd=ROOT, text=True
    )
    current = (ROOT / filename).read_text()

    def definition(source):
        return next(n for n in ast.parse(source).body
                    if isinstance(n, ast.ClassDef) and n.name == "BlindMonitor")

    assert ast.dump(definition(old)) == ast.dump(definition(current))


def test_final_report_is_bound_to_machine_readable_results():
    path = ROOT / "results/review_v3/analysis.json"
    if not path.exists():
        import pytest

        pytest.skip("Final pipeline artifacts not generated yet")
    data = json.loads(path.read_text())
    for name, expected in data["generated_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    assert data["strict"]["strategies"]["source_only"][
        "target_relay_block_recall"
    ]["numerator"] == 90
    assert data["key_case_sensitivity"]["strategies"]["source_only"][
        "target_relay_block_recall"
    ]["numerator"] == 91
    assert data["key_case_sensitivity"]["strategies"]["source_freshness"][
        "stale_reliance_block_recall"
    ]["numerator"] == 458
    original = json.loads((ROOT / "results/BUDGET_AUTHORIZATION.json").read_text())
    approved = original["authorized_total_usd"]
    additional = ROOT / "results/LLM_JUDGE_BUDGET_AUTHORIZATION_650.json"
    if additional.exists():
        approved = max(
            approved, json.loads(additional.read_text())["authorized_total_usd"]
        )
    assert data["cost"]["cap_usd"] == approved
    assert data["cost"]["aggregate_accounted_usd"] <= approved
