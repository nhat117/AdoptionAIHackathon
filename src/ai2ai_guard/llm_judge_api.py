"""Official Responses SDK, explicit caps, durable bodies and bounded retries."""

import fcntl
import json
import math
import os
import re
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .llm_judge import MODEL, VERSION, sha
from .review_client import append

PRICING = {
    "model": MODEL, "input_per_million": 10.0, "output_per_million": 50.0,
    "cached_input_per_million": 1.0, "cache_write_per_million": 12.5,
    "source": "https://developers.openai.com/api/docs/models/gpt-6-astra",
    "verified_date": "2026-11-09", "mode": "Standard, short context; not an invoice or verified proxy surcharge",
}


def sdk_client():
    from openai import OpenAI

    # The SDK reads OPENAI_API_KEY / OPENAI_BASE_URL. Never put a key in prompts,
    # files or logs. Disable SDK retries: all retry attempts are accounted here.
    return OpenAI(max_retries=0, timeout=180)


def availability(client):
    result = {"requested_model": MODEL, "checked_utc": datetime.now(timezone.utc).isoformat(),
              "endpoint_host": urlsplit(str(getattr(client, "base_url", ""))).hostname,
              "paid_inference_calls": 0}
    try:
        model = client.models.retrieve(MODEL)
        result.update(status="AVAILABLE" if model.id == MODEL else "MODEL_MISMATCH", returned_model_id=model.id)
    except Exception as error:
        result.update(status="UNVERIFIED", error_type=type(error).__name__,
                      http_status=getattr(error, "status_code", None),
                      explanation="Metadata access failed at the configured endpoint; this does not prove global model unavailability. A capped Responses smoke test must verify model/schema before any full batch.")
    return result


def model_matches(model):
    return isinstance(model, str) and re.fullmatch(r"gpt-6-astra(?:-\d{4}-\d{2}-\d{2})?", model) is not None


def request_cost_bound(messages, schema, max_output_tokens):
    size = len(json.dumps({"input": messages, "schema": schema}).encode()) + 1024
    if size > 272000:
        raise ValueError("request_exceeds_short_context_cost_envelope")
    return (size * PRICING["cache_write_per_million"] + max_output_tokens * PRICING["output_per_million"]) / 1e6


class JudgeAPI:
    def __init__(self, root, cap_usd, aggregate_cap_usd=None, client=None,
                 max_output_tokens=8192, max_attempts=3, sleeper=time.sleep):
        if cap_usd is None or not math.isfinite(cap_usd) or cap_usd <= 0:
            raise ValueError("explicit_positive_judge_spending_cap_required")
        if not 1 <= max_attempts <= 3 or not 1 <= max_output_tokens <= 128000:
            raise ValueError("invalid_retry_or_output_bound")
        prior = json.loads((root / "results/BUDGET_AUTHORIZATION.json").read_text())["authorized_total_usd"]
        aggregate = prior if aggregate_cap_usd is None else aggregate_cap_usd
        if not math.isfinite(aggregate) or aggregate < prior or cap_usd > aggregate:
            raise ValueError("invalid_aggregate_or_project_cap")
        self.root, self.cap, self.aggregate = root, cap_usd, aggregate
        self.client = client if client is not None else sdk_client()
        self.max_output, self.attempts, self.sleep = max_output_tokens, max_attempts, sleeper
        self.folder = root / "results/llm_judge"
        self.folder.mkdir(parents=True, exist_ok=True)
        append(self.folder / "authorizations.jsonl", {
            "judge_project_total_cap_usd": cap_usd, "aggregate_total_cap_usd": aggregate,
            "source": "Explicit CLI allocation; not per request, not a reset of prior accounting",
            "recorded_utc": datetime.now(timezone.utc).isoformat(),
        })

    def reserve(self, messages, schema, request_key):
        reserve = request_cost_bound(messages, schema, self.max_output)
        request_id = str(uuid.uuid4())
        original = self.root / "results/api_ledger.jsonl"
        shared = self.root / "results/review_v3/ledger.jsonl"
        # Same lock ordering and authoritative shared ledger as existing collectors.
        # Original evidence is read-only; shared log only receives appended events.
        with original.open() as old, shared.open("a+") as new:
            fcntl.flock(old, fcntl.LOCK_EX)
            fcntl.flock(new, fcntl.LOCK_EX)
            old_cost = math.fsum(json.loads(x)["reserved_usd"] for x in old)
            new.seek(0)
            rows = [json.loads(x) for x in new]
            total = old_cost + math.fsum(r["reserved_usd"] for r in rows)
            project = math.fsum(r["reserved_usd"] for r in rows if r.get("stage") == "llm-judge")
            if total + reserve > self.aggregate or project + reserve > self.cap:
                raise RuntimeError("judge_or_aggregate_budget_cap_reached")
            row = {"stage": "llm-judge", "request_id": request_id, "request_key": request_key,
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
                response = self.client.responses.create(
                    model=MODEL, reasoning={"effort": "high"}, input=messages,
                    text={"format": {"type": "json_schema", "name": "multilingual_validation", "strict": True, "schema": schema}},
                    max_output_tokens=self.max_output, store=False, service_tier="default",
                    metadata={"protocol": VERSION, "request_key": request_key[:128]},
                )
            except Exception as error:
                status = getattr(error, "status_code", None)
                retryable = status in (408, 409, 429) or (status is not None and status >= 500) or type(error).__name__ in ("APIConnectionError", "APITimeoutError")
                append(self.folder / "errors.jsonl", {"request_key": request_key, "request_id": request_id,
                                                       "attempt": attempt, "error_type": type(error).__name__,
                                                       "http_status": status, "retryable": retryable,
                                                       "messages_sha256": sha(messages),
                                                       "billing": "Unknown, full reservation retained"})
                if not retryable or attempt + 1 == self.attempts:
                    raise RuntimeError("judge_request_failed_" + type(error).__name__) from None
                self.sleep(min(30, 2 ** attempt))
                continue
            raw = response.model_dump(mode="json")
            record = {"request_key": request_key, "request_id": request_id,
                      "timestamp_utc": datetime.now(timezone.utc).isoformat(), "attempt": attempt,
                      "requested_model": MODEL, "reasoning_effort": "high", "max_output_tokens": self.max_output,
                      "messages": messages, "messages_sha256": sha(messages), "raw_response": raw}
            # Save before model/schema/status validation; invalid or unexpected
            # responses remain evidence and never trigger outcome-based retries.
            append(self.folder / "raw_responses.jsonl", record)
            usage = raw.get("usage") or {}
            if (type(usage.get("input_tokens")) is int and type(usage.get("output_tokens")) is int
                    and usage["input_tokens"] >= 0 and usage["output_tokens"] >= 0):
                accounted = (usage["input_tokens"] * PRICING["cache_write_per_million"]
                             + usage["output_tokens"] * PRICING["output_per_million"]) / 1e6
                uncached = (usage["input_tokens"] * PRICING["input_per_million"]
                            + usage["output_tokens"] * PRICING["output_per_million"]) / 1e6
                correction = {"stage": "llm-judge", "request_id": request_id, "request_key": request_key,
                              "reserved_usd": accounted - reserve, "accounted_usd": accounted,
                              "uncached_standard_estimate_usd": uncached, "response_id": raw.get("id"),
                              "usage": usage, "basis": "Conservative standard cache-write input bound; not invoice"}
                append(self.root / "results/review_v3/ledger.jsonl", correction)
                append(self.folder / "cost_ledger.jsonl", correction)
            if not model_matches(raw.get("model")) or (expected_model and raw.get("model") != expected_model):
                raise RuntimeError("judge_returned_model_mismatch_saved_for_audit")
            if not isinstance(raw.get("id"), str) or not raw["id"]:
                raise RuntimeError("judge_response_id_missing_saved_for_audit")
            if raw.get("status") != "completed":
                raise RuntimeError("judge_incomplete_response_saved_for_audit")
            return record, response.output_text
        raise RuntimeError("judge_retry_limit")
