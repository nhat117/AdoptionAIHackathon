"""Parameterized, durably accounted Braintrust Chat Completions transport."""

import fcntl
import json
import math
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .gpt5_judge_api import MODEL, PRICING, model_matches, response_text
from .gpt5_judge_batch import AUTHORIZATION, append_sharded
from .llm_judge import sha
from .review_client import append


def bound(messages, schema, max_output):
    size = len(json.dumps({"messages": messages, "schema": schema}).encode()) + 1024
    if size > 272000:
        raise ValueError("request_exceeds_short_context_cost_envelope")
    return (size * 1.25 + max_output * 10) / 1e6


def safe_provider_error(error):
    body = getattr(error, "body", None)
    if not isinstance(body, dict):
        return {"detail": "not_available"}
    body = body.get("error", body)
    if not isinstance(body, dict):
        return {"detail": "not_available"}
    result = {}
    for key in ("code", "type", "param", "message"):
        if isinstance(body.get(key), str):
            text = body[key]
            for name in ("OPENAI_API_KEY", "BRAINTRUST_API_KEY"):
                secret = os.environ.get(name)
                if secret:
                    text = text.replace(secret, "[REDACTED]")
            text = re.sub(r"(?i)bearer\s+\S+|sk-[A-Za-z0-9_-]+", "[REDACTED]", text)
            result[key] = text[:2000]
    return result


class BudgetedChatJudge:
    def __init__(self, root, profile, folder, stage, max_output, cap, client=None, sleeper=time.sleep):
        approved = json.loads((root / AUTHORIZATION).read_text())["authorized_total_usd"]
        if approved != 650 or not math.isfinite(cap) or not 0 < cap <= approved:
            raise ValueError("cap_must_fit_recorded_650_total_authorization")
        if not 1 <= max_output <= 32768:
            raise ValueError("invalid_output_bound")
        if client is None:
            from openai import OpenAI

            client = OpenAI(max_retries=0, timeout=300,
                            default_headers={"Cache-Control": "no-store", "x-bt-use-cache": "never"})
        if urlsplit(str(client.base_url)).hostname != "api.braintrust.dev":
            raise ValueError("braintrust_endpoint_required")
        self.root, self.profile, self.folder, self.stage = root, profile, root / folder, stage
        self.max_output, self.cap, self.aggregate, self.client = max_output, cap, approved, client
        self.lock, self.sleep = threading.Lock(), sleeper
        append(self.folder / "authorizations.jsonl", {
            "judge_project_total_cap_usd": cap, "aggregate_total_cap_usd": approved,
            "authorization_file": AUTHORIZATION, "authorization_sha256": sha((root / AUTHORIZATION).read_bytes()),
            "recorded_utc": datetime.now(timezone.utc).isoformat(),
            "source": "Operator allocation within explicit US$650 cumulative user approval; all prior costs retained"})

    def reserve(self, messages, schema, key):
        reserve, request_id = bound(messages, schema, self.max_output), str(uuid.uuid4())
        with (self.root / "results/api_ledger.jsonl").open() as old, (self.root / "results/review_v3/ledger.jsonl").open("a+") as new:
            fcntl.flock(old, fcntl.LOCK_EX)
            fcntl.flock(new, fcntl.LOCK_EX)
            total = math.fsum(json.loads(x)["reserved_usd"] for x in old)
            new.seek(0)
            rows = [json.loads(x) for x in new]
            total += math.fsum(r["reserved_usd"] for r in rows)
            project = math.fsum(r["reserved_usd"] for r in rows if r.get("stage") == self.stage)
            if total + reserve > self.aggregate or project + reserve > self.cap:
                raise RuntimeError("judge_or_aggregate_budget_cap_reached")
            row = {"stage": self.stage, "request_id": request_id, "request_key": key,
                   "model": MODEL, "reserved_usd": reserve, "time": time.time()}
            new.write(json.dumps(row) + "\n")
            new.flush()
            os.fsync(new.fileno())
        append(self.folder / "cost_ledger.jsonl", row)
        return request_id, reserve

    def create(self, messages, schema, key):
        for attempt in range(3):
            request_id, reserve = self.reserve(messages, schema, key)
            try:
                response = self.client.chat.completions.create(
                    model=MODEL, messages=messages, reasoning_effort="high", max_completion_tokens=self.max_output,
                    store=False, response_format={"type": "json_schema", "json_schema": {
                        "name": "multilingual_validation", "strict": True, "schema": schema}})
            except Exception as error:
                status = getattr(error, "status_code", None)
                retryable = status in (408, 409, 429) or (status is not None and status >= 500) or type(error).__name__ in ("APIConnectionError", "APITimeoutError")
                append(self.folder / "errors.jsonl", {
                    "request_key": key, "request_id": request_id, "attempt": attempt,
                    "error_type": type(error).__name__, "http_status": status, "retryable": retryable,
                    "messages_sha256": sha(messages), "provider_error": safe_provider_error(error),
                    "billing": "Unknown, full reservation retained"})
                if not retryable or attempt == 2:
                    raise RuntimeError("judge_request_failed_" + type(error).__name__) from None
                self.sleep(min(30, 2 ** attempt))
                continue
            raw = response.model_dump(mode="json")
            record = {"request_key": key, "request_id": request_id, "attempt": attempt,
                      "timestamp_utc": datetime.now(timezone.utc).isoformat(), "profile": self.profile,
                      "requested_model": MODEL, "reasoning_effort": "high", "max_output_tokens": self.max_output,
                      "messages": messages, "messages_sha256": sha(messages), "schema_sha256": sha(schema), "raw_response": raw}
            append_sharded(self.folder / "raw_responses.jsonl", record, self.lock)
            usage = raw.get("usage") or {}
            if all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("prompt_tokens", "completion_tokens")):
                actual = (usage["prompt_tokens"] * 1.25 + usage["completion_tokens"] * 10) / 1e6
                correction = {"stage": self.stage, "request_id": request_id, "request_key": key,
                              "reserved_usd": actual - reserve, "accounted_usd": actual,
                              "response_id": raw.get("id"), "usage": usage, "basis": PRICING["mode"]}
                append(self.root / "results/review_v3/ledger.jsonl", correction)
                append(self.folder / "cost_ledger.jsonl", correction)
            if not model_matches(raw.get("model")) or not isinstance(raw.get("id"), str) or not raw["id"]:
                raise RuntimeError("judge_model_or_response_id_mismatch_saved_for_audit")
            return record, response_text(raw)
        raise RuntimeError("judge_retry_limit")
