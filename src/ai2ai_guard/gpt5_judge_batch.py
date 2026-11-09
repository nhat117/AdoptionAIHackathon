"""Authorized full-judge execution: same frozen instrument, sharded evidence."""

import json
import math
import threading
from datetime import datetime, timezone

from .gpt5_judge_api import (
    FOLDER,
    MODEL,
    PRICING,
    VERSION,
    GPT5JudgeAPI,
    model_matches,
    response_text,
)
from .llm_judge import sha
from .review_client import append

AUTHORIZATION = "results/LLM_JUDGE_BUDGET_AUTHORIZATION_650.json"
EXECUTION_VERSION = "gpt5-full-capped-sharded-v1"
SHARD_BYTES = 8 * 1024 * 1024


def read_records(path):
    paths = ([path] if path.exists() else []) + sorted(path.parent.glob(path.stem + ".part*.jsonl"))
    return [json.loads(line) for p in paths for line in p.read_text().splitlines()]


def append_sharded(path, row, lock, limit=SHARD_BYTES):
    with lock:
        shards = sorted(path.parent.glob(path.stem + ".part*.jsonl"))
        target = shards[-1] if shards else path.with_name(path.stem + ".part0001.jsonl")
        if target.exists() and target.stat().st_size >= limit:
            index = int(target.stem.rsplit("part", 1)[1]) + 1
            target = path.with_name(f"{path.stem}.part{index:04d}.jsonl")
        append(target, row)


class FullJudgeAPI(GPT5JudgeAPI):
    """Only execution cap/storage differ from the smoke-tested instrument."""

    def __init__(self, root, cap_usd, client=None, max_attempts=3, sleeper=None):
        import time
        from urllib.parse import urlsplit

        authorization = json.loads((root / AUTHORIZATION).read_text())
        approved = authorization["authorized_total_usd"]
        if not math.isfinite(cap_usd) or not 0 < cap_usd <= approved or approved != 650:
            raise ValueError("explicit_cap_must_fit_recorded_650_total_authorization")
        if not 1 <= max_attempts <= 3:
            raise ValueError("invalid_retry_bound")
        if client is None:
            from openai import OpenAI

            client = OpenAI(max_retries=0, timeout=180,
                            default_headers={"Cache-Control": "no-store", "x-bt-use-cache": "never"})
        if urlsplit(str(client.base_url)).hostname != "api.braintrust.dev":
            raise ValueError("braintrust_endpoint_required_no_silent_provider_fallback")
        self.root, self.cap, self.aggregate, self.client = root, cap_usd, approved, client
        self.max_output, self.attempts, self.sleep = 8192, max_attempts, sleeper or time.sleep
        self.folder, self.raw_lock = root / FOLDER, threading.Lock()
        self.execution_hash = None
        append(self.folder / "authorizations.jsonl", {
            "judge_project_total_cap_usd": cap_usd, "aggregate_total_cap_usd": approved,
            "authorization_file": AUTHORIZATION, "authorization_sha256": sha((root / AUTHORIZATION).read_bytes()),
            "recorded_utc": datetime.now(timezone.utc).isoformat(),
            "source": "Explicit user-selected cumulative US$650 research cap; prior spending retained"})

    def create(self, messages, schema, request_key, expected_model=None):
        for attempt in range(self.attempts):
            request_id, reserve = self.reserve(messages, schema, request_key)
            try:
                response = self.client.chat.completions.create(
                    model=MODEL, messages=messages, reasoning_effort="high",
                    max_completion_tokens=self.max_output, store=False,
                    response_format={"type": "json_schema", "json_schema": {
                        "name": "multilingual_validation", "strict": True, "schema": schema}})
            except Exception as error:
                status = getattr(error, "status_code", None)
                retryable = status in (408, 409, 429) or (status is not None and status >= 500) or type(error).__name__ in ("APIConnectionError", "APITimeoutError")
                append(self.folder / "errors.jsonl", {
                    "request_key": request_key, "request_id": request_id, "attempt": attempt,
                    "error_type": type(error).__name__, "http_status": status, "retryable": retryable,
                    "messages_sha256": sha(messages), "billing": "Unknown, full reservation retained"})
                if not retryable or attempt + 1 == self.attempts:
                    raise RuntimeError("judge_request_failed_" + type(error).__name__) from None
                self.sleep(min(30, 2 ** attempt))
                continue
            raw = response.model_dump(mode="json")
            record = {"request_key": request_key, "request_id": request_id,
                      "timestamp_utc": datetime.now(timezone.utc).isoformat(), "attempt": attempt,
                      "profile": VERSION, "execution_version": EXECUTION_VERSION,
                      "execution_protocol_sha256": self.execution_hash,
                      "requested_model": MODEL, "reasoning_effort": "high",
                      "max_output_tokens": self.max_output, "messages": messages,
                      "messages_sha256": sha(messages), "raw_response": raw}
            append_sharded(self.folder / "raw_responses.jsonl", record, self.raw_lock)
            usage = raw.get("usage") or {}
            if all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("prompt_tokens", "completion_tokens")):
                actual = (usage["prompt_tokens"] * 1.25 + usage["completion_tokens"] * 10) / 1e6
                from .gpt5_judge_api import STAGE

                correction = {"stage": STAGE, "request_id": request_id, "request_key": request_key,
                              "reserved_usd": actual - reserve, "accounted_usd": actual,
                              "response_id": raw.get("id"), "usage": usage, "basis": PRICING["mode"]}
                append(self.root / "results/review_v3/ledger.jsonl", correction)
                append(self.folder / "cost_ledger.jsonl", correction)
            if not model_matches(raw.get("model")) or (expected_model and raw["model"] != expected_model):
                raise RuntimeError("judge_returned_model_mismatch_saved_for_audit")
            if not isinstance(raw.get("id"), str) or not raw["id"]:
                raise RuntimeError("judge_response_id_missing_saved_for_audit")
            return record, response_text(raw)
        raise RuntimeError("judge_retry_limit")
