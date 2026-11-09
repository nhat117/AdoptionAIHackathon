"""Offline tests of the disclosed escrow exception; no provider calls."""

import argparse
import importlib.util
import io
import json
from pathlib import Path

import pytest

REPORT = Path(__file__).parents[1] / "reports/authentication-diagnostic-v1"
TICKET = "qwen-heldout-3001-Danger-direct_verified-current"


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "escrow_test", REPORT / "collect_with_escrow.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    plan, cases = m.run.frozen()
    jobs = [
        next(j for j in plan["jobs"] if j["id"] == TICKET),
        next(
            j
            for j in plan["jobs"]
            if j["id"] == "qwen-heldout-3000-Danger-direct_verified-current"
        ),
    ]
    plan = dict(plan, jobs=jobs)
    language = Path("data/experiment1/languages.json").read_bytes()
    monkeypatch.chdir(tmp_path)
    language_path = tmp_path / "data/experiment1/languages.json"
    language_path.parent.mkdir(parents=True)
    language_path.write_bytes(language)
    monkeypatch.setattr(m.run, "frozen", lambda: (plan, cases))
    monkeypatch.setattr(m.run, "review_admission", lambda *a, **kw: None)
    root = m.run.ROOT
    root.mkdir(parents=True)
    folder = root / TICKET
    folder.mkdir()
    request = json.dumps(
        m.run.prepare.payload(
            cases[jobs[0]["case"]], "current", plan["models"]["qwen"]
        ),
        ensure_ascii=False,
    ).encode()
    (folder / "request.json").write_bytes(request)
    admission = m.sha((REPORT / "preflight-review.json").read_bytes())
    manifest = dict(
        jobs[0],
        status="failed",
        error="HTTP Error 429: Too Many Requests",
        request_sha256=m.sha(request),
        admission_review_sha256=admission,
    )
    (folder / "manifest.json").write_text(json.dumps(manifest))
    m.run.append(root / "budget.jsonl", dict(type="reserve", ticket=TICKET, usd=0.04))
    halt = dict(type="halt", reason="uncertain billing or invalid cost")
    m.run.append(root / "budget.jsonl", halt)
    prefix = (root / "budget.jsonl").read_bytes()
    review = dict(
        verdict="proceed_under_escrow",
        plan_sha256=m.run.digest(plan),
        wrapper_sha256=m.sha(Path(m.__file__).read_bytes()),
        cap_usd=25,
        ledger_prefix_bytes=len(prefix),
        ledger_prefix_sha256=m.sha(prefix),
        covered_halt_sha256=[m.run.digest(halt)],
        escrow_ticket=TICKET,
        escrow_usd=0.04,
        failed_manifest_sha256=m.sha((folder / "manifest.json").read_bytes()),
        failed_request_sha256=m.sha(request),
        admission_review_sha256=admission,
    )
    path = tmp_path / "review.json"
    path.write_text(json.dumps(review))
    return m, root, path, review, prefix


def test_escrow_preserved_and_original_guard_unchanged(prepared):
    m, root, path, _, prefix = prepared
    b = m.budget_class(path)(root, 25)
    assert b.pending == {TICKET: 0.04} and not b.halted
    b.reserve("next", 0.04)
    b.settle("next", 0.001)
    assert b.pending == {TICKET: 0.04} and b.spent == 0.001
    assert (root / "budget.jsonl").read_bytes().startswith(prefix)
    assert m.OriginalBudget(root, 25).halted


@pytest.mark.parametrize(
    "field,value",
    [
        ("verdict", "PENDING"),
        ("wrapper_sha256", "0" * 64),
        ("plan_sha256", "0" * 64),
        ("escrow_ticket", "wrong"),
        ("cap_usd", 26),
        ("failed_manifest_sha256", "0" * 64),
        ("failed_request_sha256", "0" * 64),
        ("admission_review_sha256", "0" * 64),
    ],
)
def test_review_binding_rejections(prepared, field, value):
    m, root, path, review, _ = prepared
    review[field] = value
    path.write_text(json.dumps(review))
    with pytest.raises((ValueError, StopIteration)):
        m.budget_class(path)(root, 25)


def test_changed_prefix_and_new_uncertainty_stop(prepared):
    m, root, path, _, _ = prepared
    b = m.budget_class(path)(root, 25)
    b.reserve("new-unknown", 0.04)
    b.halt("uncertain billing or invalid cost")
    with pytest.raises(ValueError):
        m.budget_class(path)(root, 25)
    assert set(m.OriginalBudget(root, 25).pending) == {TICKET, "new-unknown"}


def test_changed_ledger_prefix_is_rejected(prepared):
    m, root, path, _, _ = prepared
    ledger = root / "budget.jsonl"
    ledger.write_text(ledger.read_text().replace('"usd": 0.04', '"usd": 0.03'))
    with pytest.raises(ValueError, match="prefix"):
        m.budget_class(path)(root, 25)


def test_new_pending_without_halt_is_rejected(prepared):
    m, root, path, _, _ = prepared
    m.run.append(
        root / "budget.jsonl", dict(type="reserve", ticket="another", usd=0.04)
    )
    with pytest.raises(ValueError, match="reservation"):
        m.budget_class(path)(root, 25)


def test_cap_denial_is_marked_before_dispatch(prepared):
    m, root, path, _, _ = prepared
    b = m.budget_class(path)(root, 25)
    b.spent = 24.95
    folder = root / "next"
    folder.mkdir()
    (folder / "manifest.json").write_text(json.dumps(dict(status="running")))
    with pytest.raises(RuntimeError):
        b.reserve("next", 0.04)
    assert (
        json.loads((folder / "manifest.json").read_text())["status"]
        == "blocked_before_dispatch"
    )
    assert b.pending == {TICKET: 0.04} and b.halted
    with pytest.raises(ValueError):
        m.budget_class(path)(root, 25)


def test_no_credential_read_in_default_dry_run(prepared, monkeypatch, capsys):
    m, _, _, _, _ = prepared
    monkeypatch.setattr(m.run, "load_dotenv", lambda: pytest.fail("credential read"))
    m.main(argparse.Namespace(execute=False, review=None))
    assert json.loads(capsys.readouterr().out)["inference_calls"] == 0


def test_attempted_failure_skipped_and_new_job_dispatched_once(prepared, monkeypatch):
    m, root, path, _, _ = prepared
    failed_before = (root / TICKET / "manifest.json").read_bytes()
    monkeypatch.setattr(m.run, "load_dotenv", lambda: None)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-placeholder")
    sent = []

    def response(request, **kwargs):
        sent.append(json.loads(request.data))
        config = m.run.frozen()[0]["models"]["qwen"]
        decision = dict(
            signal="Danger",
            action="evacuate",
            message="Offline test.",
            parents=[],
            evidence_status="verified",
            verified_signal="Danger",
        )
        return io.BytesIO(
            json.dumps(
                dict(
                    model=config["model"],
                    provider=config["returned_provider"],
                    usage={"cost": 0.001},
                    choices=[
                        dict(
                            finish_reason="stop",
                            message={"content": json.dumps(decision)},
                        )
                    ],
                )
            ).encode()
        )

    monkeypatch.setattr(m.run.urllib.request, "urlopen", response)
    m.main(argparse.Namespace(execute=True, review=path))
    assert len(sent) == 1
    assert (root / TICKET / "manifest.json").read_bytes() == failed_before
    assert m.OriginalBudget(root, 25).pending == {TICKET: 0.04}


def test_collector_lock_contention_stops_before_dispatch(prepared, monkeypatch):
    import fcntl

    m, root, path, _, _ = prepared
    monkeypatch.setattr(
        m.run.urllib.request, "urlopen", lambda *a, **k: pytest.fail("network")
    )
    with (root / "collector.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            m.main(argparse.Namespace(execute=True, review=path))
