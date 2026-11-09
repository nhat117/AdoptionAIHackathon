"""Fresh-task confirmation after the separate development projection repair."""

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from run_near_target import MODELS, ReuseFirst, oracle, prepare

from ai2ai_guard import ReportGuard
from ai2ai_guard.fact_projection import projected_fact_report
from ai2ai_guard.facts import fact_messages
from ai2ai_injection.adaption_provider import AdaptionClient, load_key
from ai2ai_injection.pacing import RequestPacer
from ai2ai_injection.runner import collect

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "runs/near-target-confirmation-v1"


def confirmation_cases():
    excluded = set()
    for name in ("selected_500_cases.jsonl", "selected_600_cases.jsonl"):
        excluded.update(
            json.loads(x)["task"]["task_id"]
            for x in (ROOT / "data/authority500" / name).read_text().splitlines()
        )
    excluded.update(
        json.loads(x)["task"]["task_id"]
        for x in (ROOT / "data/harness-challenge-v1/live_cases.jsonl")
        .read_text()
        .splitlines()
    )
    available = [
        json.loads(x)
        for x in (ROOT / "data/authority500/evaluation.jsonl").read_text().splitlines()
        if json.loads(x)["task_id"] not in excluded
    ]
    families = ("numeric", "categorical", "distributed", "composite")
    selected = dict(zip(families, available[:4]))
    cases = []
    for original in prepare():
        if original["family"] not in selected:
            continue
        case = dict(original)
        task = dict(selected[case["family"]])
        assert task["split"] == "heldout" and task["task_id"] not in excluded
        task["facts"] = dict(case["task"]["facts"])
        case["task"] = task
        case["expected"] = dict(
            task["facts"],
            task_id=task["task_id"],
            status=task["status"],
            checkpoint=task["milestone"],
        )
        case["trial_id"] = original["trial_id"].replace("near-", "confirm-", 1)
        case["pair_id"] = original["pair_id"].replace("near-", "confirm-", 1)
        cases.append(case)
    assert len(cases) == 48
    return cases


def trial(case, client):
    row = dict(case)
    messages = fact_messages(case["task"], case["annotations"])
    row["prompt_messages"] = messages
    try:
        response = client.chat(messages, None)
        row.update(completed=True, response=response)
        row["oracle"] = oracle(
            response["content"], case["expected"], case["task"]["marker"]
        )
        row["original_gate"] = asdict(
            ReportGuard().check(response["content"], case["task"])
        )
        reuse = ReuseFirst(response, client, messages)
        result = projected_fact_report(case["task"], case["annotations"], reuse)
        row["protected"] = asdict(result)
        row["recovery"] = reuse.recovery
        row["released_oracle"] = (
            oracle(json.dumps(result.report), case["expected"], case["task"]["marker"])
            if result.released
            else None
        )
        assert (
            result.audit[0]["candidate_sha256"]
            == hashlib.sha256(response["content"].encode()).hexdigest()
        )
    except Exception as error:
        row.update(completed=False, error=type(error).__name__)
        for attr in ("request_attempts", "response_metadata"):
            if hasattr(error, attr):
                row[attr] = getattr(error, attr)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    cases = confirmation_cases()
    FOLDER.mkdir(parents=True, exist_ok=True)
    inputs = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases)
    sources = [
        Path(__file__),
        ROOT / "scripts/run_near_target.py",
        ROOT / "src/ai2ai_guard/facts.py",
        ROOT / "src/ai2ai_guard/fact_projection.py",
        ROOT / "src/ai2ai_guard/__init__.py",
        ROOT / "src/ai2ai_injection/target.py",
    ]
    spec = {
        "phase": "fresh heldout-task confirmation; small, four task clusters",
        "models": MODELS,
        "pairs": 24,
        "initial_calls": 48,
        "families": ["numeric", "categorical", "distributed", "composite"],
        "guard": "projected trusted facts; frozen after development repair",
        "sampling": "First four unused evaluation tasks in saved pool order; exclude all 80 stopped500, 100 prior600 and 100 challenge task IDs",
        "temperature": 0.7,
        "max_output_tokens": 4096,
        "stop_rule": "Complete all cases; no expansion based on outcomes",
        "primary_endpoint": "Targeted substitution conditional on correct matched clean output; compare identical first candidates before and after guard",
        "inputs_sha256": hashlib.sha256(inputs.encode()).hexdigest(),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sources
        },
    }
    frozen = FOLDER / "FROZEN_PROTOCOL.json"
    if frozen.exists():
        assert json.loads(frozen.read_text())["spec"] == spec
    else:
        frozen.write_text(
            json.dumps(
                {
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "registration": "Local freeze, not external preregistration",
                    "spec": spec,
                },
                indent=2,
            )
            + "\n"
        )
        (FOLDER / "inputs.jsonl").write_text(inputs)
    print("Frozen 24 fresh-task attack/clean pairs", flush=True)
    if not args.run:
        return
    key = load_key("adaption")
    for model in MODELS:
        client = AdaptionClient(
            model, key, max_output_tokens=4096, pacer=RequestPacer(interval=2)
        )
        try:
            collect(
                FOLDER / (model + ".jsonl"),
                [c for c in cases if c["model"] == model],
                trial,
                client,
                4,
            )
        finally:
            client.close()
    print("Fresh-task confirmation finished", flush=True)


if __name__ == "__main__":
    main()
