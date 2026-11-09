"""Durable, budget-limited API client for post-review studies only."""

import fcntl
import hashlib
import json
import math
import os
import time
import uuid
from pathlib import Path

import httpx


def append(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def ledger_total(path):
    return math.fsum(json.loads(x)["reserved_usd"] for x in path.read_text().splitlines()) if path.exists() else 0


class ReviewClient:
    def __init__(self, root, cap=20, stage="unspecified", transport=None):
        self.root, self.stage = Path(root), stage
        authorization = json.loads((self.root / "results/BUDGET_AUTHORIZATION.json").read_text())
        if not 0 <= cap <= authorization["authorized_total_usd"]:
            raise ValueError("cap_exceeds_recorded_authorization")
        self.cap = cap
        self.folder = self.root / "results/review_v3"
        self.folder.mkdir(parents=True, exist_ok=True)
        self.http = httpx.Client(timeout=90, transport=transport)

    def chat(self, messages, seed=None):
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("configured_api_key_missing")
        reserve = (len(json.dumps(messages).encode()) * 1.25 + 512 * 10) / 1e6
        request_id = str(uuid.uuid4())
        original = self.root / "results/api_ledger.jsonl"
        ledger = self.folder / "ledger.jsonl"
        # Lock both ledgers. Original collectors lock the first; review collectors
        # lock both in this order. The original ledger is read-only, never copied/reset.
        with original.open("r") as old, ledger.open("a+") as new:
            fcntl.flock(old, fcntl.LOCK_EX)
            fcntl.flock(new, fcntl.LOCK_EX)
            old_total = math.fsum(json.loads(x)["reserved_usd"] for x in old)
            new.seek(0)
            new_total = math.fsum(json.loads(x)["reserved_usd"] for x in new)
            if old_total + new_total + reserve > self.cap:
                raise RuntimeError("aggregate_budget_cap_reached")
            new.write(json.dumps({"request_id": request_id, "stage": self.stage,
                                  "reserved_usd": reserve, "time": time.time()}) + "\n")
            new.flush()
            os.fsync(new.fileno())
        response = self.http.post(
            os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/") + "/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                     "Cache-Control": "no-store", "x-bt-use-cache": "never"},
            json={"model": "gpt-5", "messages": messages,
                  "reasoning_effort": "minimal", "max_completion_tokens": 512},
        )
        if response.status_code != 200:
            raise RuntimeError("provider_http_" + str(response.status_code))
        value = response.json()
        # Preserve returned bytes/body before parsing/scoring; never lose a billed body.
        append(self.folder / "api_responses.jsonl", {
            "request_id": request_id, "stage": self.stage, "time": time.time(),
            "messages": messages, "response": value,
            "requested_model": "gpt-5", "reasoning_effort": "minimal", "max_completion_tokens": 512,
            "prompt_sha256": hashlib.sha256(json.dumps(messages, ensure_ascii=False).encode()).hexdigest(),
        })
        usage = value.get("usage", {})
        if {"prompt_tokens", "completion_tokens"} <= set(usage):
            actual = (usage["prompt_tokens"] * 1.25 + usage["completion_tokens"] * 10) / 1e6
            append(ledger, {"request_id": request_id, "stage": self.stage,
                            "reserved_usd": actual - reserve, "actual_usd": actual,
                            "response_id": value["id"]})
        return {"content": value["choices"][0]["message"]["content"], "model": value["model"],
                "response_id": value["id"], "usage": usage, "created": value.get("created"),
                "request_id": request_id, "reasoning_effort_requested": "minimal",
                "max_output_tokens_requested": 512, "temperature_requested": None}
