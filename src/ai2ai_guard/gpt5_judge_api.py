"""Braintrust GPT-5 judge transport; legacy Astra evidence remains untouched."""

import fcntl
import json
import math
import os
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .llm_judge import sha
from .review_client import append

MODEL = "gpt-5"
RETURNED_MODEL = "gpt-5-2025-08-07"
VERSION = "braintrust-gpt5-multilingual-v1"
FOLDER = "results/llm_judge_gpt5"
STAGE = "llm-judge-gpt5"
PRICING = {"model": MODEL, "input_per_million": 1.25, "output_per_million": 10.0,
           "source": "Existing GPT-5 worker accounting rates; no cache discount assumed",
           "mode": "Token-based estimate, not a provider invoice or verified proxy surcharge"}


def model_matches(model):
    return model == RETURNED_MODEL


def response_text(raw):
    choices = raw.get("choices", [])
    if len(choices) != 1 or choices[0].get("finish_reason") != "stop":
        raise ValueError("judge_incomplete_or_multiple_choices_saved_for_audit")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str) or choices[0]["message"].get("refusal"):
        raise ValueError("judge_missing_content_or_refusal_saved_for_audit")
    return content


def request_cost_bound(messages, schema, max_output_tokens=8192):
    size = len(json.dumps({"messages": messages, "schema": schema}).encode()) + 1024
    if size > 272000:
        raise ValueError("request_exceeds_short_context_cost_envelope")
    return (size * 1.25 + max_output_tokens * 10) / 1e6


class GPT5JudgeAPI:
    def __init__(self, root, cap_usd, client=None, max_output_tokens=8192,
                 max_attempts=3, sleeper=time.sleep):
        if not math.isfinite(cap_usd) or cap_usd <= 0:
            raise ValueError("explicit_positive_judge_spending_cap_required")
        if not 1 <= max_attempts <= 3 or not 1 <= max_output_tokens <= 128000:
            raise ValueError("invalid_retry_or_output_bound")
        self.aggregate = json.loads((root / "results/BUDGET_AUTHORIZATION.json").read_text())["authorized_total_usd"]
        if cap_usd > self.aggregate:
            raise ValueError("project_cap_exceeds_recorded_authorization")
        if client is None:
            from openai import OpenAI

            client = OpenAI(max_retries=0, timeout=180,
                            default_headers={"Cache-Control": "no-store", "x-bt-use-cache": "never"})
        if urlsplit(str(client.base_url)).hostname != "api.braintrust.dev":
            raise ValueError("braintrust_endpoint_required_no_silent_provider_fallback")
        self.root, self.cap, self.client = root, cap_usd, client
        self.max_output, self.attempts, self.sleep = max_output_tokens, max_attempts, sleeper
        self.folder = root / FOLDER
        append(self.folder / "authorizations.jsonl", {
            "judge_project_total_cap_usd": cap_usd, "aggregate_total_cap_usd": self.aggregate,
            "recorded_utc": datetime.now(timezone.utc).isoformat(),
            "source": "Cumulative GPT-5 profile allocation, not a reset of Astra/shared spending"})

    def reserve(self, messages, schema, key):
        reserve = request_cost_bound(messages, schema, self.max_output)
        request_id = str(uuid.uuid4())
        with (self.root / "results/api_ledger.jsonl").open() as old, (self.root / "results/review_v3/ledger.jsonl").open("a+") as new:
            fcntl.flock(old, fcntl.LOCK_EX)
            fcntl.flock(new, fcntl.LOCK_EX)
            old_total = math.fsum(json.loads(x)["reserved_usd"] for x in old)
            new.seek(0)
            rows = [json.loads(x) for x in new]
            total = old_total + math.fsum(r["reserved_usd"] for r in rows)
            project = math.fsum(r["reserved_usd"] for r in rows if r.get("stage") == STAGE)
            if total + reserve > self.aggregate or project + reserve > self.cap:
                raise RuntimeError("judge_or_aggregate_budget_cap_reached")
            row = {"stage": STAGE, "request_id": request_id, "request_key": key,
                   "model": MODEL, "reserved_usd": reserve, "time": time.time()}
            new.write(json.dumps(row) + "\n")
            new.flush()
            os.fsync(new.fileno())
        append(self.folder / "cost_ledger.jsonl", row)
        return request_id, reserve

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
                      "profile": VERSION, "requested_model": MODEL, "reasoning_effort": "high",
                      "max_output_tokens": self.max_output, "messages": messages,
                      "messages_sha256": sha(messages), "raw_response": raw}
            append(self.folder / "raw_responses.jsonl", record)
            usage = raw.get("usage") or {}
            if all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("prompt_tokens", "completion_tokens")):
                actual = (usage["prompt_tokens"] * 1.25 + usage["completion_tokens"] * 10) / 1e6
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
