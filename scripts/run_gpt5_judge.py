"""Versioned Braintrust GPT-5 multilingual judge. Default: offline dry-run."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from run_llm_judge import revision_messages

from ai2ai_guard.gpt5_judge_api import (
    FOLDER,
    MODEL,
    PRICING,
    VERSION,
    GPT5JudgeAPI,
    request_cost_bound,
)
from ai2ai_guard.llm_judge import (
    ASSESSMENT_SCHEMA,
    REVISION_SCHEMA,
    aggregate,
    extract_groups,
    request_messages,
    sha,
    validate_assessment,
    validate_revision,
)
from ai2ai_guard.llm_judge import VERSION as RUBRIC_VERSION
from ai2ai_guard.review_client import append

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def prepare(root=ROOT):
    groups, files = extract_groups(root)
    folder = root / FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    corpus = "".join(json.dumps(g, ensure_ascii=False) + "\n" for g in groups)
    sources = {name: sha((root / name).read_bytes()) for name in (
        "scripts/run_gpt5_judge.py", "src/ai2ai_guard/gpt5_judge_api.py",
        "src/ai2ai_guard/llm_judge.py", "scripts/run_llm_judge.py")}
    protocol = {"version": VERSION, "model": MODEL, "transport": "braintrust-chat-completions",
                "rubric_version": RUBRIC_VERSION,
                "rubric_note": "Legacy rubric identifier retained for identical schemas; it does not identify the judge model",
                "reasoning_effort": "high", "max_output_tokens": 8192, "repeats": 3,
                "max_transport_attempts": 3, "source_files_sha256": files,
                "source_sha256": sources, "corpus_sha256": sha(corpus.encode()), "pricing": PRICING,
                "historical_data_changed": False, "english_is_gold_standard": False,
                "previous_judge_responses_shared": False,
                "limitations": "Same model family as workers; repeated judgments share biases. LLM-based, not human validation. Smoke is not corpus validation."}
    for name, text in (("aligned_prompts.jsonl", corpus), ("PROTOCOL.json", json.dumps(protocol, indent=2) + "\n")):
        path = folder / name
        if path.exists() and path.read_text() != text:
            raise ValueError("frozen_gpt5_judge_profile_changed_use_new_version")
        if not path.exists():
            path.write_text(text)
    bounds = [request_cost_bound(request_messages(g, 0), ASSESSMENT_SCHEMA) for g in groups]
    estimate = {"aligned_groups": len(groups), "initial_judge_requests": len(groups) * 3,
                "initial_no_retry_conservative_ceiling_usd": round(sum(bounds) * 3, 6),
                "initial_max_retry_conservative_ceiling_usd": round(sum(bounds) * 9, 6),
                "initial_planning_estimate_usd": round(sum(b - .08192 + .04096 for b in bounds) * 3, 6),
                "planning_output_tokens_per_call_not_observed": 4096, "pricing": PRICING,
                "scope": "All 1920 aligned groups; no template deduplication; revisions cost extra"}
    (folder / "cost_estimate.json").write_text(json.dumps(estimate, indent=2) + "\n")
    return groups, estimate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--smoke", action="store_true")
    stage.add_argument("--run", action="store_true")
    stage.add_argument("--revisions", action="store_true")
    parser.add_argument("--cap-usd", type=float, help="Cumulative GPT-5 judge allocation; shared authorization still applies")
    args = parser.parse_args()
    groups, estimate = prepare()
    print(json.dumps(estimate, indent=2), flush=True)
    folder = ROOT / FOLDER
    if not any((args.smoke, args.run, args.revisions)):
        return
    if args.cap_usd is None:
        parser.error("--cap-usd required before paid requests")
    smoke = folder / "SMOKE_COMPLETE.json"
    protocol_hash = sha((folder / "PROTOCOL.json").read_bytes())
    if not args.smoke and not smoke.exists():
        raise RuntimeError("valid_returned_model_and_schema_smoke_required")
    receipt = json.loads(smoke.read_text()) if smoke.exists() else None
    if receipt and receipt["protocol_sha256"] != protocol_hash:
        raise ValueError("smoke_protocol_mismatch")
    api = GPT5JudgeAPI(ROOT, args.cap_usd)
    saved = read(folder / "judgments.jsonl")

    def assess(group, repeat, replacement=None):
        phase = "revised" if replacement else "original"
        key = f"{phase}:{group['group_id']}:{repeat}"
        path = folder / ("revised_judgments.jsonl" if replacement else "judgments.jsonl")
        prior = [r for r in read(path) if r["request_key"] == key]
        if len(prior) > 1:
            raise ValueError("duplicate_judge_request")
        if prior:
            return prior[0]
        messages = request_messages(group, repeat, replacement)
        raw, text = api.create(messages, ASSESSMENT_SCHEMA, key, receipt["returned_model"] if receipt else None)
        row = {"request_key": key, "group_id": group["group_id"], "repeat": repeat, "phase": phase,
               "language_order": [p["language"] for p in json.loads(messages[1]["content"])["prompts_in_randomized_order"]],
               "source_group_sha256": group["source_group_sha256"], "response_id": raw["raw_response"]["id"],
               "returned_model": raw["raw_response"]["model"], "timestamp_utc": raw["timestamp_utc"], "status": "INVALID"}
        try:
            row.update(assessment=validate_assessment(text, group, replacement), status="VALID")
        except (ValueError, TypeError) as error:
            row["instrument_error"] = str(error)
        append(path, row)
        return row

    if args.smoke:
        rows = [assess(groups[0], i) for i in range(3)]
        if aggregate(groups[0], rows)["valid_judgments"] != 3 or len({r["returned_model"] for r in rows}) != 1:
            raise RuntimeError("smoke_schema_or_model_check_failed_no_full_batch")
        smoke.write_text(json.dumps({"group_id": groups[0]["group_id"], "returned_model": rows[0]["returned_model"],
                                     "valid_structured_responses": 3, "protocol_sha256": protocol_hash,
                                     "response_ids": [r["response_id"] for r in rows]}, indent=2) + "\n")
    elif args.run:
        for group in groups:
            for i in range(3):
                assess(group, i)
    else:
        drafts = {r["group_id"]: r for r in read(folder / "revision_drafts.jsonl")}
        for group in groups:
            rows = [r for r in saved if r["group_id"] == group["group_id"]]
            if aggregate(group, rows)["outcome"] not in ("FAIL", "REVIEW_REQUIRED"):
                continue
            if group["group_id"] not in drafts:
                raw, text = api.create(revision_messages(group, rows), REVISION_SCHEMA,
                                       "draft:" + group["group_id"], receipt["returned_model"])
                draft = {"group_id": group["group_id"], "response_id": raw["raw_response"]["id"],
                         "version": VERSION + "-suggested-revision-1", "draft": validate_revision(text, group),
                         "historical_prompts_replaced": False}
                append(folder / "revision_drafts.jsonl", draft)
                drafts[group["group_id"]] = draft
            replacement = {p["language"]: p["suggested_text"] for p in drafts[group["group_id"]]["draft"]["proposals"]}
            for i in range(3):
                assess(group, i, replacement)
    (folder / "execution_status.json").write_text(json.dumps({
        "status": "SMOKE_COMPLETE_CORPUS_PENDING" if args.smoke else "STAGE_COMPLETE",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        folder = ROOT / FOLDER
        if folder.exists():
            (folder / "execution_status.json").write_text(json.dumps({
                "status": "BLOCKED_OR_INTERRUPTED", "error_type": type(error).__name__,
                "reason": str(error) if isinstance(error, (ValueError, RuntimeError)) else "execution_error"}, indent=2) + "\n")
        raise
