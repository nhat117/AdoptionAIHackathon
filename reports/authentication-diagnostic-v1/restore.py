"""Restore raw diagnostic records without replacing differing files or inference."""

import base64
import fcntl
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "runs/authentication-diagnostic-v1"


def restore():
    if RUN.resolve() != ROOT.resolve() / "runs/authentication-diagnostic-v1":
        raise ValueError("Diagnostic root must not redirect through symlinks")
    RUN.mkdir(parents=True, exist_ok=True)
    lock = (RUN / "collector.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    with gzip.open(
        Path(__file__).with_name("raw-records.jsonl.gz"), "rt", encoding="utf-8"
    ) as f:
        rows = [json.loads(line) for line in f]
    targets = []
    seen = set()
    for row in rows:
        path = Path(row["path"])
        target = (ROOT / path).resolve()
        if (
            path.is_absolute()
            or not target.is_relative_to(RUN.resolve())
            or target == RUN.resolve()
        ):
            raise ValueError("Archive path outside diagnostic root")
        if target in seen:
            raise ValueError("Duplicate archive destination")
        seen.add(target)
        content = base64.b64decode(row["content_base64"], validate=True)
        if hashlib.sha256(content).hexdigest() != row["sha256"]:
            raise ValueError("Archive record hash mismatch")
        if target.exists() and target.read_bytes() != content:
            raise ValueError("Refusing to overwrite differing record: " + str(target))
        targets.append((target, content))
    for target, content in targets:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    print(json.dumps(dict(restored_records=len(targets), inference_calls=0)))


if __name__ == "__main__":
    restore()
