"""Provisional accounting keeps frozen scientific calculations and raw evidence."""

import ast
import fcntl
import io
import json
from pathlib import Path

import pytest
from test_authentication_diagnostic import analyze as frozen
from test_authentication_diagnostic import args, module, run, technical_run  # noqa: F401
from test_authentication_escrow import prepared  # noqa: F401

REPORT = Path(__file__).parents[1] / "reports/authentication-diagnostic-v1"


def test_mechanical_science_code_equivalence():
    a = (REPORT / "analyze.py").read_text()
    b = (REPORT / "analyze_with_escrow.py").read_text()
    prefix = "    plan, cases = run.frozen()"
    assert (
        a[a.index(prefix) : a.index("    if pending:")]
        == b[b.index(prefix) : b.index("    if pending != escrow:")]
    )
    suffix = "    if abs(spent - billed)"
    assert (
        a[a.index(suffix) : a.index("    return dict(", a.index(suffix))]
        == b[b.index(suffix) : b.index("    return dict(", b.index(suffix))]
    )
    funcs = []
    for source in [a, b]:
        tree = ast.parse(source)
        flip = next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "sign_flip"
        )
        analyze = next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "analyze"
        )
        result = analyze.body[-1].value
        scientific = [k for k in result.keywords if k.arg not in {"mode", "budget"}]
        funcs.append((ast.dump(flip), [ast.dump(k) for k in scientific]))
    assert funcs[0] == funcs[1]


@pytest.fixture
def settled(technical_run, tmp_path, monkeypatch):  # noqa: F811
    root, plan, cases = technical_run
    manifests = list(root.glob("*/manifest.json"))
    review = dict(
        verdict="proceed",
        plan_sha256=run.digest(plan),
        admitted_models=["qwen"],
        receipt_sha256={
            p.parent.name: run.hashlib.sha256(p.read_bytes()).hexdigest()
            for p in manifests
        },
    )
    path = tmp_path / "preflight-review.json"
    path.write_text(json.dumps(review))
    lookup = {
        run.digest(
            run.prepare.payload(cases[j["case"]], j["wording"], plan["models"]["qwen"])
        ): (cases[j["case"]], j["wording"])
        for j in plan["jobs"]
        if j["model"] == "qwen" and j["phase"] == "diagnostic"
    }

    def fake(request, **kwargs):
        case, wording = lookup[run.digest(json.loads(request.data))]
        gold = case["gold"]
        if wording == "clarified":
            status, signal = gold["evidence_status"], gold["verified_signal"]
        elif gold["evidence_status"] == "verified":
            status, signal = "none", "Unknown"
        else:
            status, signal = "verified", "Danger"
        decision = dict(
            signal="Unknown",
            action="stay",
            message="Offline comparison fixture.",
            parents=[],
            evidence_status=status,
            verified_signal=signal,
        )
        config = plan["models"]["qwen"]
        return io.StringIO(
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
            )
        )

    monkeypatch.setattr(run.urllib.request, "urlopen", fake)
    run.main(args(execute=True, cap_usd=5, phase="diagnostic", preflight_review=path))
    return root


def scientific(summary):
    return {
        k: summary[k]
        for k in [
            "rows",
            "rates",
            "paired_wording_contrasts",
            "technically_valid",
            "failed_or_unattempted",
            "unit",
        ]
    }


def test_identical_settled_fixture_outputs(settled, monkeypatch):
    provisional = module("analyze_with_escrow")
    monkeypatch.setattr(
        provisional, "approved_escrow", lambda root: ({}, "offline-statistics-only")
    )
    a = frozen.analyze(settled)
    b = provisional.analyze(settled)
    assert scientific(a) == scientific(b)
    proof = next(
        c
        for c in b["paired_wording_contrasts"]
        if c["model"] == "qwen" and c["condition"] == "relayed_verified"
    )
    assert proof["seeds"] == 8 and proof["mean_difference"] == 1
    assert proof["p_unadjusted"] == 2 / 256


def test_pending_kept_and_original_still_rejects(settled, monkeypatch):
    provisional = module("analyze_with_escrow")
    before = frozen.analyze(settled)
    run.append(
        settled / "budget.jsonl",
        dict(type="reserve", ticket="offline-escrow", usd=0.04),
    )
    run.append(settled / "budget.jsonl", dict(type="halt", reason="offline"))
    monkeypatch.setattr(
        provisional,
        "approved_escrow",
        lambda root: ({"offline-escrow": 0.04}, "offline-accounting-only"),
    )
    raw = (settled / "budget.jsonl").read_bytes()
    with pytest.raises(ValueError, match="Unresolved billing"):
        frozen.analyze(settled)
    after = provisional.analyze(settled)
    assert scientific(before) == scientific(after)
    assert after["mode"] == "collected_under_escrow"
    assert after["budget"]["pending"] == {"offline-escrow": 0.04}
    assert after["budget"]["billing_status"] == "unresolved"
    assert after["budget"]["current_accounted_exposure_usd"] == pytest.approx(0.242)
    assert (
        after["budget"]["max_exposure_usd"]
        >= after["budget"]["current_accounted_exposure_usd"]
    )
    assert (settled / "budget.jsonl").read_bytes() == raw
    run.append(
        settled / "budget.jsonl", dict(type="reserve", ticket="unexpected", usd=0.04)
    )
    with pytest.raises(ValueError, match="Unapproved unresolved"):
        provisional.analyze(settled)


def test_excess_historical_exposure_rejected(settled, monkeypatch):
    provisional = module("analyze_with_escrow")
    monkeypatch.setattr(
        provisional, "approved_escrow", lambda root: ({}, "offline-accounting-only")
    )
    run.append(
        settled / "budget.jsonl", dict(type="reserve", ticket="over-cap", usd=26)
    )
    run.append(settled / "budget.jsonl", dict(type="settle", ticket="over-cap", cost=0))
    with pytest.raises(ValueError, match="budget exceeded"):
        provisional.analyze(settled)


@pytest.fixture
def bound_guard(prepared, monkeypatch):  # noqa: F811
    m, root, path, review, _ = prepared
    m.budget_class(path)(root, 25)
    (root / "run-plan.json").write_text(
        json.dumps(dict(plan_sha256=review["plan_sha256"], cap_usd=25))
    )
    (root / ("escrow-wrapper-" + review["wrapper_sha256"] + ".py")).write_bytes(
        Path(m.__file__).read_bytes()
    )
    provisional = module("analyze_with_escrow")
    monkeypatch.setattr(provisional, "escrow_guard", lambda: m)
    return provisional, m, root, review


def test_real_approval_binding_and_missing_marker(bound_guard):
    provisional, m, root, review = bound_guard
    assert provisional.approved_escrow(root)[0] == {review["escrow_ticket"]: 0.04}
    ledger = root / "budget.jsonl"
    rows = m.run.records(ledger)
    ledger.write_text(
        "".join(
            json.dumps(r) + "\n"
            for r in rows
            if r["type"] != "operational_escrow_resume"
        )
    )
    with pytest.raises(ValueError, match="resume marker"):
        provisional.approved_escrow(root)


def test_altered_approval_or_wrapper_rejected(bound_guard):
    provisional, _, root, review = bound_guard
    path = next(root.glob("escrow-review-*.json"))
    raw = path.read_bytes()
    path.write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="approval hash"):
        provisional.approved_escrow(root)
    path.write_bytes(raw)
    (root / ("escrow-wrapper-" + review["wrapper_sha256"] + ".py")).write_bytes(
        b"changed"
    )
    with pytest.raises(ValueError, match="wrapper copy"):
        provisional.approved_escrow(root)


def test_active_manifests_and_lock_rejected(bound_guard):
    provisional, _, root, _ = bound_guard
    p = root / "active" / "manifest.json"
    p.parent.mkdir()
    p.write_text(json.dumps(dict(status="running")))
    with pytest.raises(ValueError, match="active collection"):
        provisional.approved_escrow(root)
    with (root / "collector.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            provisional.analyze(root)
