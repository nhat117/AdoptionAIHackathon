"""Explicit audited recovery of local DNS failures; never retry attempted games.

Frozen inference files remain unchanged. This wrapper releases only reservations
for errno-8 name-resolution failures with no returned provider metadata, then
resumes unattempted jobs through the original frozen runner.
"""

import argparse
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "frozen_runner", Path(__file__).with_name("run.py")
)
frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen)
OriginalBudget = frozen.Budget


def reconcile(root):
    original = OriginalBudget(root)
    entries = [json.loads(x) for x in original.path.read_text().splitlines()]
    last_halt = max(
        (i for i, x in enumerate(entries) if x["type"] == "halt"), default=-1
    )
    last_resume = max(
        (i for i, x in enumerate(entries) if x["type"] == "resume_verified_dns"),
        default=-1,
    )
    if not original.pending:
        if last_resume > last_halt:
            original.halted = False
        return original
    verified = []
    for ticket in original.pending:
        game_id, call = ticket.rsplit(":", 1)
        folder = root / game_id
        manifest = json.loads((folder / "manifest.json").read_text())
        calls_path = folder / "calls.jsonl"
        calls = (
            [json.loads(x) for x in calls_path.read_text().splitlines()]
            if calls_path.exists()
            else []
        )
        metadata = [x for x in calls if x["type"] == "provider_metadata"]
        # This exact OS error means no hostname resolved and hence no connection
        # or HTTP request could be established. Timeouts/HTTP errors are excluded.
        if not (
            manifest["status"] == "failed"
            and manifest.get("error_type") == "URLError"
            and manifest.get("error")
            == "<urlopen error [Errno 8] nodename nor servname provided, or not known>"
            and len(metadata) == int(call) - 1
        ):
            raise RuntimeError("Reservation is not a proven pre-connect DNS failure")
        verified.append((ticket, manifest))
    for ticket, manifest in verified:
        frozen.append(
            original.path,
            dict(
                type="settle",
                ticket=ticket,
                cost=0,
                at=frozen.now(),
                reconciliation="verified_preconnect_dns",
                manifest=manifest,
            ),
        )
        original.pending.pop(ticket)
    frozen.append(
        original.path,
        dict(
            type="resume_verified_dns",
            at=frozen.now(),
            tickets=[x[0] for x in verified],
            wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            policy="Do not retry attempted games; continue untouched jobs only",
        ),
    )
    original.halted = False
    return original


class ReconciledBudget(OriginalBudget):
    def __init__(self, root):
        restored = reconcile(root)
        self.__dict__.update(restored.__dict__)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("runs/overnight-v1"))
    p.add_argument("--section", type=int, choices=[2, 3], required=True)
    p.add_argument("--env-file", type=Path, default=Path(".env"))
    args = p.parse_args()
    args.plan_only = False
    frozen.Budget = ReconciledBudget
    asyncio.run(frozen.main(args))
