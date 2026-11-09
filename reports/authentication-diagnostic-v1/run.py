"""Default dry run. Paid preflight/diagnostics require explicit fresh authorization."""

import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from swarm_lab.evacuation.language import validate

HERE = Path(__file__).resolve().parent
ROOT = Path("runs/authentication-diagnostic-v1")
spec = importlib.util.spec_from_file_location("diagnostic_prepare", HERE / "prepare.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(prepare.canonical(value).encode()).hexdigest()


def append(path, row):
    with path.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def records(path):
    return (
        [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
    )


def frozen():
    plan = json.loads((HERE / "plan.json").read_text())
    for path, expected in plan["source_sha256"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError("Frozen source changed: " + path)
    rows = records(Path(plan["cases_path"]))
    return plan, {r["id"]: r for r in rows}


def validate_response(data, view):
    if not isinstance(data, dict) or set(data) != set(prepare.SCHEMA["required"]):
        raise ValueError("Wrong diagnostic fields")
    validate({k: data[k] for k in ["signal", "action", "message", "parents"]}, view)
    if data["evidence_status"] not in ["verified", "unverified", "none"]:
        raise ValueError("Invalid evidence status")
    if data["verified_signal"] not in ["Danger", "Safe", "Unknown"]:
        raise ValueError("Invalid verified signal")
    return data


class Budget:
    def __init__(self, root, cap):
        self.path, self.cap = root / "budget.jsonl", cap
        self.spent, self.pending, self.halted = 0.0, {}, False
        for row in records(self.path):
            if row["type"] == "reserve":
                if row["ticket"] in self.pending:
                    raise ValueError("Duplicate reservation")
                self.pending[row["ticket"]] = row["usd"]
            elif row["type"] == "settle":
                self.pending.pop(row["ticket"])
                self.spent += row["cost"]
            elif row["type"] == "halt":
                self.halted = True
        self.halted |= bool(self.pending)
        if self.spent + sum(self.pending.values()) > cap:
            raise ValueError("Existing ledger exceeds fresh cap")

    def reserve(self, ticket, amount):
        if ticket in self.pending or not math.isfinite(amount) or amount <= 0:
            raise ValueError("Invalid/duplicate reservation")
        if self.halted or self.spent + sum(self.pending.values()) + amount > self.cap:
            raise RuntimeError("Budget guard: cap or unresolved billing")
        self.pending[ticket] = amount
        append(self.path, dict(type="reserve", ticket=ticket, usd=amount, at=now()))

    def settle(self, ticket, cost):
        if (
            not isinstance(cost, (int, float))
            or not math.isfinite(cost)
            or not (0 <= cost <= self.pending[ticket])
        ):
            raise ValueError("Invalid/over-reservation billed cost")
        self.pending.pop(ticket)
        self.spent += cost
        append(self.path, dict(type="settle", ticket=ticket, cost=cost, at=now()))

    def halt(self, reason):
        self.halted = True
        append(self.path, dict(type="halt", reason=reason, at=now()))


def review_admission(path, plan, model, root=None):
    root = ROOT if root is None else root
    if path is None:
        raise ValueError("Diagnostic phase requires independent preflight review")
    review = json.loads(path.read_text())
    if review.get("verdict") != "proceed" or review.get("plan_sha256") != digest(plan):
        raise ValueError("Review verdict/plan mismatch")
    if model not in review.get("admitted_models", []):
        raise ValueError("Configuration not admitted by technical review")
    preflight = [
        j for j in plan["jobs"] if j["model"] == model and j["phase"] == "preflight"
    ]
    if len(preflight) != 2:
        raise ValueError("Expected two frozen preflight jobs")
    for job in preflight:
        manifest = root / job["id"] / "manifest.json"
        if (
            not manifest.exists()
            or json.loads(manifest.read_text())["status"] != "valid"
        ):
            raise ValueError("Technical preflight is incomplete or failed")
        m = json.loads(manifest.read_text())
        case = next(
            r for r in records(Path(plan["cases_path"])) if r["id"] == job["case"]
        )
        folder = manifest.parent
        request = folder / "request.json"
        response = folder / "response.json"
        if (
            json.loads(request.read_text())
            != prepare.payload(case, job["wording"], plan["models"][model])
            or hashlib.sha256(request.read_bytes()).hexdigest() != m["request_sha256"]
        ):
            raise ValueError("Preflight request changed")
        if hashlib.sha256(response.read_bytes()).hexdigest() != m["response_sha256"]:
            raise ValueError("Preflight response changed")
        if (
            review["receipt_sha256"].get(job["id"])
            != hashlib.sha256(manifest.read_bytes()).hexdigest()
        ):
            raise ValueError("Preflight receipt changed since review")


def main(args):
    plan, cases = frozen()
    selected = [
        j
        for j in plan["jobs"]
        if j["phase"] == args.phase and (args.model is None or j["model"] == args.model)
    ]
    if not args.execute:
        print(
            json.dumps(
                dict(
                    mode="dry_run",
                    selected=len(selected),
                    planned=len(plan["jobs"]),
                    inference_calls=0,
                    note="No credentials read or network requests made",
                )
            )
        )
        return
    if args.cap_usd is None or not math.isfinite(args.cap_usd) or args.cap_usd <= 0:
        raise ValueError("Execution requires an explicitly authorized fresh --cap-usd")
    ROOT.mkdir(parents=True, exist_ok=True)
    lock = (ROOT / "collector.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    run_plan = dict(plan_sha256=digest(plan), cap_usd=args.cap_usd)
    path = ROOT / "run-plan.json"
    if path.exists() and json.loads(path.read_text()) != run_plan:
        raise ValueError("Existing plan/cap differs; do not reset the ledger")
    path.write_text(json.dumps(run_plan, indent=2))
    budget = Budget(ROOT, args.cap_usd)
    if budget.halted:
        raise ValueError("Ledger halted; independent billing review required")
    admission_sha = None
    if args.phase == "diagnostic":
        for model in {j["model"] for j in selected}:
            review_admission(args.preflight_review, plan, model)
        review_bytes = args.preflight_review.read_bytes()
        admission_sha = hashlib.sha256(review_bytes).hexdigest()
        admission_path = ROOT / ("admission-" + admission_sha + ".json")
        if admission_path.exists() and admission_path.read_bytes() != review_bytes:
            raise ValueError("Saved admission differs")
        admission_path.write_bytes(review_bytes)
    load_dotenv()
    key = os.environ["OPENROUTER_API_KEY"]
    for job in selected:
        folder = ROOT / job["id"]
        if folder.exists():
            continue  # No failed or valid request is retried.
        config, case = plan["models"][job["model"]], cases[job["case"]]
        body = prepare.payload(case, job["wording"], config)
        encoded = json.dumps(body, ensure_ascii=False).encode()
        if len(encoded) > plan["input_byte_cap"]:
            raise ValueError("Prepared input byte cap exceeded before dispatch")
        # Do not create an attempted cell when no reservation is possible.
        if budget.spent + config["reservation_usd"] > args.cap_usd:
            budget.halt("budget_limit")
            break
        folder.mkdir()
        manifest = dict(
            job,
            status="running",
            started_at=now(),
            plan_sha256=digest(plan),
            request_sha256=hashlib.sha256(encoded).hexdigest(),
            low="requested; not equal compute across models",
        )
        if admission_sha is not None:
            manifest["admission_review_sha256"] = admission_sha
        receipt = folder / "manifest.json"
        receipt.write_text(json.dumps(manifest, indent=2))
        (folder / "request.json").write_bytes(encoded)  # Never save auth headers.
        ticket = job["id"]
        budget.reserve(ticket, config["reservation_usd"])
        try:
            request = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=encoded,
                headers={
                    "Authorization": "Bearer " + key,
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.load(response)
            response_path = folder / "response.json"
            response_path.write_text(json.dumps(result, indent=2))
            manifest["response_sha256"] = hashlib.sha256(
                response_path.read_bytes()
            ).hexdigest()
            budget.settle(ticket, (result.get("usage") or {}).get("cost"))
            if (
                result.get("model") != config["model"]
                or result.get("provider") != (config["returned_provider"])
            ):
                budget.halt("model/provider mismatch")
                raise ValueError("Unexpected returned model/provider")
            choices = result.get("choices") or []
            if not choices or choices[0].get("finish_reason") != "stop":
                raise ValueError("No normal completed response")
            raw = choices[0].get("message", {}).get("content")
            if not isinstance(raw, str):
                raise ValueError("Missing response content")
            parsed = validate_response(json.loads(raw), case["view"])
            (folder / "decision.json").write_text(json.dumps(parsed, indent=2))
            manifest["status"] = "valid"  # Technical validity, never gold correctness.
        except Exception as exc:
            manifest.update(
                status="failed", error_type=type(exc).__name__, error=str(exc)[:240]
            )
            if ticket in budget.pending:
                if isinstance(exc, urllib.error.URLError) and isinstance(
                    exc.reason, socket.gaierror
                ):
                    budget.settle(ticket, 0)
                    manifest["reconciliation"] = "verified_preconnect_dns"
                else:
                    budget.halt("uncertain billing or invalid cost")
        manifest["finished_at"] = now()
        receipt.write_text(json.dumps(manifest, indent=2))
        print(job["id"], manifest["status"], f"spent=${budget.spent:.6f}", flush=True)
        if budget.halted:
            break
    print(
        json.dumps(
            dict(
                spent_usd=budget.spent,
                pending=budget.pending,
                halted=budget.halted,
                cap_usd=args.cap_usd,
            )
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase", choices=["preflight", "diagnostic"], default="preflight"
    )
    parser.add_argument("--model", choices=[c[0] for c in prepare.CHOICES])
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--cap-usd", type=float)
    parser.add_argument("--preflight-review", type=Path)
    main(parser.parse_args())
