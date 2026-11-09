"""V2 instrument fixtures: no empirical model quality claims."""

import copy
import json
import runpy
import sys
from pathlib import Path

import httpx
import pytest

from ai2ai_guard.gpt5_judge_api import RETURNED_MODEL
from ai2ai_guard.gpt5_judge_batch import AUTHORIZATION, read_records
from ai2ai_guard.gpt5_judge_v2 import (
    FOLDER,
    MAX_OUTPUT,
    VERSION,
    JudgeV2,
    assessment_messages,
    constrained_schema,
    cost_bound,
)
from ai2ai_guard.llm_judge import (
    ASSESSMENT_SCHEMA,
    CRITERIA,
    FEATURES,
    LANGUAGES,
    extract_groups,
    schema_validate,
    validate_assessment,
)
from ai2ai_guard.llm_judge import VERSION as RUBRIC_VERSION
from ai2ai_guard.review_client import ledger_total

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def group():
    return extract_groups(ROOT)[0][0]


def fixture_assessment(group):
    return {"rubric_version": RUBRIC_VERSION, "construct_summary": "Synthetic engineering fixture",
            "scores": dict.fromkeys(CRITERIA, 5),
            "language_scores": {lang: dict.fromkeys(CRITERIA, 5) for lang in LANGUAGES},
            "preservation": {key: {"status": "preserved", "material": False,
                                   "explanation": "Synthetic", "excerpts": []} for key in FEATURES},
            "mismatches": [], "limitations": "Synthetic, not a model observation"}


def test_schema_only_allows_exact_whole_source_fields_without_mutating_legacy(group):
    before = copy.deepcopy(ASSESSMENT_SCHEMA)
    schema = constrained_schema(group)
    enum = schema["properties"]["mismatches"]["items"]["properties"]["excerpts"]["items"]["properties"]["text"]["enum"]
    expected = {text for p in group["prompts"].values() for text in (
        p["peer_message"], p["messages"][0]["content"], p["messages"][1]["content"])}
    assert set(enum) == expected
    assert before == ASSESSMENT_SCHEMA
    value = fixture_assessment(group)
    excerpt = {"language": "en", "scope": "peer_message", "text": group["prompts"]["en"]["peer_message"]}
    value["mismatches"] = [{"criterion": CRITERIA[0], "severity": "minor", "explanation": "Synthetic", "excerpts": [excerpt]}]
    schema_validate(value, schema)
    validate_assessment(json.dumps(value), group)
    excerpt["text"] = "Fabricated or normalized quotation"
    with pytest.raises(ValueError, match="schema_string"):
        schema_validate(value, schema)


def test_revised_schema_quotes_actual_revised_source_not_prior_scores(group):
    replacements = {lang: "synthetic revised " + lang for lang in LANGUAGES}
    schema = constrained_schema(group, replacements)
    enum = schema["properties"]["mismatches"]["items"]["properties"]["excerpts"]["items"]["properties"]["text"]["enum"]
    assert set(replacements.values()) <= set(enum)
    messages = assessment_messages(group, 1, replacements)
    assert "EXACT COMPLETE" in messages[0]["content"]
    prompts = json.loads(messages[1]["content"])["prompts_in_randomized_order"]
    assert all(p["peer_message"] == replacements[p["language"]] for p in prompts)
    assert "independent_initial_assessments" not in messages[1]["content"]


def test_v2_sdk_envelope_and_separate_evidence_accounting(tmp_path, group):
    openai = pytest.importorskip("openai")
    (tmp_path / "results/review_v3").mkdir(parents=True)
    (tmp_path / AUTHORIZATION).write_text('{"authorized_total_usd":650}')
    (tmp_path / "results/api_ledger.jsonl").write_text('{"reserved_usd":5}\n')
    (tmp_path / "results/review_v3/ledger.jsonl").write_text('{"stage":"llm-judge-gpt5","reserved_usd":2}\n')
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"id": "synthetic", "model": RETURNED_MODEL, "object": "chat.completion", "created": 1,
                                        "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "{}"}}],
                                        "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}})

    client = openai.OpenAI(api_key="synthetic-not-real", base_url="https://api.braintrust.dev/v1/proxy", max_retries=0,
                           http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    api = JudgeV2(tmp_path, 650, client=client)
    api.create(assessment_messages(group, 0), constrained_schema(group), "synthetic")
    body = json.loads(requests[0].content)
    assert body["max_completion_tokens"] == MAX_OUTPUT == 16384
    assert body["reasoning_effort"] == "high" and body["model"] == "gpt-5"
    assert body["response_format"]["json_schema"]["strict"] is True
    raw = read_records(tmp_path / FOLDER / "raw_responses.jsonl")
    assert raw[0]["profile"] == VERSION and raw[0]["max_output_tokens"] == 16384
    assert ledger_total(tmp_path / "results/review_v3/ledger.jsonl") == pytest.approx(2.002125)
    assert not (tmp_path / "results/llm_judge_gpt5/raw_responses.jsonl").exists()
    assert cost_bound(assessment_messages(group, 0), constrained_schema(group)) > .16384


def test_v2_dry_run_never_constructs_client(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = runpy.run_path(str(ROOT / "scripts/run_gpt5_judge_v2.py"))
    scope = module["main"].__globals__
    scope["prepare"] = lambda: ([], {"synthetic": True})

    def forbidden(*args, **kwargs):
        pytest.fail("Dry-run cannot create a paid client")

    scope["JudgeV2"] = forbidden
    monkeypatch.setattr(sys, "argv", ["run_gpt5_judge_v2.py"])
    module["main"]()
