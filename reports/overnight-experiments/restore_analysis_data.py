"""Restore published raw archives into a new directory, without inference calls."""

import argparse
import gzip
import json
from pathlib import Path

REPORT = Path(__file__).resolve().parent


def restore(destination):
    if destination.exists():
        raise ValueError(
            "Destination exists; choose a new directory to preserve records"
        )
    destination.mkdir(parents=True)
    groups = {
        "original": ["experiment-1", "experiment-2", "experiment-3"],
        "extensions": ["terra-comparison", "experiment-4", "experiment-5"],
    }
    count = 0
    for name, sections in groups.items():
        root = (destination / name).resolve()
        root.mkdir()
        for section in sections:
            with gzip.open(
                REPORT / section / "raw-records.jsonl.gz", "rt", encoding="utf-8"
            ) as f:
                for line in f:
                    record = json.loads(line)
                    target = (root / record["path"]).resolve()
                    if not target.is_relative_to(root) or target == root:
                        raise ValueError("Invalid archive path")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(record["content"], encoding="utf-8")
                    count += 1
        (root / "plan.json").write_bytes(
            (REPORT / sections[-1] / "plan.json").read_bytes()
        )
    print(
        json.dumps(
            dict(
                destination=str(destination.resolve()),
                archive_records=count,
                inference_calls=0,
            )
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--destination", type=Path, default=Path("runs/restored-review"))
    restore(p.parse_args().destination)
