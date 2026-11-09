"""Full Braintrust judge run under the user-approved cumulative US$650 cap."""

import argparse
import fcntl
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from run_gpt5_judge import prepare
from run_llm_judge import revision_messages

from ai2ai_guard.gpt5_judge_api import FOLDER, VERSION
from ai2ai_guard.gpt5_judge_batch import (
    AUTHORIZATION,
    EXECUTION_VERSION,
    FullJudgeAPI,
    append_sharded,
    read_records,
)
from ai2ai_guard.llm_judge import (
    ASSESSMENT_SCHEMA,
    REVISION_SCHEMA,
    aggregate,
    request_messages,
    sha,
    validate_assessment,
    validate_revision,
)
from ai2ai_guard.review_client import ledger_total

ROOT = Path(__file__).resolve().parents[1]


def prepare_execution(root, workers):
    groups, estimate = prepare(root)
    folder = root / FOLDER
    source_names = ("scripts/run_full_gpt5_judge.py", "src/ai2ai_guard/gpt5_judge_batch.py", AUTHORIZATION)
    protocol = {"version": EXECUTION_VERSION, "instrument_protocol_sha256": sha((folder / "PROTOCOL.json").read_bytes()),
                "source_sha256": {name: sha((root / name).read_bytes()) for name in source_names},
                "workers": workers, "aggregate_cap_usd": 650,
                "scheduling": "Fixed corpus order; up to eight remote requests; no result-based exclusions/replacements",
                "storage": "Append-only 8 MiB JSONL shards; unsharded smoke evidence retained",
                "same_instrument": "Unchanged GPT-5 model, rubric, prompts, high reasoning, strict schema and 8192 output limit",
                "recovery": "Recovered complete raw answers are validated without another paid call; incomplete/model-mismatched answers stop for review"}
    path = folder / "FULL_EXECUTION_PROTOCOL.json"
    text = json.dumps(protocol, indent=2) + "\n"
    if path.exists() and path.read_text() != text:
        raise ValueError("frozen_full_execution_changed_create_a_new_version")
    if not path.exists():
        path.write_text(text)
    return groups, estimate, sha(path.read_bytes())


def run(root, workers, cap, revisions=False):
    groups, _, execution_hash = prepare_execution(root, workers)
    folder = root / FOLDER
    receipt = json.loads((folder / "SMOKE_COMPLETE.json").read_text())
    if receipt["protocol_sha256"] != sha((folder / "PROTOCOL.json").read_bytes()) or receipt["valid_structured_responses"] != 3:
        raise ValueError("valid_smoke_required")
    api = FullJudgeAPI(root, cap)
    api.execution_hash = execution_hash
    lock, stop = threading.Lock(), threading.Event()
    status_path = folder / "execution_status.json"
    raw = read_records(folder / "raw_responses.jsonl")
    raw_by_key = {}
    for record in raw:
        if record["request_key"] in raw_by_key:
            raise ValueError("duplicate_saved_raw_request_key_requires_review")
        raw_by_key[record["request_key"]] = record
    saved = read_records(folder / "judgments.jsonl") + read_records(folder / "revised_judgments.jsonl")
    saved_keys = {r["request_key"] for r in saved}
    if len(saved_keys) != len(saved):
        raise ValueError("duplicate_saved_judge_key")

    def create(messages, schema, key):
        previous = raw_by_key.get(key)
        if previous:
            from ai2ai_guard.gpt5_judge_api import model_matches, response_text

            if previous["messages"] != messages or not model_matches(previous["raw_response"].get("model")):
                raise RuntimeError("saved_raw_request_mismatch_requires_review")
            return previous, response_text(previous["raw_response"])
        return api.create(messages, schema, key, receipt["returned_model"])

    def assess(group, repeat, replacement=None):
        phase = "revised" if replacement else "original"
        key = f"{phase}:{group['group_id']}:{repeat}"
        if key in saved_keys or stop.is_set():
            return
        messages = request_messages(group, repeat, replacement)
        try:
            record, text = create(messages, ASSESSMENT_SCHEMA, key)
            row = {"request_key": key, "group_id": group["group_id"], "repeat": repeat, "phase": phase,
                   "language_order": [p["language"] for p in json.loads(messages[1]["content"])["prompts_in_randomized_order"]],
                   "source_group_sha256": group["source_group_sha256"], "response_id": record["raw_response"]["id"],
                   "returned_model": record["raw_response"]["model"], "timestamp_utc": record["timestamp_utc"], "status": "INVALID"}
            try:
                row.update(assessment=validate_assessment(text, group, replacement), status="VALID")
            except (ValueError, TypeError) as error:
                row["instrument_error"] = str(error)
            append_sharded(folder / ("revised_judgments.jsonl" if replacement else "judgments.jsonl"), row, lock)
            with lock:
                saved.append(row)
                saved_keys.add(key)
                if len(saved) % 30 == 0:
                    print(json.dumps({"saved_records": len(saved), "valid": sum(r["status"] == "VALID" for r in saved)}), flush=True)
        except Exception:
            stop.set()
            raise

    status_path.write_text(json.dumps({"status": "RUNNING_REVISIONS" if revisions else "RUNNING_FULL_INITIAL",
                                       "workers": workers, "aggregate_cap_usd": 650,
                                       "started_utc": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
    try:
        if revisions:
            drafts = {r["group_id"]: r for r in read_records(folder / "revision_drafts.jsonl")}

            def revise(group):
                if stop.is_set():
                    return
                rows = [r for r in saved if r["phase"] == "original" and r["group_id"] == group["group_id"]]
                if aggregate(group, rows)["outcome"] not in ("FAIL", "REVIEW_REQUIRED"):
                    return
                try:
                    draft = drafts.get(group["group_id"])
                    if draft is None:
                        record, text = create(revision_messages(group, rows), REVISION_SCHEMA, "draft:" + group["group_id"])
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

            tasks = [(revise, (group,)) for group in groups]
        else:
            tasks = [(assess, (group, repeat)) for group in groups for repeat in range(3)
                     if f"original:{group['group_id']}:{repeat}" not in saved_keys]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(function, *args) for function, args in tasks]
            for future in as_completed(futures):
                future.result()
        initial = [r for r in saved if r["phase"] == "original"]
        valid = sum(r["status"] == "VALID" for r in initial)
        status = "REVISIONS_STAGE_FINISHED" if revisions else "INITIAL_COMPLETE" if valid == 5760 else "INITIAL_REQUESTS_FINISHED_WITH_INSTRUMENT_FAILURES"
        result = {"status": status, "saved_initial_records": len(initial), "valid_initial_judgments": valid,
                  "aggregate_accounted_usd": round(ledger_total(root / "results/api_ledger.jsonl") + ledger_total(root / "results/review_v3/ledger.jsonl"), 8),
                  "finished_utc": datetime.now(timezone.utc).isoformat()}
        status_path.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result), flush=True)
    except Exception as error:
        status_path.write_text(json.dumps({"status": "BLOCKED_OR_INTERRUPTED", "error_type": type(error).__name__,
                                           "reason": str(error) if isinstance(error, (RuntimeError, ValueError)) else "execution_error",
                                           "saved_records": len(saved), "timestamp_utc": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Paid initial judging; absent by default")
    parser.add_argument("--revisions", action="store_true", help="Paid drafting/blinded reassessment of flagged groups")
    parser.add_argument("--cap-usd", type=float)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.workers <= 8 or (args.run and args.revisions):
        parser.error("Use 1-8 workers and one paid stage")
    if not args.run and not args.revisions:
        groups, estimate, _ = prepare_execution(ROOT, args.workers)
        print(json.dumps({"groups": len(groups), "paid_calls": 0, "estimate": estimate}), flush=True)
        return
    if args.cap_usd is None:
        parser.error("Explicit --cap-usd required for paid execution")
    lock_path = ROOT / FOLDER / "full_execution.lock"
    with lock_path.open("a") as execution_lock:
        fcntl.flock(execution_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(ROOT, args.workers, args.cap_usd, args.revisions)


if __name__ == "__main__":
    main()
