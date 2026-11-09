"""Restore v3 raw records and prior budget ledgers without replacing data."""

import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = Path(__file__).with_name("raw-records.jsonl.gz")


def restore():
    with gzip.open(ARCHIVE, "rt", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    targets = []
    for row in rows:
        relative = Path(row["path"])
        target = (ROOT / relative).resolve()
        if not target.is_relative_to(ROOT / "runs") or relative.is_absolute():
            raise ValueError("Archive path outside runs")
        if target.exists() and target.read_text() != row["content"]:
            raise ValueError(
                "Existing record differs; refusing overwrite: " + str(target)
            )
        targets.append((target, row["content"]))
    for target, content in targets:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    print(json.dumps(dict(records=len(targets), inference_calls=0)))


if __name__ == "__main__":
    restore()
