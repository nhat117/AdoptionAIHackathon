"""Synthetic transport fixtures; not empirical linguistic judgments."""

import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from ai2ai_guard.gpt5_judge_api import (
    FOLDER,
    RETURNED_MODEL,
    STAGE,
    GPT5JudgeAPI,
    response_text,
)
from ai2ai_guard.llm_judge import ASSESSMENT_SCHEMA
from ai2ai_guard.review_client import ledger_total

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def budget(tmp_path):
    (tmp_path / "results/review_v3").mkdir(parents=True)
    (tmp_path / "results/BUDGET_AUTHORIZATION.json").write_text('{"authorized_total_usd":20}')
    (tmp_path / "results/api_ledger.jsonl").write_text('{"reserved_usd":5}\n')
    (tmp_path / "results/review_v3/ledger.jsonl").write_text('{"stage":"llm-judge","reserved_usd":1}\n')
    return tmp_path


def raw_response(model=RETURNED_MODEL, finish="stop"):
    return {"id": "chatcmpl-synthetic", "object": "chat.completion", "created": 1, "model": model,
            "choices": [{"index": 0, "finish_reason": finish, "message": {"role": "assistant", "content": "{}"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}}


def fake_client(create):
    return SimpleNamespace(base_url="https://api.braintrust.dev/v1/proxy",
                           chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_gpt5_sdk_chat_route_strict_schema_usage_and_no_credential_logging(budget):
    openai = pytest.importorskip("openai")
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=raw_response())

    client = openai.OpenAI(api_key="fixture-not-real", base_url="https://api.braintrust.dev/v1/proxy",
                           max_retries=0, default_headers={"x-bt-use-cache": "never"},
                           http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    api = GPT5JudgeAPI(budget, .5, client=client)
    record, text = api.create([{"role": "user", "content": "synthetic"}], ASSESSMENT_SCHEMA, "fixture")
    request = requests[0]
    body = json.loads(request.content)
    assert request.url.path == "/v1/proxy/chat/completions"
    assert request.headers["x-bt-use-cache"] == "never"
    assert body["model"] == "gpt-5" and body["reasoning_effort"] == "high"
    assert body["max_completion_tokens"] == 8192 and body["store"] is False
    assert body["response_format"]["json_schema"]["strict"] is True
    assert text == "{}" and record["raw_response"]["model"] == RETURNED_MODEL
    assert ledger_total(budget / "results/review_v3/ledger.jsonl") == pytest.approx(1.002125)
    assert "fixture-not-real" not in (budget / FOLDER / "raw_responses.jsonl").read_text()
    events = [json.loads(x) for x in (budget / FOLDER / "cost_ledger.jsonl").read_text().splitlines()]
    assert all(r["stage"] == STAGE for r in events)


def test_caps_and_existing_astra_reservations_are_not_reset(budget):
    calls = []

    def create(**kw):
        calls.append(kw)
        return SimpleNamespace(model_dump=lambda **kw: raw_response())

    api = GPT5JudgeAPI(budget, .001, client=fake_client(create))
    with pytest.raises(RuntimeError, match="budget_cap"):
        api.create([], {}, "fixture")
    assert not calls
    (budget / "results/review_v3/ledger.jsonl").write_text('{"stage":"llm-judge","reserved_usd":14.99}\n')
    api = GPT5JudgeAPI(budget, .5, client=fake_client(create))
    with pytest.raises(RuntimeError, match="budget_cap"):
        api.create([], {}, "fixture")
    assert not calls


@pytest.mark.parametrize("model,finish,exception", [("gpt-6-astra", "stop", RuntimeError),
                                                 (RETURNED_MODEL, "length", ValueError)])
def test_unexpected_or_incomplete_responses_are_durable_not_retried(budget, model, finish, exception):
    calls = []

    def create(**kw):
        calls.append(1)
        return SimpleNamespace(model_dump=lambda **kw: raw_response(model, finish))

    api = GPT5JudgeAPI(budget, .5, client=fake_client(create))
    with pytest.raises(exception):
        api.create([], {}, "fixture")
    assert len(calls) == 1
    assert (budget / FOLDER / "raw_responses.jsonl").exists()
    assert ledger_total(budget / "results/review_v3/ledger.jsonl") == pytest.approx(1.002125)


@pytest.mark.parametrize("status,attempts", [(401, 1), (404, 1), (429, 3), (500, 3)])
def test_transport_retries_bounded_and_errors_redacted(budget, status, attempts):
    calls, sleeps = [], []

    class ProviderError(Exception):
        status_code = status

    def create(**kw):
        calls.append(1)
        raise ProviderError("credential or provider text must never be logged")

    api = GPT5JudgeAPI(budget, 1, client=fake_client(create), sleeper=sleeps.append)
    with pytest.raises(RuntimeError, match="judge_request_failed"):
        api.create([], {}, "fixture")
    assert len(calls) == attempts and len(sleeps) == attempts - 1
    errors = (budget / FOLDER / "errors.jsonl").read_text()
    assert "credential or provider" not in errors
    assert ledger_total(budget / FOLDER / "cost_ledger.jsonl") > 0


def test_no_provider_fallback(budget):
    with pytest.raises(ValueError, match="braintrust_endpoint_required"):
        GPT5JudgeAPI(budget, .5, client=SimpleNamespace(base_url="https://api.openai.com/v1"))


def test_response_refusal_not_scored():
    raw = raw_response()
    raw["choices"][0]["message"]["refusal"] = "synthetic refusal"
    with pytest.raises(ValueError, match="refusal"):
        response_text(raw)


def test_dry_run_never_constructs_api(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = runpy.run_path(str(ROOT / "scripts/run_gpt5_judge.py"))
    scope = module["main"].__globals__
    scope["prepare"] = lambda: ([], {"synthetic": True})

    def forbidden(*args, **kwargs):
        pytest.fail("Dry-run cannot construct an API client")

    scope["GPT5JudgeAPI"] = forbidden
    monkeypatch.setattr(sys, "argv", ["run_gpt5_judge.py"])
    module["main"]()


def test_profile_is_separate_and_saved_gpt5_results_verify(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = runpy.run_path(str(ROOT / "scripts/report_llm_judge.py"))
    if not (ROOT / FOLDER / "PROTOCOL.json").exists():
        pytest.skip("GPT-5 profile not prepared")
    outputs = module["build"](ROOT, profile="gpt5")
    result = json.loads(outputs[Path(FOLDER) / "validation_results.json"])
    assert result["summary"]["model"] == "gpt-5"
    assert result["summary"]["same_worker_judge_model_family"] is True
    assert result["summary"]["historical_experimental_outputs_changed"] is False
    assert all(Path(FOLDER) in p.parents for p in outputs)
    assert result["summary"]["saved_valid_initial_judgments"] <= result["summary"]["planned_initial_judge_requests"]


@pytest.mark.parametrize("cap", [0, -1, float("inf"), float("nan"), 21])
def test_explicit_finite_authorized_cap_required(budget, cap):
    with pytest.raises(ValueError):
        GPT5JudgeAPI(budget, cap, client=fake_client(lambda **kw: None))


def test_full_run_requires_smoke_before_constructing_api(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = runpy.run_path(str(ROOT / "scripts/run_gpt5_judge.py"))
    scope = module["main"].__globals__
    folder = tmp_path / FOLDER
    folder.mkdir(parents=True)
    (folder / "PROTOCOL.json").write_text("{}")
    scope["ROOT"] = tmp_path
    scope["prepare"] = lambda: ([], {"synthetic": True})

    def forbidden(*args, **kwargs):
        pytest.fail("Missing smoke must block before API construction")

    scope["GPT5JudgeAPI"] = forbidden
    monkeypatch.setattr(sys, "argv", ["run_gpt5_judge.py", "--run", "--cap-usd", "0.5"])
    with pytest.raises(RuntimeError, match="smoke_required"):
        module["main"]()
