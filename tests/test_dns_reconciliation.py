"""Only verified DNS failures release reservations; unknown billing stays blocked."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "continuation",
    Path(__file__).parents[1] / "reports/overnight-experiments/continue.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(root, error):
    folder = root / "failed-game"
    folder.mkdir()
    (folder / "manifest.json").write_text(
        json.dumps(dict(status="failed", error_type="URLError", error=error))
    )
    ledger = root / "budget.jsonl"
    ledger.write_text(
        json.dumps(dict(type="reserve", ticket="failed-game:1"))
        + "\n"
        + json.dumps(dict(type="halt", reason="uncertain request outcome"))
        + "\n"
    )


def test_dns_release_is_audited_and_resume_is_idempotent(tmp_path):
    fixture(
        tmp_path,
        "<urlopen error [Errno 8] nodename nor servname provided, or not known>",
    )
    b = module.reconcile(tmp_path)
    assert not b.pending and not b.halted
    before = (tmp_path / "budget.jsonl").read_text()
    b = module.reconcile(tmp_path)
    assert not b.pending and not b.halted
    assert before == (tmp_path / "budget.jsonl").read_text()
    # Game remains failed and will be skipped by the frozen runner.
    assert (
        json.loads((tmp_path / "failed-game/manifest.json").read_text())["status"]
        == "failed"
    )


def test_timeout_does_not_release_uncertain_billing(tmp_path):
    fixture(tmp_path, "<urlopen error timed out>")
    before = (tmp_path / "budget.jsonl").read_text()
    with pytest.raises(RuntimeError, match="proven pre-connect"):
        module.reconcile(tmp_path)
    assert before == (tmp_path / "budget.jsonl").read_text()
