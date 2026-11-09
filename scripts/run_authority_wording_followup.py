"""Locally freeze a wording-balanced worker-only follow-up; no inference by default."""

import argparse
import copy
import hashlib
import json
import math
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from ai2ai_guard.review_client import ReviewClient, append, ledger_total

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/authority_wording_v2"


def read(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def digest(data):
    return hashlib.sha256(data).hexdigest()


def design(root=ROOT):
    cfg = json.loads((root / "configs/authority-followup-v1.json").read_text())
    words = json.loads((root / cfg["wording_source"]).read_text())
    inputs = read(root / "results/measurement_v2_replication/inputs.jsonl")
    rows = []
    for original in inputs:
        if original["cluster"] not in cfg["task_clusters"]:
            continue
        for variant in cfg["wordings"]:
            row = copy.deepcopy(original)
            lang, authority = row["language"], row["authority"]
            role = words["roles"][lang][authority]
            template = words["wordings"][lang][variant] if row["attack"] else cfg["clean_wordings"][lang][variant]
            peer = template.format(role=role, budget=row["false_budget"])
            row.update(trial_id=f"wording-v1-w{variant}-{original['trial_id']}",
                       source_trial_id=original["trial_id"], wording=variant,
                       prompt_version=cfg["version"], peer_message=peer)
            body = json.loads(row["messages"][1]["content"])
            body["peer_message"] = peer
            row["messages"][1]["content"] = json.dumps(body, ensure_ascii=False)
            rows.append(row)
    random.Random(cfg["dispatch_seed"]).shuffle(rows)
    return rows


def prepare():
    cfg = json.loads((ROOT / "configs/authority-followup-v1.json").read_text())
    rows = design()
    if len(rows) != cfg["planned_worker_calls"] or len({r["trial_id"] for r in rows}) != len(rows):
        raise ValueError("unexpected_or_duplicate_design")
    OUT.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    path = OUT / "inputs.jsonl"
    if path.exists() and path.read_text() != text:
        raise ValueError("frozen_inputs_changed")
    if not path.exists():
        path.write_text(text)
    names = ["configs/authority-followup-v1.json", "configs/authority-wording-v2.json",
             "scripts/run_authority_wording_followup.py", "src/ai2ai_guard/review_client.py",
             "src/ai2ai_guard/review_measurement.py", "src/ai2ai_guard/budget_claims_v2.py"]
    sources = {n: digest((ROOT / n).read_bytes()) for n in names}
    protocol_path = OUT / "PROTOCOL.json"
    if protocol_path.exists():
        protocol = json.loads(protocol_path.read_text())
        if protocol["source_sha256"] != sources or protocol["inputs_sha256"] != digest(text.encode()):
            raise ValueError("frozen_collection_source_changed")
    else:
        append_only = {}
        for name in ("results/review_v3/api_responses.jsonl", "results/review_v3/ledger.jsonl"):
            data = (ROOT / name).read_bytes()
            append_only[name] = {"bytes": len(data), "prefix_sha256": digest(data)}
        protocol = dict(cfg, frozen_utc=datetime.now(timezone.utc).isoformat(),
                        base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                        dirty_tree=True, registration="Local prospective freeze after historical inspection, not external preregistration",
                        source_sha256=sources, inputs_sha256=digest(text.encode()),
                        preserved_log_prefixes=append_only, model="gpt-5", reasoning_effort="minimal",
                        max_completion_tokens=512, sampling_seed_sent=None,
                        monitor_evaluation="Not collected for this worker-only follow-up")
        protocol_path.write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n")
    for name, meta in protocol["preserved_log_prefixes"].items():
        if digest((ROOT / name).read_bytes()[:meta["bytes"]]) != meta["prefix_sha256"]:
            raise ValueError("prior_append_only_evidence_modified")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--cap-usd", type=float, default=20)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    rows = prepare()
    historical = read(ROOT / "results/measurement_v2_replication/workers.jsonl")
    mean = math.fsum((r["response"]["usage"]["prompt_tokens"] * 1.25 + r["response"]["usage"]["completion_tokens"] * 10) / 1e6 for r in historical) / len(historical)
    accounted = ledger_total(ROOT / "results/api_ledger.jsonl") + ledger_total(ROOT / "results/review_v3/ledger.jsonl")
    estimate = {"stage": "authority-wording-v2", "planned_calls": len(rows),
                "expected_usd_at_historical_mean": round(mean * len(rows), 6),
                "planning_allowance_usd_15pct": round(1.15 * mean * len(rows), 6),
                "accounted_before_run_usd": round(accounted, 8),
                "aggregate_cap_usd": args.cap_usd, "run_requested": args.run,
                "stop_rule": "Fixed IDs or cap/infrastructure; per-request conservative reservations, no outcome selection"}
    append(OUT / "preflight.jsonl", estimate)
    print(json.dumps(estimate, indent=2), flush=True)
    if not args.run:
        return
    path = OUT / "workers.jsonl"
    saved = read(path)
    done = {r["trial_id"] for r in saved}
    if len(done) != len(saved):
        raise ValueError("duplicate_saved_ids")
    client = ReviewClient(ROOT, cap=args.cap_usd, stage="authority-wording-v2")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

    def collect(row):
        if row["trial_id"] in done:
            return
        try:
            response = client.chat(row["messages"])
            append(path, dict(row, response=response, collection_commit=commit))
        except Exception as error:
            append(OUT / "errors.jsonl", {"trial_id": row["trial_id"], "error_type": type(error).__name__,
                                         "reason": str(error) if isinstance(error, RuntimeError) else "collection_failure"})
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(collect, rows))
    print(json.dumps({"saved": len(read(path)), "assigned": len(rows)}))


if __name__ == "__main__":
    main()
