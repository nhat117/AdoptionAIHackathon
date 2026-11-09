"""Prospective v2: larger reasoning envelope and source-constrained excerpts."""

import copy
import fcntl
import json
import math
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .gpt5_judge_api import MODEL, PRICING, model_matches, response_text
from .gpt5_judge_batch import AUTHORIZATION, append_sharded
from .llm_judge import ASSESSMENT_SCHEMA, REVISION_SCHEMA, request_messages, sha
from .review_client import append

VERSION = "braintrust-gpt5-multilingual-v2-16k-exact-fields"
FOLDER = "results/llm_judge_gpt5_v2"
STAGE = "llm-judge-gpt5-v2"
MAX_OUTPUT = 16384
QUOTE_INSTRUCTION = (
    " Evidence quoting rule for this instrument version: for every excerpt select an EXACT COMPLETE "
    "source field from the response schema's text enum (peer_message, system content or user JSON). "
    "Do not shorten, retype, normalize whitespace, translate, or paraphrase the quote. "
    "Use the corresponding language and scope. Whole-field quotes are deliberate instrument constraints, "
    "not evidence that every part of the quoted field is defective. Explain the specific concern separately."
)


def assessment_messages(group, repeat, revision=None):
    messages = request_messages(group, repeat, revision)
    messages[0]["content"] += QUOTE_INSTRUCTION
    return messages


def constrained_schema(group, revision=None, drafting=False):
    messages = request_messages(group, 0, revision)
    texts = set()
    for prompt in json.loads(messages[1]["content"])["prompts_in_randomized_order"]:
        texts.update((prompt["peer_message"], prompt["messages"][0]["content"], prompt["messages"][1]["content"]))
    schema = copy.deepcopy(REVISION_SCHEMA if drafting else ASSESSMENT_SCHEMA)

    def constrain(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and set(node.get("properties", {})) == {"language", "scope", "text"}:
                node["properties"]["text"] = {"type": "string", "enum": sorted(texts)}
            for value in node.values():
                constrain(value)
        elif isinstance(node, list):
            for value in node:
                constrain(value)

    constrain(schema)
    return schema


def cost_bound(messages, schema):
    size = len(json.dumps({"messages": messages, "schema": schema}).encode()) + 1024
    if size > 272000:
        raise ValueError("request_exceeds_short_context_cost_envelope")
    return (size * 1.25 + MAX_OUTPUT * 10) / 1e6


class JudgeV2:
    def __init__(self, root, cap_usd, client=None, sleeper=time.sleep):
        approved = json.loads((root / AUTHORIZATION).read_text())["authorized_total_usd"]
        if approved != 650 or not math.isfinite(cap_usd) or not 0 < cap_usd <= approved:
            raise ValueError("cap_must_fit_recorded_650_total_authorization")
        if client is None:
            from openai import OpenAI

            client = OpenAI(max_retries=0, timeout=300,
                            default_headers={"Cache-Control": "no-store", "x-bt-use-cache": "never"})
        if urlsplit(str(client.base_url)).hostname != "api.braintrust.dev":
            raise ValueError("braintrust_endpoint_required")
        self.root, self.cap, self.aggregate, self.client = root, cap_usd, approved, client
        self.folder, self.lock, self.sleep = root / FOLDER, threading.Lock(), sleeper
        append(self.folder / "authorizations.jsonl", {
            "judge_project_total_cap_usd": cap_usd, "aggregate_total_cap_usd": approved,
            "authorization_file": AUTHORIZATION, "authorization_sha256": sha((root / AUTHORIZATION).read_bytes()),
            "recorded_utc": datetime.now(timezone.utc).isoformat(),
            "source": "Explicit cumulative US$650 research approval; v1 costs retained"})

    def reserve(self, messages, schema, key):
        bound, request_id = cost_bound(messages, schema), str(uuid.uuid4())
        with (self.root / "results/api_ledger.jsonl").open() as old, (self.root / "results/review_v3/ledger.jsonl").open("a+") as new:
            fcntl.flock(old, fcntl.LOCK_EX)
            fcntl.flock(new, fcntl.LOCK_EX)
            total = math.fsum(json.loads(x)["reserved_usd"] for x in old)
            new.seek(0)
            rows = [json.loads(x) for x in new]
            total += math.fsum(r["reserved_usd"] for r in rows)
            project = math.fsum(r["reserved_usd"] for r in rows if r.get("stage") == STAGE)
            if total + bound > self.aggregate or project + bound > self.cap:
                raise RuntimeError("judge_or_aggregate_budget_cap_reached")
            row = {"stage": STAGE, "request_id": request_id, "request_key": key,
                   "model": MODEL, "reserved_usd": bound, "time": time.time()}
            new.write(json.dumps(row) + "\n")
            new.flush()
            os.fsync(new.fileno())
        append(self.folder / "cost_ledger.jsonl", row)
        return request_id, bound

    def create(self, messages, schema, key):
        for attempt in range(3):
            request_id, bound = self.reserve(messages, schema, key)
            try:
                response = self.client.chat.completions.create(
                    model=MODEL, messages=messages, reasoning_effort="high", max_completion_tokens=MAX_OUTPUT,
                    store=False, response_format={"type": "json_schema", "json_schema": {
                        "name": "multilingual_validation", "strict": True, "schema": schema}})
            except Exception as error:
                status = getattr(error, "status_code", None)
                retryable = status in (408, 409, 429) or (status is not None and status >= 500) or type(error).__name__ in ("APIConnectionError", "APITimeoutError")
                append(self.folder / "errors.jsonl", {
                    "request_key": key, "request_id": request_id, "attempt": attempt,
                    "error_type": type(error).__name__, "http_status": status, "retryable": retryable,
                    "messages_sha256": sha(messages), "billing": "Unknown, full reservation retained"})
                if not retryable or attempt == 2:
                    raise RuntimeError("judge_request_failed_" + type(error).__name__) from None
                self.sleep(min(30, 2 ** attempt))
                continue
            raw = response.model_dump(mode="json")
            record = {"request_key": key, "request_id": request_id, "attempt": attempt,
                      "timestamp_utc": datetime.now(timezone.utc).isoformat(), "profile": VERSION,
                      "requested_model": MODEL, "reasoning_effort": "high", "max_output_tokens": MAX_OUTPUT,
                      "messages": messages, "messages_sha256": sha(messages),
                      "schema_sha256": sha(schema), "raw_response": raw}
            append_sharded(self.folder / "raw_responses.jsonl", record, self.lock)
            usage = raw.get("usage") or {}
            if all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("prompt_tokens", "completion_tokens")):
                actual = (usage["prompt_tokens"] * 1.25 + usage["completion_tokens"] * 10) / 1e6
                correction = {"stage": STAGE, "request_id": request_id, "request_key": key,
                              "reserved_usd": actual - bound, "accounted_usd": actual,
                              "response_id": raw.get("id"), "usage": usage, "basis": PRICING["mode"]}
                append(self.root / "results/review_v3/ledger.jsonl", correction)
                append(self.folder / "cost_ledger.jsonl", correction)
            if not model_matches(raw.get("model")):
                raise RuntimeError("judge_model_mismatch_saved_for_audit")
            if not isinstance(raw.get("id"), str) or not raw["id"]:
                raise RuntimeError("judge_response_id_missing_saved_for_audit")
            return record, response_text(raw)
        raise RuntimeError("judge_retry_limit")
