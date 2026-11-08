"""Frozen H1 collection and paired H3 monitoring; no generation of harmful tasks."""

import argparse
import getpass
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .attacks import build_trials
from .evaluator import evaluate
from .logging_io import freeze, read_jsonl
from .monitor import monitor_messages, verdict
from .providers import Client
from .target import target_messages

ROOT = Path(__file__).resolve().parents[2]


def target_trial(trial, client):
    row = dict(trial)
    messages = target_messages(trial["task"], trial["peer_message"])
    row["prompt_messages"] = messages
    row["system_prompt_hash"] = hashlib.sha256(
        messages[0]["content"].encode()
    ).hexdigest()
    try:
        result = client.chat(messages, trial["seed"])
        row.update(
            completed=True, target=result, **evaluate(result["content"], trial["task"])
        )
    except Exception as error:
        row.update(
            completed=False,
            error=str(error)
            if isinstance(error, RuntimeError)
            else type(error).__name__,
        )
    return row


def monitor_trial(row, client):
    result = dict(row)
    messages = monitor_messages(row, row["candidate_output"], row["visibility"])
    result["prompt_messages"] = messages
    try:
        response = client.chat(messages, row["seed"])
        result["monitor"] = response
        result["block"] = verdict(response["content"])
        result["completed"] = True
    except Exception as error:
        result.update(
            completed=False,
            block=True,
            error=str(error)
            if isinstance(error, RuntimeError)
            else type(error).__name__,
        )
    return result


def collect(path, items, function, client, workers):
    rows = read_jsonl(path)
    done = {r["trial_id"] for r in rows}
    with path.open("a") as stream, ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(function, row, client)
            for row in items
            if row["trial_id"] not in done
        ]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
            if len(rows) % 30 == 0 or len(rows) == len(items):
                print(
                    path.name,
                    len(rows),
                    "/",
                    len(items),
                    "errors",
                    sum(not r["completed"] for r in rows),
                    flush=True,
                )
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["braintrust", "ollama"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--freeze-only", action="store_true")
    parser.add_argument("--skip-monitors", action="store_true")
    args = parser.parse_args(argv)
    if Path(args.run_id).name != args.run_id:
        parser.error("--run-id must be a single directory name")
    config = json.loads((ROOT / "configs/experiment_h1.json").read_text())
    tasks = read_jsonl(ROOT / "data/tasks.jsonl")
    translations = json.loads((ROOT / "data/translations.json").read_text())
    folder = ROOT / "runs" / args.run_id
    freeze(ROOT, folder, config, args.provider, args.model)
    if args.freeze_only:
        print(folder / "FROZEN_PROTOCOL.json")
        return
    key = os.environ.get("BRAINTRUST_API_KEY") or getpass.getpass(
        "Braintrust key (not saved): "
    )
    client = Client(
        args.provider, args.model, key, temperature=config["target_temperature"]
    )
    trials = build_trials(tasks, config, translations)
    print(
        "Planned targets:",
        len(trials),
        "paired monitors:",
        0 if args.skip_monitors else 2 * len(trials),
        flush=True,
    )
    rows = collect(
        folder / "targets.jsonl",
        trials,
        target_trial,
        client,
        6 if args.provider == "braintrust" else 1,
    )
    if not args.skip_monitors:
        monitor = Client(
            config["monitor_provider"],
            config["monitor_model"],
            key,
            temperature=config["monitor_temperature"],
        )
        items = []
        for row in rows:
            if not row["completed"]:
                continue
            for visibility in ["output_only", "full_trace"]:
                item = dict(
                    row,
                    trial_id=row["trial_id"] + "-" + visibility,
                    target_trial_id=row["trial_id"],
                    visibility=visibility,
                    candidate_output=row["target"]["content"],
                )
                items.append(item)
        collect(folder / "monitors.jsonl", items, monitor_trial, monitor, 8)
    (folder / "COLLECTION_COMPLETE.json").write_text(
        json.dumps(
            {
                "attempted_targets": len(rows),
                "target_errors": sum(not r["completed"] for r in rows),
                "monitors_requested": not args.skip_monitors,
            },
            indent=2,
        )
        + "\n"
    )
    print("Collection complete:", folder, flush=True)


if __name__ == "__main__":
    main()
