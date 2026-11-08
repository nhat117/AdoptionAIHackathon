"""Export research data and optionally import development rows to Adaption."""

import argparse
import hashlib
import json
from pathlib import Path

from adaption import Adaption

from ai2ai_guard import ReportGuard
from ai2ai_injection.adaption_provider import load_key
from ai2ai_injection.attacks import build_trials
from ai2ai_injection.target import target_messages

ROOT = Path(__file__).resolve().parents[1]


def development_reference(trial):
    task = trial["task"]
    if task["split"] != "development":
        raise ValueError("Heldout tasks cannot enter the development upload")
    response = json.dumps(
        {
            "task_id": task["task_id"],
            "status": task["status"],
            "public_summary": f"The {task['topic']} Checkpoint: {task['milestone']}.",
        },
        ensure_ascii=False,
    )
    if not ReportGuard().check(response, task).allowed:
        raise ValueError("Reference failed the deterministic reporting contract")
    return {
        "instruction": target_messages(task, trial["peer_message"]),
        "response": response,
        "task_id": task["task_id"],
        "language": trial["language"],
        "authority": trial["authority"],
        "attack": trial["attack"],
        "split": "development",
        "reference_type": "constructed_safe_reference",
        "human_reviewed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upload-development", action="store_true")
    args = parser.parse_args()
    folder = ROOT / "data/authority500"
    tasks = [json.loads(x) for x in (folder / "tasks.jsonl").read_text().splitlines()]
    assert len(tasks) == len({r["task_id"] for r in tasks}) == 500
    translations = json.loads((ROOT / "data/translations.json").read_text())
    config = {
        "languages": ["en", "vi", "zh"],
        "authority_conditions": ["peer", "authority"],
        "repetitions": 1,
        "benign_repetitions": 1,
        "seed": 202611085,
        "template_id": "correction_v1",
    }
    dev = [r for r in tasks if r["split"] == "development"]
    heldout = [r for r in tasks if r["split"] == "heldout"]
    assert len(dev) == 100 and len(heldout) == 400
    assert not {r["task_id"] for r in dev} & {r["task_id"] for r in heldout}
    references = [
        development_reference(t) for t in build_trials(dev, config, translations)
    ]
    trial_rows = build_trials(heldout, config, translations)
    for name, rows in [
        ("development_references", references),
        ("evaluation_trials", trial_rows),
    ]:
        (folder / f"{name}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
        )
    source = folder / "development_references.jsonl"
    manifest = {
        "base_tasks": 500,
        "development_tasks": 100,
        "heldout_tasks": 400,
        "development_reference_rows": len(references),
        "heldout_trial_rows": len(trial_rows),
        "heldout_attack_rows": sum(r["attack"] for r in trial_rows),
        "heldout_benign_rows": sum(not r["attack"] for r in trial_rows),
        "evaluation_run_status": "Not dispatched; no observed model outcomes",
        "training_or_adaptation_started": False,
        "upload_permitted_split": "development only",
        "task_file_sha256": hashlib.sha256(
            (folder / "tasks.jsonl").read_bytes()
        ).hexdigest(),
        "upload_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "evaluation_trials_sha256": hashlib.sha256(
            (folder / "evaluation_trials.jsonl").read_bytes()
        ).hexdigest(),
        "translation_review": "Machine audit; independent bilingual review pending",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (folder / "EXPORT_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)
    if not args.upload_development:
        return
    receipt = folder / "ADAPTION_IMPORT.json"
    with Adaption(api_key=load_key("adaption"), max_retries=0, timeout=120) as client:
        if receipt.exists():
            record = json.loads(receipt.read_text())
            assert record["upload_sha256"] == manifest["upload_sha256"]
            dataset_id = record["dataset_id"]
        else:
            dataset_id = client.datasets.upload_file(str(source)).dataset_id
            record = {
                "dataset_id": dataset_id,
                "upload_sha256": manifest["upload_sha256"],
                "rows": len(references),
                "split": "development",
                "adaptation_started": False,
            }
            receipt.write_text(json.dumps(record, indent=2) + "\n")
        status = client.datasets.get_status(dataset_id)
        (folder / "ADAPTION_STATUS.json").write_text(
            json.dumps(status.model_dump(mode="json"), indent=2) + "\n"
        )
        print(
            "Adaption development dataset:",
            dataset_id,
            "status:",
            status.status,
            flush=True,
        )


if __name__ == "__main__":
    main()
