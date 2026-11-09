"""Authorized full-run accounting/sharding tests; no live paid calls."""

import json
import runpy
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai2ai_guard.gpt5_judge_api import FOLDER, RETURNED_MODEL, STAGE, request_cost_bound
from ai2ai_guard.gpt5_judge_batch import (
    AUTHORIZATION,
    FullJudgeAPI,
    append_sharded,
    read_records,
)
from ai2ai_guard.llm_judge import ASSESSMENT_SCHEMA, request_messages, sha
from ai2ai_guard.review_client import ledger_total

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def root(tmp_path):
    (tmp_path / "results/review_v3").mkdir(parents=True)
    (tmp_path / AUTHORIZATION).write_text('{"authorized_total_usd":650}')
    (tmp_path / "results/api_ledger.jsonl").write_text('{"reserved_usd":5}\n')
    (tmp_path / "results/review_v3/ledger.jsonl").write_text('{"stage":"llm-judge","reserved_usd":1}\n')
    return tmp_path


def client(create):
    return SimpleNamespace(base_url="https://api.braintrust.dev/v1/proxy",
                           chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def response():
    return {"id": "synthetic-response", "model": RETURNED_MODEL,
            "choices": [{"finish_reason": "stop", "message": {"content": "{}"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 200}}


def test_recorded_authorization_required_and_prior_spending_counts(root):
    api = FullJudgeAPI(root, 650, client=client(lambda **kw: None))
    assert api.aggregate == 650
    (root / "results/review_v3/ledger.jsonl").write_text('{"stage":"llm-judge","reserved_usd":644.99}\n')
    with pytest.raises(RuntimeError, match="budget_cap"):
        api.reserve([], {}, "synthetic")
    with pytest.raises(ValueError):
        FullJudgeAPI(root, 651, client=client(lambda **kw: None))
    (root / AUTHORIZATION).unlink()
    with pytest.raises(FileNotFoundError):
        FullJudgeAPI(root, 650, client=client(lambda **kw: None))


def test_concurrent_reservations_cannot_overspend(root):
    bound = request_cost_bound([], {})
    (root / "results/review_v3/ledger.jsonl").write_text(json.dumps({"stage": "llm-judge", "reserved_usd": 645 - bound * 2.5}) + "\n")
    api = FullJudgeAPI(root, 650, client=client(lambda **kw: None))

    def reserve(i):
        try:
            api.reserve([], {}, str(i))
            return True
        except RuntimeError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        succeeded = list(pool.map(reserve, range(20)))
    assert sum(succeeded) == 2
    assert ledger_total(root / "results/api_ledger.jsonl") + ledger_total(root / "results/review_v3/ledger.jsonl") <= 650


def test_shards_preserve_smoke_and_concurrent_records(root):
    path = root / FOLDER / "raw_responses.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text('{"index":-1}\n')
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda i: append_sharded(path, {"index": i}, lock, limit=50), range(50)))
    assert path.read_text() == '{"index":-1}\n'
    assert sorted(r["index"] for r in read_records(path)) == list(range(-1, 50))
    assert len(list(path.parent.glob("raw_responses.part*.jsonl"))) > 1


def test_transport_instrument_unchanged_and_usage_accounted(root):
    calls = []

    def create(**kw):
        calls.append(kw)
        return SimpleNamespace(model_dump=lambda **kw: response())

    api = FullJudgeAPI(root, 650, client=client(create))
    api.execution_hash = "synthetic-frozen-execution"
    record, text = api.create([], ASSESSMENT_SCHEMA, "synthetic")
    assert text == "{}"
    assert calls[0]["model"] == "gpt-5" and calls[0]["reasoning_effort"] == "high"
    assert calls[0]["max_completion_tokens"] == 8192
    assert calls[0]["response_format"]["json_schema"]["strict"] is True
    assert record["execution_protocol_sha256"] == "synthetic-frozen-execution"
    assert len(read_records(root / FOLDER / "raw_responses.jsonl")) == 1
    assert ledger_total(root / "results/review_v3/ledger.jsonl") == pytest.approx(1.002125)
    assert all(r["stage"] == STAGE for r in read_records(root / FOLDER / "cost_ledger.jsonl"))


def test_dry_run_never_constructs_client(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = runpy.run_path(str(ROOT / "scripts/run_full_gpt5_judge.py"))
    scope = module["main"].__globals__
    scope["prepare_execution"] = lambda *args: ([], {}, "synthetic")

    def forbidden(*args, **kwargs):
        pytest.fail("Dry-run cannot make paid calls")

    scope["FullJudgeAPI"] = forbidden
    monkeypatch.setattr(sys, "argv", ["run_full_gpt5_judge.py"])
    module["main"]()


def test_full_runner_recovers_raw_and_resumes_without_replacing_answers(monkeypatch, root):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = runpy.run_path(str(ROOT / "scripts/run_full_gpt5_judge.py"))
    scope = module["run"].__globals__
    group = {"group_id": "synthetic", "intended_construct": {}, "record_condition": "absent",
             "source_group_sha256": "synthetic-source", "prompts": {}}
    for lang in ("en", "vi", "zh"):
        group["prompts"][lang] = {"peer_message": "synthetic", "messages": [
            {"role": "system", "content": "Synthetic engineering fixture"},
            {"role": "user", "content": '{"peer_message":"synthetic"}'}]}
    folder = root / FOLDER
    folder.mkdir(parents=True)
    (folder / "PROTOCOL.json").write_text("{}")
    (folder / "SMOKE_COMPLETE.json").write_text(json.dumps({
        "protocol_sha256": sha(b"{}"), "valid_structured_responses": 3, "returned_model": RETURNED_MODEL}))
    scope["prepare_execution"] = lambda *args: ([group], {}, "synthetic-execution")
    scope["validate_assessment"] = lambda text, *args: json.loads(text)
    calls = []

    def record(messages, key):
        return {"request_key": key, "messages": messages, "timestamp_utc": "synthetic-time",
                "raw_response": dict(response(), id="synthetic-" + key)}

    recovery = record(request_messages(group, 0), "original:synthetic:0")
    recovery["raw_response"]["choices"][0]["message"]["content"] = '{"test_fixture":true}'
    (folder / "raw_responses.jsonl").write_text(json.dumps(recovery) + "\n")

    class FakeAPI:
        def __init__(self, *args):
            pass

        def create(self, messages, schema, key, expected):
            calls.append(key)
            return record(messages, key), '{"test_fixture":true}'

    scope["FullJudgeAPI"] = FakeAPI
    module["run"](root, 2, 650)
    assert sorted(calls) == ["original:synthetic:1", "original:synthetic:2"]
    rows = read_records(folder / "judgments.jsonl")
    assert len(rows) == 3 and all(r["status"] == "VALID" for r in rows)
    module["run"](root, 2, 650)
    assert len(calls) == 2 and len(read_records(folder / "judgments.jsonl")) == 3
