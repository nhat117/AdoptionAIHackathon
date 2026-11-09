"""Project paired harness records into the dashboard's reviewed query schemas."""

import hashlib
import json

LANG = {"en": "English", "vi": "Vietnamese", "zh": "Chinese"}


def read(path):
    return (
        [json.loads(x) for x in path.read_text().splitlines() if x]
        if path.exists()
        else []
    )


def challenge_rows(root):
    folder = root / "runs/harness-challenge-live"
    if not (folder / "COLLECTION_COMPLETE.json").exists():
        return [], [], [], [], []
    path = folder / "trials.jsonl"
    raw = read(path)
    base = {
        "cohort": "Harness challenge",
        "run_id": folder.name,
        "model": "Gemma 4 · 26B-A4B (paired harness)",
        "model_id": "gemma-4-26b-a4b-it",
    }
    targets = []
    protection = []
    for r in raw:
        t = r.get("target", {})
        b = r.get("baseline", {})
        p = r.get("protected", {})
        common = dict(
            base,
            id=folder.name + ":" + r["trial_id"],
            trial_id=r["trial_id"],
            language=LANG[r["language"]],
            language_code=r["language"],
            sender="Peer" if r["authority"] == "peer" else "Director",
            condition="Attack" if r["attack"] else "Benign",
        )
        targets.append(
            dict(
                common,
                task_id=r["task"]["task_id"],
                rep=0,
                completed=r["completed"],
                leak=b.get("marker_disclosed"),
                violation=b.get("policy_violation"),
                utility_complete=b.get("task_complete"),
                error=r.get("error", ""),
                latency_s=t.get("latency_s"),
                response=t.get("content", ""),
                peer_message=r["peer_message"],
                marker=r["task"]["marker"],
                source_file=str(path.relative_to(root)),
                returned_model=t.get("model", ""),
                prompt_tokens=t.get("usage", {}).get("prompt_tokens"),
                completion_tokens=t.get("usage", {}).get("completion_tokens"),
            )
        )
        protection.append(
            dict(
                common,
                case_id=r["trial_id"],
                peer_message=r["peer_message"],
                baseline_response=t.get("content", ""),
                error=r.get("error", ""),
                released=p.get("released", False),
                attempts=p.get("attempts", 0),
                report=json.dumps(p.get("report"), ensure_ascii=False),
                audit=json.dumps(p.get("audit", [])),
                baseline_violation=b.get("policy_violation"),
                released_violation=bool(
                    r.get("released_assessment", {}).get("policy_violation")
                )
                if r.get("released_assessment")
                else False,
                baseline_complete=r["completed"],
                family=r["family"],
            )
        )
    completed = sum(r["completed"] for r in raw)
    health = [
        dict(
            base,
            planned=600,
            planned_cell=90,
            attempted=len(raw),
            completed=completed,
            failed=len(raw) - completed,
            coverage=completed / 600,
            monitor_attempts=0,
            monitor_completed=0,
            status="Complete" if completed == 600 else "Incomplete",
            source_hash=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
    ]
    f = root / "runs/harness-challenge-faults"
    v1 = json.loads((f / "v1_metrics.json").read_text())
    v2 = json.loads((f / "current_metrics.json").read_text())
    faults = [
        {
            "id": str(i),
            "cohort": "Harness challenge",
            "stage": stage,
            "unsafe_released": n,
            "unsafe_candidates": v2["unsafe"],
            "benign_released": (
                v1["benign_released"]
                if stage == "Original gate"
                else (
                    v2["benign"] if stage == "Without gate" else v2["benign_released"]
                )
            ),
            "benign_candidates": v2["benign"],
            "origin": "Controlled generator faults; not model attack success",
        }
        for i, (stage, n) in enumerate(
            [
                ("Without gate", v2["unsafe"]),
                ("Original gate", v1["unsafe_released"]),
                ("Updated gate", v2["unsafe_released"]),
            ]
        )
    ]
    files = [
        str(path.relative_to(root)),
        str((f / "v1_metrics.json").relative_to(root)),
        str((f / "current_metrics.json").relative_to(root)),
        "data/harness-challenge-v1/fault_heldout.jsonl",
    ]
    return targets, health, protection, faults, files
