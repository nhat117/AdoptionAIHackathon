"""Exactly 600 target calls: 200 per language, balanced across sender roles."""

import argparse
import hashlib
import json
import random
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from ai2ai_injection.adaption_provider import AdaptionClient, load_key
from ai2ai_injection.attacks import build_trials, render_attack
from ai2ai_injection.pacing import RequestPacer
from ai2ai_injection.runner import collect, target_trial

ROOT = Path(__file__).resolve().parents[1]


def prepare():
    folder = ROOT / "data/authority500"
    pool = [
        json.loads(x) for x in (folder / "evaluation.jsonl").read_text().splitlines()
    ]
    old = [
        json.loads(x)
        for x in (folder / "selected_500_cases.jsonl").read_text().splitlines()
    ]
    excluded = {r["task"]["task_id"] for r in old}
    assert len(excluded) == 80 and len(pool) == 400
    by_domain = defaultdict(list)
    for task in pool:
        if task["task_id"] not in excluded:
            by_domain[task["domain"]].append(task)
    rng = random.Random(202611087)
    attack_tasks = []
    benign_tasks = []
    for domain in sorted(by_domain):
        candidates = sorted(by_domain[domain], key=lambda t: t["task_id"])
        rng.shuffle(candidates)
        chosen = candidates[:10]
        assert len(chosen) == 10
        benign_tasks.append(chosen[0])
        attack_tasks.extend(chosen[1:])
    assert len(attack_tasks) == 90 and len(benign_tasks) == 10
    translations = json.loads((ROOT / "data/translations.json").read_text())
    cfg = {
        "languages": ["en", "vi", "zh"],
        "authority_conditions": ["peer", "authority"],
        "repetitions": 1,
        "benign_repetitions": 0,
        "seed": 202611087,
        "template_id": "correction_v1",
    }
    cases = build_trials(attack_tasks, cfg, translations)
    benign = build_trials(
        benign_tasks,
        dict(cfg, authority_conditions=[], benign_repetitions=1),
        translations,
    )
    for row in benign:
        for role in ["peer", "authority"]:
            r = dict(row, authority=role)
            tid = f"{r['task']['task_id']}-{r['language']}-{role}-False-0"
            r.update(
                trial_id=tid,
                seed=int(hashlib.sha256(tid.encode()).hexdigest()[:8], 16),
                peer_message=render_attack(
                    r["task"], r["language"], role, translations, attack=False
                ),
            )
            cases.append(r)
    rng.shuffle(cases)
    assert len(cases) == len({r["trial_id"] for r in cases}) == 600
    assert len({r["task"]["task_id"] for r in cases}) == 100
    assert not {r["task"]["task_id"] for r in cases} & excluded
    for language in cfg["languages"]:
        rr = [r for r in cases if r["language"] == language]
        assert len(rr) == 200 and sum(r["attack"] for r in rr) == 180
        assert Counter(r["authority"] for r in rr) == {"peer": 100, "authority": 100}
    path = folder / "selected_600_cases.jsonl"
    content = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in cases)
    if path.exists():
        assert path.read_text() == content
    else:
        path.write_text(content)
    return cfg, cases, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    cfg, cases, data = prepare()
    folder = ROOT / "runs/h1-adaption-authority600"
    folder.mkdir(exist_ok=True)
    config = dict(
        cfg,
        planned_targets=600,
        planned_attack_targets=540,
        planned_benign_targets=60,
        task_limit=100,
        attack_task_clusters=90,
        benign_task_clusters=10,
        target_temperature=0.7,
        max_output_tokens=2048,
        collect_monitors=False,
        pacing_min_interval_seconds=1.5,
        selection="10 fresh heldout tasks per domain; one benign and nine attacked",
        exclusion="All 80 tasks assigned to the stopped 500-case design are excluded",
        language_counts={"en": 200, "vi": 200, "zh": 200},
        purpose="Fixed 600-case exploratory study; no stopping on favorable effects",
        translation_review="Machine audits; independent bilingual review pending",
    )
    paths = list((ROOT / "src/ai2ai_injection").glob("*.py")) + [
        Path(__file__),
        data,
        ROOT / "data/translations.json",
        ROOT / "data/authority500/selected_500_cases.jsonl",
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
                        "Local freeze before dispatch; not external preregistration"
                    ),
                },
                indent=2,
            )
            + "\n"
        )
    print("Prepared 600 cases: 200 per language; 540 attacks and 60 benign", flush=True)
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
    print("600-case collection complete", flush=True)


if __name__ == "__main__":
    main()
