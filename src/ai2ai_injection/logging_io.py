"""Immutable protocol manifest and append-only trial records."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone


def read_jsonl(path):
    return (
        [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        if path.exists()
        else []
    )


def freeze(root, folder, config, provider, model):
    paths = list((root / "src/ai2ai_injection").glob("*.py"))
    paths += [
        *sorted((root / "configs").glob("*.json")),
        root / "data/tasks.jsonl",
        root / "data/translations.json",
    ]
    hashes = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in paths
    }
    spec = {
        "config": config,
        "provider": provider,
        "model": model,
        "file_hashes": hashes,
    }
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "FROZEN_PROTOCOL.json"
    if path.exists():
        if json.loads(path.read_text())["spec"] != spec:
            raise ValueError(
                "Frozen configuration/code changed; use a new run directory"
            )
        return
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain"], text=True
    )
    path.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "spec": spec,
                "git_commit": commit,
                "working_tree_status": dirty,
                "registration": "local freeze, not external preregistration",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
