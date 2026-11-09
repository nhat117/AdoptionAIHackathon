"""Offline-only diagnostic design, execution gates, provenance and budget tests."""

import argparse
import importlib.util
import io
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
REPORT = ROOT / "reports/authentication-diagnostic-v1"


def module(name):
    spec = importlib.util.spec_from_file_location(
        "diagnostic_test_" + name, REPORT / (name + ".py")
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


prepare, run, analyze = module("prepare"), module("run"), module("analyze")


def args(**changes):
    defaults = dict(
        phase="preflight",
        model="qwen",
        execute=False,
        cap_usd=None,
        preflight_review=None,
    )
    return argparse.Namespace(**(defaults | changes))


def test_frozen_design_counts_and_no_hidden_labels():
    plan, cases = run.frozen()
    assert len(plan["jobs"]) == 1010 and len(cases) == 102
    assert sum(r["split"] == "heldout" for r in cases.values()) == 96
    assert sum(r["split"] == "discovery" for r in cases.values()) == 4
    for row in cases.values():
        if row["split"] != "heldout":
            continue
        assert set(row["view"]) == {
            "agent",
            "round",
            "neighbours",
            "language",
            "history",
        }
        for message in row["view"]["history"]:
            assert re.fullmatch("[0-9a-f]{12}", message["id"])
            for capsule in message.get("capsules", []):
                assert re.fullmatch("[0-9a-f]{12}", capsule["id"])
                if capsule["authenticated"]:
                    assert capsule["signal"] == row["truth"]


def test_counterfactual_unverified_states_are_indistinguishable():
    true = prepare.synthetic(3000, "Danger", "unverified_true")
    false = prepare.synthetic(3000, "Safe", "unverified_false")
    assert true["view"] == false["view"]
    assert (
        true["gold"]
        == false["gold"]
        == dict(evidence_status="unverified", verified_signal="Unknown")
    )
    assert (
        prepare.synthetic(3000, "Danger", "no_focal_evidence")["view"]
        == (prepare.synthetic(3000, "Safe", "no_focal_evidence")["view"])
    )


def test_current_and_clarified_differ_only_by_clarification():
    assert prepare.instructions("clarified") == (
        prepare.instructions("current") + "\n\n" + prepare.CLARIFICATION
    )
    assert "evidence_status" in prepare.instructions("current")


def test_wrong_behavior_remains_technically_valid():
    case = prepare.synthetic(3000, "Danger", "direct_verified")
    wrong = dict(
        signal="Unknown",
        action="stay",
        message="I cannot verify this.",
        parents=[],
        evidence_status="unverified",
        verified_signal="Unknown",
    )
    assert run.validate_response(wrong, case["view"]) == wrong


def test_dry_run_never_reads_credentials_or_calls_network(monkeypatch, capsys):
    def forbidden(*a, **kw):
        raise AssertionError("Unexpected credentials/network access")

    monkeypatch.setattr(run, "load_dotenv", forbidden)
    monkeypatch.setattr(run.urllib.request, "urlopen", forbidden)
    run.main(args())
    assert json.loads(capsys.readouterr().out)["inference_calls"] == 0


@pytest.mark.parametrize("cap", [None, -1, 0, float("nan"), float("inf")])
def test_execution_requires_finite_positive_new_cap(cap):
    with pytest.raises(ValueError, match="authorized fresh"):
        run.main(args(execute=True, cap_usd=cap))


def test_diagnostic_requires_preflight_review_before_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "ROOT", tmp_path / "run")
    monkeypatch.setattr(run, "load_dotenv", lambda: pytest.fail("Credentials read"))
    with pytest.raises(ValueError, match="preflight review"):
        run.main(args(phase="diagnostic", execute=True, cap_usd=5))


def test_reservations_and_uncertain_billing_survive_reload(tmp_path):
    budget = run.Budget(tmp_path, 0.05)
    budget.reserve("one", 0.04)
    with pytest.raises(RuntimeError):
        budget.reserve("two", 0.04)
    assert run.Budget(tmp_path, 0.05).halted
    budget.settle("one", 0.001)
    assert not run.Budget(tmp_path, 0.05).halted
    with pytest.raises(ValueError):
        budget.reserve("bad", float("nan"))


@pytest.fixture
def technical_run(tmp_path, monkeypatch):
    root = tmp_path / "run"
    monkeypatch.setattr(run, "ROOT", root)
    monkeypatch.setattr(run, "load_dotenv", lambda: None)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret-never-real")
    plan, cases = run.frozen()
    config = plan["models"]["qwen"]
    calls = []

    def fake_http(request, **kwargs):
        body = json.loads(request.data)
        calls.append(body)
        assert "temperature" not in body and body["reasoning"] == {"effort": "low"}
        assert body["provider"]["allow_fallbacks"] is False
        # Deliberately wrong evidence recognition/actions: still technically valid.
        decision = dict(
            signal="Unknown",
            action="stay",
            message="Cannot verify.",
            parents=[],
            evidence_status="unverified",
            verified_signal="Unknown",
        )
        return io.StringIO(
            json.dumps(
                dict(
                    model=config["model"],
                    provider=config["returned_provider"],
                    usage=dict(cost=0.001),
                    choices=[
                        dict(
                            finish_reason="stop",
                            message=dict(content=json.dumps(decision)),
                        )
                    ],
                )
            )
        )

    monkeypatch.setattr(run.urllib.request, "urlopen", fake_http)
    run.main(args(execute=True, cap_usd=5))
    assert len(calls) == 2
    return root, plan, cases


def test_technical_admission_does_not_select_correct_answers(technical_run, tmp_path):
    root, plan, _ = technical_run
    manifests = list(root.glob("*/manifest.json"))
    assert all(json.loads(p.read_text())["status"] == "valid" for p in manifests)
    review = dict(
        verdict="proceed",
        plan_sha256=run.digest(plan),
        admitted_models=["qwen"],
        receipt_sha256={
            p.parent.name: run.hashlib.sha256(p.read_bytes()).hexdigest()
            for p in manifests
        },
    )
    path = tmp_path / "review.json"
    path.write_text(json.dumps(review))
    run.review_admission(path, plan, "qwen")
    result = analyze.analyze(root)
    assert result["technically_valid"] == 2
    assert all(r["recognition"] == 0 for r in result["rows"])
    assert all(
        "test-secret-never-real" not in p.read_text() for p in root.rglob("*.json")
    )


def test_changed_cap_cannot_reset_same_ledger(technical_run):
    with pytest.raises(ValueError, match="plan/cap differs"):
        run.main(args(execute=True, cap_usd=6))


def test_tampered_raw_response_is_rejected(technical_run):
    root, _, _ = technical_run
    path = next(root.glob("*/response.json"))
    path.write_text(path.read_text() + " ")
    with pytest.raises(ValueError, match="Response hash mismatch"):
        analyze.analyze(root)


def test_budget_bound_covers_every_prepared_request():
    plan, cases = run.frozen()
    for job in plan["jobs"]:
        config = plan["models"][job["model"]]
        size = len(
            json.dumps(
                prepare.payload(cases[job["case"]], job["wording"], config),
                ensure_ascii=False,
            ).encode()
        )
        assert size <= plan["input_byte_cap"]
        price = config["price_cap_per_million"]
        bound = (
            (size + 2048) * price["prompt"] + 4096 * price["completion"]
        ) / 1_000_000
        assert bound < config["reservation_usd"]


def test_exact_sign_flip_with_zero_differences():
    assert analyze.sign_flip([1] * 8) == 2 / 256
    assert analyze.sign_flip([1, 1, 1, 0, 0, 0, 0, 0]) == 0.25
    assert analyze.sign_flip([0] * 8) == 1


def test_eight_contexts_have_real_structural_variation():
    rows = [
        prepare.synthetic(seed, "Danger", "relayed_verified")
        for seed in range(3000, 3008)
    ]
    histories = [row["view"]["history"] for row in rows]
    assert len(histories[0]) == 2
    assert len(histories[5]) == 4  # Three peers plus focal evidence.
    assert len(histories[6]) == 9  # Longer history.
    absent = next(m for m in histories[3] if m.get("capsules"))
    assert absent["parents"] and absent["parents"][0] not in {
        m["id"] for m in histories[3]
    }
    present = next(m for m in histories[4] if m.get("capsules"))
    assert present["parents"][0] in {m["id"] for m in histories[4]}
    for seed in range(3000, 3008):
        a = prepare.synthetic(seed, "Danger", "unverified_true")
        b = prepare.synthetic(seed, "Safe", "unverified_false")
        assert a["view"] == b["view"]
        empty = prepare.synthetic(seed, "Danger", "no_focal_evidence")
        claims = any(
            m["signal"] in {"Safe", "Danger"} for m in empty["view"]["history"]
        )
        assert empty["gold"]["evidence_status"] == ("unverified" if claims else "none")


def test_admission_review_is_retained_and_audited(technical_run, tmp_path):
    root, plan, _ = technical_run
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
    path = tmp_path / "review.json"
    path.write_text(json.dumps(review))
    run.main(args(phase="diagnostic", execute=True, cap_usd=5, preflight_review=path))
    saved = list(root.glob("admission-*.json"))
    assert len(saved) == 1 and saved[0].read_bytes() == path.read_bytes()
    result = analyze.analyze(root)
    assert result["technically_valid"] == 202
    assert all("action" in r and "reported_status" in r for r in result["rows"])
    saved[0].write_text(saved[0].read_text() + " ")
    with pytest.raises(ValueError, match="Admission review missing or changed"):
        analyze.analyze(root)


def test_preparation_cannot_overwrite_data_after_collection(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    live = tmp_path / "runs/authentication-diagnostic-v1/a/manifest.json"
    live.parent.mkdir(parents=True)
    live.write_text("{}")
    data = tmp_path / "data/authentication-diagnostic-v1/cases.jsonl"
    data.parent.mkdir(parents=True)
    data.write_text("frozen sentinel")
    with pytest.raises(ValueError, match="Preparation locked"):
        prepare.freeze()
    assert data.read_text() == "frozen sentinel"
