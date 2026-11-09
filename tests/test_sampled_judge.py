"""Random-sample design/transport fixtures, not observed validation results."""

import copy
import json
import runpy
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from ai2ai_guard.gpt5_judge_api import RETURNED_MODEL
from ai2ai_guard.gpt5_judge_batch import AUTHORIZATION, read_records
from ai2ai_guard.judge_transport import BudgetedChatJudge, safe_provider_error
from ai2ai_guard.llm_judge import ASSESSMENT_SCHEMA, extract_groups
from ai2ai_guard.review_client import ledger_total
from ai2ai_guard.sampled_judge import (
    FOLDER,
    MAX_OUTPUT,
    QUOTE_INSTRUCTION,
    SEED,
    STAGE,
    STRATUM_FIELDS,
    VERSION,
    sample_groups,
    sample_messages,
    sample_schema,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def population():
    return extract_groups(ROOT)[0]


def test_five_percent_equal_probability_stratified_sample(population):
    selected, manifest = sample_groups(population)
    assert len(selected) == len({g["group_id"] for g in selected}) == 96
    assert Counter(g["cohort"] for g in selected) == {"primary": 24, "wording_followup": 72}
    strata = Counter(tuple(g[k] for k in STRATUM_FIELDS) for g in selected)
    assert len(strata) == 96 and set(strata.values()) == {1}
    assert manifest["population_groups"] == 1920 and manifest["requested_judgments"] == 288
    assert all(r["population_n"] == 20 and r["inclusion_probability"] == .05 for r in manifest["strata"])
    assert manifest["prior_scores_or_worker_outcomes_used"] is False


def test_reproducible_selection_independent_of_frame_order_or_previous_scores(population):
    selected, manifest = sample_groups(population)
    assert sample_groups(list(reversed(population))) == (selected, manifest)
    augmented = copy.deepcopy(population)
    for row in augmented:
        row["unused_prior_model_score"] = 1
        row["unused_worker_outcome"] = "adversarial fixture, never selection input"
    altered, altered_manifest = sample_groups(augmented)
    assert [g["group_id"] for g in altered] == [g["group_id"] for g in selected]
    assert altered_manifest == manifest
    assert [g["group_id"] for g in sample_groups(population, SEED + 1)[0]] != [g["group_id"] for g in selected]
    with pytest.raises(ValueError, match="sampling_frame"):
        sample_groups(population[:-1])


def test_three_separate_language_orders_and_legacy_schema(population):
    selected, _ = sample_groups(population)
    g = selected[0]
    orders = []
    for repeat in range(3):
        messages = sample_messages(g, repeat)
        assert QUOTE_INSTRUCTION in messages[0]["content"]
        prompts = json.loads(messages[1]["content"])["prompts_in_randomized_order"]
        orders.append([p["language"] for p in prompts])
        assert "independent_initial_assessments" not in messages[1]["content"]
    assert all(set(order[i] for order in orders) == {"en", "vi", "zh"} for i in range(3))
    assert sample_schema() == ASSESSMENT_SCHEMA
    assert "enum" not in sample_schema()["properties"]["mismatches"]["items"]["properties"]["excerpts"]["items"]["properties"]["text"]


@pytest.fixture
def root(tmp_path):
    (tmp_path / "results/review_v3").mkdir(parents=True)
    (tmp_path / AUTHORIZATION).write_text('{"authorized_total_usd":650}')
    (tmp_path / "results/api_ledger.jsonl").write_text('{"reserved_usd":5}\n')
    (tmp_path / "results/review_v3/ledger.jsonl").write_text('{"stage":"llm-judge","reserved_usd":2}\n')
    return tmp_path


def test_sample_transport_model_tokens_schema_cost_and_separate_evidence(root, population):
    openai = pytest.importorskip("openai")
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"id": "synthetic-sample", "object": "chat.completion", "created": 1,
                                        "model": RETURNED_MODEL, "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "{}"}}],
                                        "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}})

    client = openai.OpenAI(api_key="fixture-not-real", base_url="https://api.braintrust.dev/v1/proxy", max_retries=0,
                           http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    api = BudgetedChatJudge(root, VERSION, FOLDER, STAGE, MAX_OUTPUT, 60, client=client)
    api.create(sample_messages(population[0], 0), sample_schema(), "synthetic")
    body = json.loads(requests[0].content)
    assert body["max_completion_tokens"] == 16384 and body["reasoning_effort"] == "high"
    assert body["response_format"]["json_schema"]["schema"] == ASSESSMENT_SCHEMA
    raw = read_records(root / FOLDER / "raw_responses.jsonl")
    assert len(raw) == 1 and raw[0]["profile"] == VERSION
    assert ledger_total(root / "results/review_v3/ledger.jsonl") == pytest.approx(2.002125)
    assert not (root / "results/llm_judge_gpt5/raw_responses.jsonl").exists()


def test_provider_diagnostics_redact_credentials(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sensitive-fixture-value")
    error = SimpleNamespace(body={"error": {"code": "invalid_schema", "param": "response_format",
                                           "message": "sensitive-fixture-value Bearer other-secret sk-example123"}})
    detail = safe_provider_error(error)
    assert detail["code"] == "invalid_schema" and detail["param"] == "response_format"
    assert "sensitive-fixture-value" not in str(detail) and "other-secret" not in str(detail) and "sk-example123" not in str(detail)


def test_aggregate_cap_still_applies_to_sample(root):
    def forbidden(**kw):
        pytest.fail("No network call allowed when budget is exhausted")

    client = SimpleNamespace(base_url="https://api.braintrust.dev/v1/proxy", chat=SimpleNamespace(completions=SimpleNamespace(create=forbidden)))
    api = BudgetedChatJudge(root, VERSION, FOLDER, STAGE, MAX_OUTPUT, 60, client=client)
    (root / "results/review_v3/ledger.jsonl").write_text('{"stage":"older-study","reserved_usd":644.99}\n')
    with pytest.raises(RuntimeError, match="budget_cap"):
        api.create([], {}, "synthetic")


@pytest.mark.parametrize("status,attempts", [(400, 1), (429, 3)])
def test_sample_retries_are_bounded_and_provider_diagnostic_is_preserved(root, status, attempts):
    calls, sleeps = [], []

    class ProviderError(Exception):
        status_code = status
        body = {"code": "synthetic_provider_error", "param": "response_format", "message": "Synthetic diagnostic"}

    def create(**kwargs):
        calls.append(1)
        raise ProviderError()

    client = SimpleNamespace(base_url="https://api.braintrust.dev/v1/proxy", chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    api = BudgetedChatJudge(root, VERSION, FOLDER, STAGE, MAX_OUTPUT, 60, client=client, sleeper=sleeps.append)
    with pytest.raises(RuntimeError, match="judge_request_failed"):
        api.create([], {}, "synthetic")
    assert len(calls) == attempts and len(sleeps) == attempts - 1
    errors = read_records(root / FOLDER / "errors.jsonl")
    assert errors[0]["provider_error"]["param"] == "response_format"
    assert ledger_total(root / FOLDER / "cost_ledger.jsonl") > 0


def test_dry_run_never_constructs_client(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = runpy.run_path(str(ROOT / "scripts/run_sampled_judge.py"))
    scope = module["main"].__globals__
    scope["prepare"] = lambda: ([], {"synthetic": True})

    def forbidden(*args, **kwargs):
        pytest.fail("Dry-run cannot construct an API client")

    scope["BudgetedChatJudge"] = forbidden
    monkeypatch.setattr(sys, "argv", ["run_sampled_judge.py"])
    module["main"]()


def test_sample_report_never_claims_full_corpus_validation(monkeypatch):
    if not (ROOT / FOLDER / "PROTOCOL.json").exists():
        pytest.skip("Sample profile not prepared")
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = runpy.run_path(str(ROOT / "scripts/report_llm_judge.py"))
    outputs = module["build"](ROOT, profile="gpt5-sample")
    result = json.loads(outputs[Path(FOLDER) / "validation_results.json"])
    summary = result["summary"]
    assert summary["completed_full_validation"] is False
    assert summary["aligned_groups"] == 96 and summary["planned_initial_judge_requests"] == 288
    assert summary["unsampled_groups_not_validated"] == 1824
    assert len(result["groups"]) == 96
