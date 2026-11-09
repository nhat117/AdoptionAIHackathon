"""Freeze/estimate a 180-call neutral-prompt pilot; --run required for inference."""

import argparse
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Event

from ai2ai_guard.review_client import ReviewClient, append, ledger_total
from ai2ai_guard.round3_neutral import design, score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/round3_neutral"


def read(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def prepare():
    cfg = json.loads((ROOT / "configs/round3-neutral-v1.json").read_text())
    rows = design(ROOT)
    if len(rows) != 180 or len({r["trial_id"] for r in rows}) != 180:
        raise ValueError("invalid_neutral_design")
    OUT.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    path = OUT / "inputs.jsonl"
    if path.exists() and path.read_text() != text:
        raise ValueError("frozen_neutral_inputs_changed")
    if not path.exists():
        path.write_text(text)
    names = ["configs/round3-neutral-v1.json", "scripts/run_round3_neutral.py",
             "src/ai2ai_guard/round3_neutral.py", "src/ai2ai_guard/review_client.py",
             "src/ai2ai_guard/review_measurement.py", cfg["neutral_source"], cfg["attack_text_source"]]
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}
    p = OUT / "PROTOCOL.json"
    if p.exists():
        protocol = json.loads(p.read_text())
        if protocol["source_sha256"] != hashes:
            raise ValueError("frozen_neutral_source_changed")
    else:
        protocol = dict(cfg, source_sha256=hashes, inputs_sha256=hashlib.sha256(text.encode()).hexdigest(),
                        frozen_utc=datetime.now(timezone.utc).isoformat(),
                        base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                        dirty_tree=True, registration="Local prospective freeze, not external preregistration")
        p.write_text(json.dumps(protocol, indent=2) + "\n")
    return rows, cfg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    rows, cfg = prepare()
    reserve = sum((len(json.dumps(r["messages"]).encode()) * 1.25 + 512 * 10) / 1e6 for r in rows)
    accounted = ledger_total(ROOT / "results/api_ledger.jsonl") + ledger_total(ROOT / "results/review_v3/ledger.jsonl")
    preflight = {"planned_calls": len(rows), "mean_based_estimate_usd": round(180 * .0011191215277777777, 6),
                 "no_retry_byte_bound_reservation_usd": round(reserve, 6),
                 "accounted_before_usd": round(accounted, 8), "aggregate_cap_usd": 20,
                 "run_requested": args.run, "model": cfg["model"], "reasoning_effort": "minimal"}
    append(OUT / "preflight.jsonl", preflight)
    print(json.dumps(preflight, indent=2), flush=True)
    if not args.run:
        return
    if not 1 <= args.workers <= 8:
        raise ValueError("workers_must_be_1_to_8")
    client = ReviewClient(ROOT, cap=20, stage="round3-neutral")
    path = OUT / "workers.jsonl"
    prior = read(path)
    done = {r["trial_id"] for r in prior}
    if len(done) != len(prior):
        raise ValueError("duplicate_neutral_observations")
    stopped = Event()

    def collect(row):
        if row["trial_id"] in done or stopped.is_set():
            return
        try:
            response = client.chat(row["messages"])
            observation = dict(row, response=response, model_configuration={
                "requested_model": "gpt-5", "reasoning_effort": "minimal", "max_completion_tokens": 512,
                "sampling_seed_sent": None, "temperature_override": None})
            observation["measurement"] = score(observation)
            append(path, observation)
            if response["model"] != cfg["expected_returned_model"]:
                stopped.set()
                raise RuntimeError("unexpected_returned_model_retained; stop rather than substitute")
        except Exception as error:
            append(OUT / "errors.jsonl", {"trial_id": row["trial_id"], "error_type": type(error).__name__,
                                         "reason": str(error) if isinstance(error, RuntimeError) else "transport_or_collection_error"})
    pending = [r for r in rows if r["trial_id"] not in done]
    if pending:
        collect(pending[0])  # fixed first assigned case checks actual model, not outcome
    if not stopped.is_set():
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(collect, pending[1:]))
    print(json.dumps({"assigned": 180, "saved": len(read(path)), "model_mismatch_stop": stopped.is_set()}))


if __name__ == "__main__":
    main()
