"""Resume only saved expansion inputs; never reselect tasks after new runs exist."""

import argparse
import hashlib
import json
from pathlib import Path

from run_oversight_ablation import trial

from ai2ai_injection.adaption_provider import AdaptionClient, load_key
from ai2ai_injection.pacing import RequestPacer
from ai2ai_injection.runner import collect

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "runs/oversight-expansion-v2"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    spec = json.loads((FOLDER / "FROZEN_PROTOCOL.json").read_text())["spec"]
    raw = (FOLDER / "inputs.jsonl").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == spec["inputs_sha256"]
    for name, expected in spec["source_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    cases = [json.loads(line) for line in raw.decode().splitlines()]
    saved = FOLDER / "trials.jsonl"
    rows = (
        [json.loads(line) for line in saved.read_text().splitlines()]
        if saved.exists()
        else []
    )
    done = {r["trial_id"] for r in rows}
    assert len(done) == len(rows)
    assert done <= {c["trial_id"] for c in cases}
    missing = [c for c in cases if c["trial_id"] not in done]
    print(f"Frozen cases: {len(cases)}; retained: {len(rows)}; missing: {len(missing)}")
    if not args.run or not missing:
        return
    client = AdaptionClient(
        spec["model"],
        load_key("adaption"),
        max_output_tokens=spec["max_output_tokens"],
        pacer=RequestPacer(interval=2),
    )
    try:
        collect(saved, cases, trial, client, 3)
    finally:
        client.close()


if __name__ == "__main__":
    main()
