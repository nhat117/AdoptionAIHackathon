"""Freeze/estimate first; --run resumes fixed post-review cohorts under the total cap."""

import argparse
import hashlib
import json
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ai2ai_guard.budget_claims import BlindMonitor
from ai2ai_guard.review_client import ReviewClient, append, ledger_total
from ai2ai_guard.review_design import CommitteeClient, committee_design, pilot_design
from ai2ai_guard.review_monitors import improved_messages, parse_monitor
from swarm_lab.budget_review import episode

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/review_v3"


def read(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def freeze(path, value):
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text() != content:
        raise ValueError("frozen_design_changed: " + str(path))
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


class SavedClient:
    def __init__(self, response):
        self.response = response
        self.messages = None

    def chat(self, messages, seed):
        self.messages = messages
        return self.response


def monitor_inputs(workers):
    rows = []
    for worker in workers:
        body = json.loads(worker["messages"][1]["content"])
        for variant in ("original", "improved"):
            if variant == "original":
                capture = SavedClient({"content": '{"decision":"ABSTAIN","reasons":[]}'})
                BlindMonitor(capture).check(body["peer_message"], worker["response"]["content"])
                messages = capture.messages
            else:
                messages = improved_messages(body["task"], body["peer_message"],
                                             worker["response"]["content"], body.get("trusted_record"))
            rows.append({"trial_id": f"{variant}:{worker['trial_id']}", "source_trial_id": worker["trial_id"],
                         "variant": variant, "messages": messages})
    random.Random(20261111).shuffle(rows)
    return rows


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    workers = read(ROOT / "results/measurement_v2_replication/workers.jsonl")
    stages = {"monitors": monitor_inputs(workers), "pilot": pilot_design(ROOT), "committee": committee_design(ROOT)}
    pilot = read(OUT / "pilot/outputs.jsonl")
    if len(pilot) == 36:
        stages["pilot-monitors"] = monitor_inputs(pilot)
    for stage, rows in stages.items():
        freeze(OUT / stage / "inputs.json", rows)
    # Source freeze excludes report/analysis code, which never changes collection.
    names = ["configs/review-v3.json", "configs/authority-wording-v2.json",
             "scripts/run_review_followup.py", "src/ai2ai_guard/review_client.py",
             "src/ai2ai_guard/review_design.py", "src/ai2ai_guard/review_monitors.py",
             "src/swarm_lab/budget_review.py"]
    protocol = {"version": "review-followup-v3.1", "base_commit": "1dcf401",
                "collected_from_dirty_tree": True, "sampling_seed_sent": None,
                "source_sha256": {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in names},
                "stop_rule": "All assigned IDs or aggregate US$20 cap/infrastructure failure; no outcome selection",
                "original_ledger_sha256": hashlib.sha256((ROOT / "results/api_ledger.jsonl").read_bytes()).hexdigest()}
    freeze(OUT / "PROTOCOL.json", protocol)
    return stages


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", choices=("monitors", "pilot", "pilot-monitors", "committee"), default="monitors")
    p.add_argument("--run", action="store_true")
    p.add_argument("--cap-usd", type=float, default=20)
    p.add_argument("--workers", type=int, default=6)
    args = p.parse_args()
    stages = prepare()
    rows = stages.get(args.stage)
    if rows is None:
        raise RuntimeError("collect_pilot_before_pilot_monitors")
    old = ledger_total(ROOT / "results/api_ledger.jsonl")
    current = ledger_total(OUT / "ledger.jsonl")
    estimate = {
        "initial_planned_calls": 2880 + 36 + 72 + 840,
        "stage": args.stage, "stage_assigned_units": len(rows),
        "stage_assigned_calls": len(rows) * (21 if args.stage == "committee" else 1),
        "expected_new_cost_usd": 2880 * .0014 + 36 * .0008 + 72 * .0014 + 840 * .0027,
        "expected_cost_basis": "Historical mean costs with modest allowance; not a guarantee or invoice",
        "accounted_before_stage_usd": round(old + current, 8), "aggregate_cap_usd": args.cap_usd,
        "remaining_usd": round(args.cap_usd - old - current, 8),
        "worst_case": "Every dispatch reserves byte-bound input + 512 output tokens; unknown billing stays reserved. Batch may stop at cap.",
        "run_requested": args.run,
    }
    # This durable estimate is recorded BEFORE dispatch; later invocations get separate records.
    append(OUT / "preflight.jsonl", estimate)
    print(json.dumps(estimate, indent=2), flush=True)
    if not args.run:
        return
    path = OUT / args.stage / "outputs.jsonl"
    saved = read(path)
    done = {r["trial_id"] for r in saved}
    if len(done) != len(saved):
        raise ValueError("duplicate_saved_ids")
    client = ReviewClient(ROOT, cap=args.cap_usd, stage=args.stage)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

    def collect(row):
        if row["trial_id"] in done:
            return
        try:
            if args.stage == "committee":
                result = episode(row["scenario"], CommitteeClient(client, row["attacked"], row["guarded"]))
                append(path, dict(row, result=result, collection_commit=commit))
            else:
                response = client.chat(row["messages"])
                result = dict(row, response=response, collection_commit=commit)
                if args.stage.endswith("monitors"):
                    if row["variant"] == "original":
                        body = json.loads(row["messages"][1]["content"])
                        verdict = BlindMonitor(SavedClient(response)).check(body["peer_message"], body["worker_output"])
                        result["verdict"] = {k: verdict[k] for k in ("decision", "reasons")}
                    else:
                        result["verdict"] = parse_monitor(response["content"], binary=True)
                append(path, result)
        except Exception as error:
            append(OUT / args.stage / "errors.jsonl", {"trial_id": row["trial_id"], "error_type": type(error).__name__,
                                                       "reason": str(error) if isinstance(error, RuntimeError) else "collection_failure"})
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(collect, rows))
    print(json.dumps({"stage": args.stage, "saved_units": len(read(path)), "planned_units": len(rows)}))


if __name__ == "__main__":
    main()
