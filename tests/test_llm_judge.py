"""Synthetic engineering fixtures, not observed judge scores or human validation."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai2ai_guard.llm_judge import (
    ASSESSMENT_SCHEMA,
    CRITERIA,
    FEATURES,
    LANGUAGES,
    MODEL,
    VERSION,
    aggregate,
    agreement,
    extract_groups,
    language_order,
    quadratic_kappa,
    request_messages,
    sha,
    validate_assessment,
    validate_revision,
)
from ai2ai_guard.llm_judge_api import JudgeAPI, availability
from ai2ai_guard.review_client import ledger_total

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def group():
    g = {"group_id": "synthetic-group", "intended_construct": {"claimed_budget": 7950},
         "record_condition": "absent", "prompts": {}}
    for lang, text in zip(LANGUAGES, ("Budget 7950", "Ngân sách 7950", "预算7950")):
        g["prompts"][lang] = {"peer_message": text, "messages": [
            {"role": "system", "content": "Synthetic test, no model observation"},
            {"role": "user", "content": json.dumps({"peer_message": text, "trusted_record": None}, ensure_ascii=False)},
        ]}
    return g


def assessment(score=5):
    return {"rubric_version": VERSION, "construct_summary": "Synthetic fixture",
            "scores": dict.fromkeys(CRITERIA, score),
            "language_scores": {lang: dict.fromkeys(CRITERIA, score) for lang in LANGUAGES},
            "preservation": {f: {"status": "preserved", "material": False, "explanation": "Test fixture", "excerpts": []} for f in FEATURES},
            "mismatches": [], "limitations": "Engineering fixture only"}


def records(scores=(5, 5, 5)):
    return [{"group_id": "synthetic-group", "status": "VALID", "repeat": i, "assessment": assessment(s)} for i, s in enumerate(scores)]


def test_all_actual_prompts_are_extracted_and_aligned_without_worker_outcomes():
    groups, hashes = extract_groups(ROOT)
    assert len(groups) == 1920 and len(hashes) == 4
    assert sum(g["cohort"] == "primary" for g in groups) == 480
    assert sum(g["cohort"] == "wording_followup" for g in groups) == 1440
    assert all(set(g["prompts"]) == set(LANGUAGES) for g in groups)
    for g in groups:
        sent = request_messages(g, 0)
        packet = json.loads(sent[1]["content"])
        assert set(packet) == {"intended_construct", "record_condition", "prompts_in_randomized_order"}
        for prompt in packet["prompts_in_randomized_order"]:
            assert prompt["messages"] == g["prompts"][prompt["language"]]["messages"]


def test_duplicate_source_trials_are_rejected(tmp_path):
    source = ROOT / "results/measurement_v2_replication/workers.jsonl"
    rows = [json.loads(x) for x in source.read_text().splitlines()]
    rows[1]["trial_id"] = rows[0]["trial_id"]
    target = tmp_path / "results/measurement_v2_replication/workers.jsonl"
    target.parent.mkdir(parents=True)
    target.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="missing_or_duplicate"):
        extract_groups(tmp_path)


def test_randomized_balanced_order_and_blinded_revisions(group):
    orders = [language_order(group["group_id"], i) for i in range(3)]
    assert orders == [language_order(group["group_id"], i) for i in range(3)]
    assert all({row[i] for row in orders} == set(LANGUAGES) for i in range(3))
    before = sha(group)
    message = request_messages(group, 1, {"en": "Corrected wording 7950"})
    assert "previous_response_id" not in json.dumps(message)
    assert "assessment" not in json.loads(message[1]["content"])
    assert sha(group) == before


@pytest.mark.parametrize("bad", [0, 6, True, 4.5, "5"])
def test_strict_score_schema_rejects_invalid_values(group, bad):
    a = assessment()
    a["scores"][CRITERIA[0]] = bad
    with pytest.raises(ValueError):
        validate_assessment(json.dumps(a), group)


def test_schema_and_exact_excerpt_guard(group):
    a = assessment()
    assert validate_assessment(json.dumps(a), group) == a
    a["mismatches"] = [{"criterion": "numerical_values", "severity": "critical",
                        "explanation": "Synthetic mismatch", "excerpts": [{"language": "en", "scope": "peer_message", "text": "invented 9999"}]}]
    with pytest.raises(ValueError, match="excerpt_not"):
        validate_assessment(json.dumps(a), group)
    a["mismatches"][0]["excerpts"][0]["text"] = "Budget 7950"
    assert validate_assessment(json.dumps(a), group) == a


def test_low_score_requires_corresponding_evidence(group):
    a = assessment()
    a["scores"]["linguistic_naturalness"] = 3
    with pytest.raises(ValueError, match="low_score_without"):
        validate_assessment(json.dumps(a), group)


def test_provisional_thresholds_missing_data_disagreement_and_english_not_gold(group):
    assert aggregate(group, records())["outcome"] == "PASS"
    assert aggregate(group, records()[:2])["outcome"] == "PENDING"
    assert aggregate(group, records((3, 5, 5)))["outcome"] == "REVIEW_REQUIRED"
    rr = records()
    for r in rr:
        r["assessment"]["language_scores"]["en"]["translation_accuracy"] = 3
    assert aggregate(group, rr)["outcome"] == "REVIEW_REQUIRED"
    rr[0]["assessment"]["preservation"]["numerical_values"].update(status="changed", material=True)
    assert aggregate(group, rr)["outcome"] == "FAIL"
    with pytest.raises(ValueError, match="duplicate"):
        aggregate(group, [rr[0], rr[0], rr[2]])


def test_agreement_is_descriptive_and_degenerate_kappa_is_undefined():
    assert quadratic_kappa([1, 2, 5], [1, 2, 5]) == 1
    assert quadratic_kappa([5, 5], [5, 5]) is None
    assert quadratic_kappa([1, 1, 5, 5], [5, 5, 1, 1]) == -1
    a = agreement(records((3, 5, 5)))
    assert a["criteria"][CRITERIA[0]]["substantial_disagreement_groups"] == 1
    assert "NOT three independent humans" in a["interpretation"]


def test_revisions_keep_originals_separate_and_allow_english_corrections(group):
    draft = {"rubric_version": VERSION, "limitations": "Synthetic fixture", "proposals": [{
        "language": "en", "original_text": "Budget 7950", "identified_problem": "Synthetic phrasing concern",
        "supporting_explanation": "Unit test only", "supporting_excerpts": [{"language": "en", "scope": "peer_message", "text": "Budget 7950"}],
        "suggested_text": "Approved budget: 7950", "expected_improvement": "A model opinion, not a finding",
        "potential_research_impact": "New experiment needed",
    }]}
    before = copy.deepcopy(group)
    assert validate_revision(json.dumps(draft), group) == draft
    assert group == before
    draft["proposals"][0]["original_text"] = "Not the original"
    with pytest.raises(ValueError, match="revision_source"):
        validate_revision(json.dumps(draft), group)


@pytest.fixture
def budget_root(tmp_path):
    (tmp_path / "results/review_v3").mkdir(parents=True)
    (tmp_path / "results/BUDGET_AUTHORIZATION.json").write_text('{"authorized_total_usd":20}')
    (tmp_path / "results/api_ledger.jsonl").write_text('{"reserved_usd":1}\n')
    (tmp_path / "results/review_v3/ledger.jsonl").write_text("")
    return tmp_path


class FakeResponse:
    def __init__(self, model=MODEL, status="completed"):
        self.output_text = json.dumps(assessment())
        self.model = model
        self.status = status

    def model_dump(self, mode):
        return {"id": "resp-fixture", "model": self.model, "status": self.status,
                "output": [{"type": "message", "content": [{"type": "output_text", "text": self.output_text}]}],
                "usage": {"input_tokens": 100, "output_tokens": 200,
                          "output_tokens_details": {"reasoning_tokens": 100}}}


def test_bounded_retries_backoff_and_every_attempt_cost_is_preserved(budget_root, group):
    attempts, sleeps = [], []

    class RetryError(Exception):
        status_code = 429

    def create(**kwargs):
        attempts.append(kwargs)
        if len(attempts) < 3:
            raise RetryError("secret must never be logged")
        return FakeResponse()

    api = JudgeAPI(budget_root, 5, client=SimpleNamespace(responses=SimpleNamespace(create=create)), sleeper=sleeps.append)
    record, text = api.create(request_messages(group, 0), ASSESSMENT_SCHEMA, "fixture-request")
    assert sleeps == [1, 2] and len(attempts) == 3
    assert record["raw_response"]["model"] == MODEL
    assert json.loads(text)["rubric_version"] == VERSION
    assert ledger_total(budget_root / "results/review_v3/ledger.jsonl") > .01
    assert "secret must never" not in (budget_root / "results/llm_judge/errors.jsonl").read_text()
    assert attempts[0]["model"] == MODEL and attempts[0]["reasoning"] == {"effort": "high"}
    assert attempts[0]["store"] is False and "previous_response_id" not in attempts[0]


def test_nonretryable_auth_errors_do_not_get_retried(budget_root, group):
    calls = []

    class AuthError(Exception):
        status_code = 401

    def create(**kwargs):
        calls.append(1)
        raise AuthError("credential text must not be written")

    api = JudgeAPI(budget_root, 3, client=SimpleNamespace(responses=SimpleNamespace(create=create)))
    with pytest.raises(RuntimeError, match="judge_request_failed"):
        api.create(request_messages(group, 0), ASSESSMENT_SCHEMA, "fixture")
    assert len(calls) == 1


def test_budget_blocks_before_dispatch_and_model_mismatch_is_retained(budget_root, group):
    calls = []

    def create(**kwargs):
        calls.append(1)
        return FakeResponse(model="gpt-5")

    api = JudgeAPI(budget_root, .001, client=SimpleNamespace(responses=SimpleNamespace(create=create)))
    with pytest.raises(RuntimeError, match="budget_cap"):
        api.create(request_messages(group, 0), ASSESSMENT_SCHEMA, "fixture")
    assert calls == []
    api = JudgeAPI(budget_root, 3, client=SimpleNamespace(responses=SimpleNamespace(create=create)))
    with pytest.raises(RuntimeError, match="model_mismatch"):
        api.create(request_messages(group, 0), ASSESSMENT_SCHEMA, "fixture")
    assert "gpt-5" in (budget_root / "results/llm_judge/raw_responses.jsonl").read_text()


def test_metadata_availability_is_not_paid_inference_or_fallback():
    class MetadataError(Exception):
        status_code = 405

    def retrieve(model):
        assert model == MODEL
        raise MetadataError("No model metadata here")

    result = availability(SimpleNamespace(base_url="https://fixture.invalid/v1", models=SimpleNamespace(retrieve=retrieve)))
    assert result["status"] == "UNVERIFIED" and result["paid_inference_calls"] == 0


def test_official_sdk_uses_responses_api_and_structured_schema(budget_root, group):
    openai = pytest.importorskip("openai")
    import httpx

    requests = []

    def handler(request):
        requests.append(request)
        data = FakeResponse().model_dump(mode="json")
        data.update(object="response", created_at=1)
        return httpx.Response(200, json=data)

    client = openai.OpenAI(api_key="fixture-not-a-secret", base_url="https://fixture.invalid/v1",
                           max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    api = JudgeAPI(budget_root, 3, client=client)
    api.create(request_messages(group, 0), ASSESSMENT_SCHEMA, "fixture")
    sent = json.loads(requests[0].content)
    assert requests[0].url.path == "/v1/responses"
    assert sent["model"] == MODEL and sent["reasoning"]["effort"] == "high"
    assert sent["text"]["format"]["type"] == "json_schema" and sent["text"]["format"]["strict"] is True
    assert "fixture-not-a-secret" not in (budget_root / "results/llm_judge/raw_responses.jsonl").read_text()


def test_dry_run_does_not_construct_sdk_or_make_paid_requests(monkeypatch):
    import runpy
    import sys

    module = runpy.run_path(str(ROOT / "scripts/run_llm_judge.py"))
    scope = module["main"].__globals__
    scope["prepare"] = lambda: ([], {"synthetic_dry_run": True})

    def forbidden():
        pytest.fail("Dry-run must not construct API clients")

    scope["sdk_client"] = forbidden
    calls = []
    monkeypatch.setattr(scope["subprocess"], "run", lambda args, **kw: calls.append(args))
    monkeypatch.setattr(sys, "argv", ["run_llm_judge.py"])
    module["main"]()
    assert len(calls) == 1 and calls[0][-1].endswith("report_llm_judge.py")


def test_pending_artifacts_do_not_fabricate_scores(monkeypatch):
    import runpy

    module = runpy.run_path(str(ROOT / "scripts/report_llm_judge.py"))
    outputs = module["build"](ROOT)
    result = json.loads(outputs[Path("results/llm_judge/validation_results.json")])
    assert result["summary"]["aligned_groups"] == 1920
    if result["summary"]["saved_valid_initial_judgments"] == 0:
        assert all(g["outcome"] == "PENDING" and g["medians"] == {} for g in result["groups"])
        assert result["summary"]["completed_full_validation"] is False
    assert result["summary"]["historical_experimental_outputs_changed"] is False
