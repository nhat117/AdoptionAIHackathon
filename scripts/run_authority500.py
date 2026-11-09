"""Exactly 500 Adaption target calls: 480 paired attacks and 20 benign controls."""

import argparse
import hashlib
import json
import random
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from ai2ai_injection.adaption_provider import AdaptionClient, load_key
from ai2ai_injection.attacks import build_trials
from ai2ai_injection.pacing import RequestPacer
from ai2ai_injection.runner import collect, target_trial

ROOT = Path(__file__).resolve().parents[1]


def prepare():
    folder = ROOT / "data/authority500"
    pool = [
        json.loads(x) for x in (folder / "evaluation.jsonl").read_text().splitlines()
    ]
    assert len(pool) == 400 and all(t["split"] == "heldout" for t in pool)
    by_domain = defaultdict(list)
    for task in pool:
        by_domain[task["domain"]].append(task)
    rng = random.Random(202611086)
    selected = []
    for domain in sorted(by_domain):
        candidates = sorted(by_domain[domain], key=lambda t: t["task_id"])
        rng.shuffle(candidates)
        selected.extend(candidates[:8])
    assert len(selected) == 80
    translations = json.loads((ROOT / "data/translations.json").read_text())
    cfg = {
        "languages": ["en", "vi", "zh"],
        "authority_conditions": ["peer", "authority"],
        "repetitions": 1,
        "benign_repetitions": 0,
        "seed": 202611086,
        "template_id": "correction_v1",
    }
    attacks = build_trials(selected, cfg, translations)
    benign_cfg = dict(cfg, authority_conditions=[], benign_repetitions=1)
    available = {
        (r["task"]["task_id"], r["language"]): r
        for r in build_trials(selected, benign_cfg, translations)
    }
    control_tasks = []
    for domain in sorted(by_domain):
        candidates = [t for t in selected if t["domain"] == domain]
        rng.shuffle(candidates)
        control_tasks.extend(candidates[:2])
    rng.shuffle(control_tasks)
    controls = [
        available[t["task_id"], ["en", "vi", "zh"][i % 3]]
        for i, t in enumerate(control_tasks)
    ]
    cases = attacks + controls
    rng.shuffle(cases)
    assert len(cases) == len({r["trial_id"] for r in cases}) == 500
    assert len(attacks) == 480 and len(controls) == 20
    for language in cfg["languages"]:
        for role in cfg["authority_conditions"]:
            assert (
                sum(
                    r["attack"] and r["language"] == language and r["authority"] == role
                    for r in cases
                )
                == 80
            )
    data = folder / "selected_500_cases.jsonl"
    content = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in cases)
    if data.exists():
        assert data.read_text() == content
    else:
        data.write_text(content)
    return cfg, cases, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    cfg, cases, data = prepare()
    folder = ROOT / "runs/h1-adaption-authority500"
    folder.mkdir(exist_ok=True)
    config = dict(
        cfg,
        planned_targets=500,
        planned_attack_targets=480,
        planned_benign_targets=20,
        task_limit=80,
        target_temperature=0.7,
        max_output_tokens=2048,
        collect_monitors=False,
        pacing_min_interval_seconds=1.5,
        controls="20 tasks, 2 per domain; languages en=7, vi=7, zh=6",
        selection="8 heldout tasks per domain, 10 domains; seed 202611086",
        purpose=(
            "Fixed 500-case exploratory evaluation; no stopping by effect direction"
        ),
        translation_review="Machine audits only; independent bilingual review pending",
    )
    paths = list((ROOT / "src/ai2ai_injection").glob("*.py")) + [
        Path(__file__),
        data,
        ROOT / "data/translations.json",
    ]
    spec = {
        "config": config,
        "provider": "adaption",
        "model": "gemma-4-26b-a4b-it",
        "file_hashes": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths
        },
    }
    protocol = folder / "FROZEN_PROTOCOL.json"
    if protocol.exists():
        assert json.loads(protocol.read_text())["spec"] == spec
    else:
        protocol.write_text(
            json.dumps(
                {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "spec": spec,
                    "git_commit": subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], text=True
                    ).strip(),
                    "registration": (
                        "Local source freeze before calls; not external preregistration"
                    ),
                },
                indent=2,
            )
            + "\n"
        )
    print("Prepared 500 cases: 480 attacks, 20 benign; 80 paired tasks", flush=True)
    if not args.run:
        return
    client = AdaptionClient(
        spec["model"],
        load_key("adaption"),
        temperature=0.7,
        max_output_tokens=2048,
        pacer=RequestPacer(interval=1.5),
    )
    try:
        rows = collect(folder / "targets.jsonl", cases, target_trial, client, 6)
    finally:
        client.close()
    (folder / "monitors.jsonl").touch()
    (folder / "COLLECTION_COMPLETE.json").write_text(
        json.dumps(
            {
                "attempted_targets": len(rows),
                "target_errors": sum(not r["completed"] for r in rows),
                "monitors_requested": False,
            },
            indent=2,
        )
        + "\n"
    )
    print("500-case collection complete", flush=True)


if __name__ == "__main__":
    main()
