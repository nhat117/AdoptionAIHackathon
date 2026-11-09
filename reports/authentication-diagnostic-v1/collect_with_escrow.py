"""Proposed operational amendment: retain reviewed escrow, never erase a halt.

Default is the original zero-inference dry run. Execution requires a separate
independent approval bound to this file, the failed request and ledger prefix.
This does not reconcile billing or make the frozen analyzer accept pending cost.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("escrow_frozen_run", HERE / "run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
OriginalBudget = run.Budget


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(review, root, cap):
    plan, cases = run.frozen()
    if (
        review.get("verdict") != "proceed_under_escrow"
        or review.get("plan_sha256") != run.digest(plan)
        or review.get("wrapper_sha256") != sha(Path(__file__).read_bytes())
        or review.get("cap_usd") != cap
        or cap != 25
    ):
        raise ValueError("Missing or mismatched independent escrow approval")
    data = (root / "budget.jsonl").read_bytes()
    length = review["ledger_prefix_bytes"]
    if (
        not isinstance(length, int)
        or length <= 0
        or len(data) < length
        or sha(data[:length]) != review["ledger_prefix_sha256"]
        or not data[:length].endswith(b"\n")
    ):
        raise ValueError("Approved ledger prefix changed")
    rows = run.records(root / "budget.jsonl")
    halts = [run.digest(r) for r in rows if r["type"] == "halt"]
    if halts != review.get("covered_halt_sha256") or len(halts) != 1:
        raise ValueError("Uncovered or unexpected halt; stop again")
    ticket = review["escrow_ticket"]
    job = next(j for j in plan["jobs"] if j["id"] == ticket)
    folder = root / ticket
    manifest_bytes = (folder / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if (
        sha(manifest_bytes) != review["failed_manifest_sha256"]
        or manifest["status"] != "failed"
        or manifest.get("error") != "HTTP Error 429: Too Many Requests"
        or (folder / "response.json").exists()
    ):
        raise ValueError("Failed HTTP429 receipt differs from review")
    admission_sha = manifest.get("admission_review_sha256")
    if admission_sha != review.get("admission_review_sha256"):
        raise ValueError("Admission review differs from escrow approval")
    run.review_admission(
        root / ("admission-" + admission_sha + ".json"), plan, job["model"], root=root
    )
    request = (folder / "request.json").read_bytes()
    if (
        sha(request) != review["failed_request_sha256"]
        or sha(request) != manifest["request_sha256"]
        or json.loads(request)
        != run.prepare.payload(
            cases[job["case"]], job["wording"], plan["models"][job["model"]]
        )
    ):
        raise ValueError("Failed request differs from frozen payload/review")
    if review.get("escrow_usd") != plan["models"][job["model"]]["reservation_usd"]:
        raise ValueError("Escrow must retain the original full reservation")
    return ticket


def budget_class(review_path):
    review_bytes = review_path.read_bytes()
    review = json.loads(review_bytes)
    review_sha = sha(review_bytes)

    class EscrowBudget(OriginalBudget):
        def __init__(self, root, cap):
            super().__init__(root, cap)
            self.root = root
            ticket = check(review, root, cap)
            if self.pending != {ticket: review["escrow_usd"]}:
                raise ValueError("Unexpected unresolved reservation; stop")
            # Original main already holds the exclusive collector lock here.
            approval = root / ("escrow-review-" + review_sha + ".json")
            if approval.exists() and approval.read_bytes() != review_bytes:
                raise ValueError("Saved escrow review changed")
            if not approval.exists():
                approval.write_bytes(review_bytes)
                run.append(
                    self.path,
                    dict(
                        type="operational_escrow_resume",
                        review_sha256=review_sha,
                        pending_ticket=ticket,
                        pending_usd=review["escrow_usd"],
                        at=run.now(),
                        note="Billing unresolved; reservation retained in exposure",
                    ),
                )
            # Only this reviewed historical stop is covered. Pending cost remains
            # in every original reserve guard; all new halts still stop main.
            self.halted = False

        def reserve(self, ticket, amount):
            if self.spent + sum(self.pending.values()) + amount > self.cap:
                # Frozen main creates its running manifest before reserve().
                # Make an escrow-aware denial explicitly non-dispatched.
                path = self.root / ticket / "manifest.json"
                if path.exists():
                    manifest = json.loads(path.read_text())
                    manifest.update(
                        status="blocked_before_dispatch",
                        finished_at=run.now(),
                        error="Escrow-inclusive budget denied before network dispatch",
                    )
                    path.write_text(json.dumps(manifest, indent=2))
                self.halt("escrow_budget_limit_before_dispatch")
                raise RuntimeError("Escrow-inclusive cap; no request dispatched")
            super().reserve(ticket, amount)

    return EscrowBudget


def main(args):
    if args.execute:
        if args.review is None:
            raise ValueError("Execution requires independent escrow approval")
        run.Budget = budget_class(args.review)
    run.main(
        argparse.Namespace(
            execute=args.execute,
            cap_usd=25,
            phase="diagnostic",
            model=None,
            preflight_review=HERE / "preflight-review.json",
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--review", type=Path)
    main(parser.parse_args())
