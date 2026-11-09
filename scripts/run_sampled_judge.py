"""Sampled multilingual LLM validation; offline by default, no full-corpus calls."""

import argparse
import fcntl
import json
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from run_llm_judge import revision_messages

from ai2ai_guard.gpt5_judge_api import MODEL, PRICING, RETURNED_MODEL, response_text
from ai2ai_guard.gpt5_judge_batch import AUTHORIZATION, append_sharded, read_records
from ai2ai_guard.judge_transport import BudgetedChatJudge, bound
from ai2ai_guard.llm_judge import (
    REVISION_SCHEMA,
    aggregate,
    extract_groups,
    sha,
    validate_assessment,
    validate_revision,
)
from ai2ai_guard.sampled_judge import (
    FOLDER,
    MAX_OUTPUT,
    PROJECT_CAP,
    QUOTE_INSTRUCTION,
    STAGE,
    VERSION,
    sample_groups,
    sample_messages,
    sample_schema,
)

ROOT = Path(__file__).resolve().parents[1]


def prepare(root=ROOT):
    population, files = extract_groups(root)
    groups, manifest = sample_groups(population)
    folder = root / FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    corpus = "".join(json.dumps(g, ensure_ascii=False) + "\n" for g in groups)
    sources = ("scripts/run_sampled_judge.py", "src/ai2ai_guard/sampled_judge.py",
               "src/ai2ai_guard/judge_transport.py", "src/ai2ai_guard/llm_judge.py",
               "src/ai2ai_guard/gpt5_judge_api.py", "src/ai2ai_guard/gpt5_judge_batch.py",
               "scripts/run_llm_judge.py", AUTHORIZATION)
    protocol = {"version": VERSION, "model": MODEL, "reasoning_effort": "high", "max_output_tokens": MAX_OUTPUT,
                "repeats": 3, "workers": 8, "source_files_sha256": files,
                "source_sha256": {name: sha((root / name).read_bytes()) for name in sources},
                "corpus_sha256": sha(corpus.encode()), "selection_sha256": sha(manifest),
                "pricing": PRICING, "sample_project_cap_usd": PROJECT_CAP, "aggregate_cap_usd": 650,
                "sampling": "5% stratified random sample, 1 of 20 tasks per cohort/authority/wording/record/attack stratum",
                "prior_ratings_reused": False, "english_is_gold_standard": False,
                "historical_data_changed": False, "quote_instruction": QUOTE_INSTRUCTION,
                "limitations": "Sampled LLM-based, not full-corpus/human validation. Repeated one-model judgments and task reuse may correlate. Worker/judge model family overlap."}
    texts = {"PROTOCOL.json": json.dumps(protocol, indent=2) + "\n",
             "SAMPLE_SELECTION.json": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
             "aligned_prompts.jsonl": corpus}
    for name, text in texts.items():
        path = folder / name
        if path.exists() and path.read_text() != text:
            raise ValueError("frozen_sample_or_instrument_changed_use_new_version")
        if not path.exists():
            path.write_text(text)
    bounds = [bound(sample_messages(g, 0), sample_schema(), MAX_OUTPUT) for g in groups]
    estimate = {"aligned_groups": 96, "population_aligned_groups": 1920, "initial_judge_requests": 288,
                "initial_no_retry_conservative_ceiling_usd": round(sum(bounds) * 3, 6),
                "initial_max_retry_conservative_ceiling_usd": round(sum(bounds) * 9, 6),
                "initial_planning_estimate_usd": round(sum(b - .16384 + .08 for b in bounds) * 3, 6),
                "planning_output_tokens_per_call_not_observed": 8000, "pricing": PRICING,
                "project_cap_usd": PROJECT_CAP, "scope": "288 initial requests including 3 smoke calls; flagged revisions cost extra within the same US$60 project / US$650 aggregate caps"}
    (folder / "cost_estimate.json").write_text(json.dumps(estimate, indent=2) + "\n")
    return groups, estimate


def execute(root, groups, cap, smoke=False, revisions=False):
    folder = root / FOLDER
    protocol_hash = sha((folder / "PROTOCOL.json").read_bytes())
    if not smoke:
        receipt = json.loads((folder / "SMOKE_COMPLETE.json").read_text())
        if receipt["protocol_sha256"] != protocol_hash or receipt["returned_model"] != RETURNED_MODEL or receipt["valid_structured_responses"] != 3:
            raise ValueError("valid_sample_smoke_required")
    api = BudgetedChatJudge(root, VERSION, FOLDER, STAGE, MAX_OUTPUT, cap)
    lock, stop = threading.Lock(), threading.Event()
    raw = read_records(folder / "raw_responses.jsonl")
    raw_by_key = {r["request_key"]: r for r in raw}
    saved = read_records(folder / "judgments.jsonl") + read_records(folder / "revised_judgments.jsonl")
    keys = {r["request_key"] for r in saved}
    if len(raw_by_key) != len(raw) or len(keys) != len(saved):
        raise ValueError("duplicate_saved_sample_requests")
    sample_ids = {g["group_id"] for g in groups}
    if any(r["group_id"] not in sample_ids for r in saved):
        raise ValueError("unassigned_sample_group")

    def create(messages, schema, key):
        previous = raw_by_key.get(key)
        if previous:
            if (previous["profile"] != VERSION or previous["messages"] != messages or previous["schema_sha256"] != sha(schema)
                    or previous["raw_response"].get("model") != RETURNED_MODEL):
                raise ValueError("saved_sample_response_mismatch")
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
            messages = sample_messages(group, repeat, replacement)
            record, text = create(messages, sample_schema(), key)
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
                keys.add(key)
                print(json.dumps({"phase": phase, "saved": len(saved), "valid": sum(r["status"] == "VALID" for r in saved)}), flush=True)
        except Exception:
            stop.set()
            raise

    if smoke:
        for repeat in range(3):
            assess(groups[0], repeat)
        rows = [r for r in saved if r["group_id"] == groups[0]["group_id"] and r["phase"] == "original"]
        if aggregate(groups[0], rows)["valid_judgments"] != 3 or {r["returned_model"] for r in rows} != {RETURNED_MODEL}:
            raise RuntimeError("sample_smoke_check_failed")
        (folder / "SMOKE_COMPLETE.json").write_text(json.dumps({"group_id": groups[0]["group_id"], "returned_model": RETURNED_MODEL,
                                                                "valid_structured_responses": 3, "protocol_sha256": protocol_hash,
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
                if draft is None:
                    messages = revision_messages(group, rows)
                    messages[0]["content"] += QUOTE_INSTRUCTION
                    record, text = create(messages, REVISION_SCHEMA, "draft:" + group["group_id"])
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
    return {"saved_initial_records": len(original), "valid_initial_judgments": sum(r["status"] == "VALID" for r in original),
            "planned_initial_judgments": 288, "sample_groups": 96, "population_groups": 1920,
            "full_corpus_validation_claimed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    stages = parser.add_mutually_exclusive_group()
    for name in ("smoke", "run", "revisions", "workflow"):
        stages.add_argument("--" + name, action="store_true")
    parser.add_argument("--cap-usd", type=float)
    args = parser.parse_args()
    groups, estimate = prepare()
    if not any((args.smoke, args.run, args.revisions, args.workflow)):
        print(json.dumps(dict(estimate, paid_calls=0)), flush=True)
        return
    if args.cap_usd is None or not 0 < args.cap_usd <= PROJECT_CAP:
        parser.error("Explicit --cap-usd required, at most the US$60 sampled-project allocation")
    folder, failure = ROOT / FOLDER, None
    status_path = folder / "execution_status.json"
    with (folder / "execution.lock").open("a") as execution_lock:
        fcntl.flock(execution_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            modes = ("smoke", "original", "revisions") if args.workflow else (("smoke",) if args.smoke else ("revisions",) if args.revisions else ("original",))
            for mode in modes:
                status_path.write_text(json.dumps({"status": "RUNNING_" + mode.upper(), "scope": "STRATIFIED_RANDOM_SAMPLE",
                                                  "started_utc": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
                result = execute(ROOT, groups, args.cap_usd, smoke=mode == "smoke", revisions=mode == "revisions")
            result["status"] = "WORKFLOW_STAGES_FINISHED" if args.workflow else "STAGE_FINISHED"
            status_path.write_text(json.dumps(result, indent=2) + "\n")
        except Exception as error:
            failure = error
            status_path.write_text(json.dumps({"status": "BLOCKED_OR_INTERRUPTED", "error_type": type(error).__name__,
                                              "reason": str(error) if isinstance(error, (ValueError, RuntimeError)) else "execution_error"}, indent=2) + "\n")
    # All collectors have stopped before reports are rebuilt. Failed stages still
    # produce truthful partial artifacts; never infer full-corpus completion.
    for script in ("scripts/run_research_pipeline.py", "scripts/export_review_report.py"):
        subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=True)
    if failure:
        raise failure


if __name__ == "__main__":
    main()
