"""Versioned 16k/exact-field GPT-5 judge: dry-run, smoke, full and revisions."""

import argparse
import fcntl
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from run_llm_judge import revision_messages

from ai2ai_guard.gpt5_judge_api import MODEL, PRICING, RETURNED_MODEL
from ai2ai_guard.gpt5_judge_batch import AUTHORIZATION, append_sharded, read_records
from ai2ai_guard.gpt5_judge_v2 import (
    FOLDER,
    MAX_OUTPUT,
    QUOTE_INSTRUCTION,
    VERSION,
    JudgeV2,
    assessment_messages,
    constrained_schema,
    cost_bound,
)
from ai2ai_guard.llm_judge import (
    aggregate,
    extract_groups,
    sha,
    validate_assessment,
    validate_revision,
)

ROOT = Path(__file__).resolve().parents[1]


def prepare(root=ROOT):
    groups, files = extract_groups(root)
    folder = root / FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    corpus = "".join(json.dumps(g, ensure_ascii=False) + "\n" for g in groups)
    source_names = ("src/ai2ai_guard/gpt5_judge_v2.py", "scripts/run_gpt5_judge_v2.py",
                    "src/ai2ai_guard/llm_judge.py", "src/ai2ai_guard/gpt5_judge_batch.py",
                    "src/ai2ai_guard/gpt5_judge_api.py", "scripts/run_llm_judge.py", AUTHORIZATION)
    protocol = {"version": VERSION, "model": MODEL, "reasoning_effort": "high", "max_output_tokens": MAX_OUTPUT,
                "repeats": 3, "workers": 8, "pricing": PRICING, "source_files_sha256": files,
                "source_sha256": {name: sha((root / name).read_bytes()) for name in source_names},
                "corpus_sha256": sha(corpus.encode()), "aggregate_cap_usd": 650,
                "transport": "braintrust-chat-completions", "schema_version": "exact-complete-source-fields-v1",
                "quote_instruction": QUOTE_INSTRUCTION, "historical_data_changed": False,
                "prior_profile": "results/llm_judge_gpt5", "prior_ratings_reused": False,
                "rationale": "v1 observed an 8192-token reasoning-only truncation and two non-exact quote errors; v2 restarts all groups, not selective quality rescoring",
                "limitations": "Same worker/judge model family; repeated judgments share biases. LLM-based, not human validation. No source-language gold standard."}
    for name, text in (("PROTOCOL.json", json.dumps(protocol, indent=2) + "\n"), ("aligned_prompts.jsonl", corpus)):
        path = folder / name
        if path.exists() and path.read_text() != text:
            raise ValueError("frozen_v2_instrument_changed_use_new_version")
        if not path.exists():
            path.write_text(text)
    bounds = [cost_bound(assessment_messages(g, 0), constrained_schema(g)) for g in groups]
    estimate = {"aligned_groups": len(groups), "initial_judge_requests": len(groups) * 3,
                "initial_no_retry_conservative_ceiling_usd": round(sum(bounds) * 3, 6),
                "initial_max_retry_conservative_ceiling_usd": round(sum(bounds) * 9, 6),
                "initial_planning_estimate_usd": round(sum(b - .16384 + .08 for b in bounds) * 3, 6),
                "planning_output_tokens_per_call_not_observed": 8000, "pricing": PRICING,
                "scope": "All 1920 groups rerun; v1 responses excluded. Bounded by US$650 aggregate even if full worst-case/revisions exceed the cap."}
    (folder / "cost_estimate.json").write_text(json.dumps(estimate, indent=2) + "\n")
    return groups, estimate


def execute(root, groups, cap, smoke=False, revisions=False):
    folder = root / FOLDER
    protocol_hash = sha((folder / "PROTOCOL.json").read_bytes())
    smoke_path = folder / "SMOKE_COMPLETE.json"
    if not smoke:
        receipt = json.loads(smoke_path.read_text())
        if receipt["protocol_sha256"] != protocol_hash or receipt["returned_model"] != RETURNED_MODEL:
            raise ValueError("valid_v2_smoke_required")
    api = JudgeV2(root, cap)
    lock, stop = threading.Lock(), threading.Event()
    raw = read_records(folder / "raw_responses.jsonl")
    raw_by_key = {r["request_key"]: r for r in raw}
    saved = read_records(folder / "judgments.jsonl") + read_records(folder / "revised_judgments.jsonl")
    keys = {r["request_key"] for r in saved}
    if len(keys) != len(saved) or len(raw_by_key) != len(raw):
        raise ValueError("duplicate_saved_v2_requests")

    def create(messages, schema, key):
        if key in raw_by_key:
            from ai2ai_guard.gpt5_judge_api import response_text

            previous = raw_by_key[key]
            if previous["messages"] != messages or previous["schema_sha256"] != sha(schema):
                raise ValueError("saved_v2_request_mismatch")
            if previous["raw_response"].get("model") != RETURNED_MODEL:
                raise ValueError("saved_v2_model_mismatch")
            return previous, response_text(previous["raw_response"])
        return api.create(messages, schema, key)

    def assess(group, repeat, replacement=None):
        if stop.is_set():
            return
        phase = "revised" if replacement else "original"
        key = f"{phase}:{group['group_id']}:{repeat}"
        if key in keys:
            return
        try:
            messages = assessment_messages(group, repeat, replacement)
            record, text = create(messages, constrained_schema(group, replacement), key)
            row = {"request_key": key, "group_id": group["group_id"], "repeat": repeat, "phase": phase,
                   "language_order": [p["language"] for p in json.loads(messages[1]["content"])["prompts_in_randomized_order"]],
                   "source_group_sha256": group["source_group_sha256"], "response_id": record["raw_response"]["id"],
                   "returned_model": record["raw_response"]["model"], "timestamp_utc": record["timestamp_utc"], "status": "INVALID"}
            try:
                from ai2ai_guard.llm_judge import schema_validate

                schema_validate(json.loads(text), constrained_schema(group, replacement))
                row.update(assessment=validate_assessment(text, group, replacement), status="VALID")
            except (ValueError, TypeError) as error:
                row["instrument_error"] = str(error)
            append_sharded(folder / ("revised_judgments.jsonl" if replacement else "judgments.jsonl"), row, lock)
            with lock:
                saved.append(row)
                keys.add(key)
                if len(saved) % 30 == 0:
                    print(json.dumps({"saved": len(saved), "valid": sum(r["status"] == "VALID" for r in saved)}), flush=True)
        except Exception:
            stop.set()
            raise

    if smoke:
        for repeat in range(3):
            assess(groups[0], repeat)
        rows = [r for r in saved if r["group_id"] == groups[0]["group_id"] and r["phase"] == "original"]
        if aggregate(groups[0], rows)["valid_judgments"] != 3 or {r["returned_model"] for r in rows} != {RETURNED_MODEL}:
            raise RuntimeError("v2_smoke_instrument_check_failed")
        smoke_path.write_text(json.dumps({"group_id": groups[0]["group_id"], "returned_model": RETURNED_MODEL,
                                          "protocol_sha256": protocol_hash, "valid_structured_responses": 3,
                                          "response_ids": [r["response_id"] for r in rows]}, indent=2) + "\n")
    elif revisions:
        drafts = {r["group_id"]: r for r in read_records(folder / "revision_drafts.jsonl")}

        def revise(group):
            if stop.is_set():
                return
            rows = [r for r in saved if r["group_id"] == group["group_id"] and r["phase"] == "original"]
            if aggregate(group, rows)["outcome"] not in ("FAIL", "REVIEW_REQUIRED"):
                return
            try:
                draft = drafts.get(group["group_id"])
                if not draft:
                    messages = revision_messages(group, rows)
                    messages[0]["content"] += QUOTE_INSTRUCTION
                    record, text = create(messages, constrained_schema(group, drafting=True), "draft:" + group["group_id"])
                    draft = {"group_id": group["group_id"], "response_id": record["raw_response"]["id"],
                             "version": VERSION + "-suggested-revision-1", "draft": validate_revision(text, group),
                             "historical_prompts_replaced": False}
                    append_sharded(folder / "revision_drafts.jsonl", draft, lock)
                replacement = {p["language"]: p["suggested_text"] for p in draft["draft"]["proposals"]}
                for repeat in range(3):
                    assess(group, repeat, replacement)
            except Exception:
                stop.set()
                raise

        with ThreadPoolExecutor(max_workers=8) as pool:
            for future in as_completed([pool.submit(revise, g) for g in groups]):
                future.result()
    else:
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(assess, g, i) for g in groups for i in range(3) if f"original:{g['group_id']}:{i}" not in keys]
            for future in as_completed(futures):
                future.result()
    original = [r for r in saved if r["phase"] == "original"]
    return {"saved_initial_records": len(original), "valid_initial_judgments": sum(r["status"] == "VALID" for r in original)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    stages = parser.add_mutually_exclusive_group()
    for name in ("smoke", "run", "revisions"):
        stages.add_argument("--" + name, action="store_true")
    parser.add_argument("--cap-usd", type=float)
    args = parser.parse_args()
    groups, estimate = prepare()
    if not any((args.smoke, args.run, args.revisions)):
        print(json.dumps(dict(estimate, paid_calls=0)), flush=True)
        return
    if args.cap_usd is None:
        parser.error("Explicit --cap-usd required")
    folder = ROOT / FOLDER
    status = folder / "execution_status.json"
    with (folder / "execution.lock").open("a") as execution_lock:
        fcntl.flock(execution_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status.write_text(json.dumps({"status": "RUNNING_SMOKE" if args.smoke else "RUNNING_REVISIONS" if args.revisions else "RUNNING_FULL_INITIAL",
                                      "started_utc": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
        try:
            result = execute(ROOT, groups, args.cap_usd, args.smoke, args.revisions)
            result["status"] = ("SMOKE_COMPLETE_CORPUS_PENDING" if args.smoke else "REVISIONS_STAGE_FINISHED" if args.revisions
                                else "INITIAL_COMPLETE" if result["valid_initial_judgments"] == 5760 else "INITIAL_REQUESTS_FINISHED_WITH_INSTRUMENT_FAILURES")
            status.write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps(result), flush=True)
        except Exception as error:
            status.write_text(json.dumps({"status": "BLOCKED_OR_INTERRUPTED", "error_type": type(error).__name__,
                                          "reason": str(error) if isinstance(error, (ValueError, RuntimeError)) else "execution_error"}, indent=2) + "\n")
            raise


if __name__ == "__main__":
    main()
