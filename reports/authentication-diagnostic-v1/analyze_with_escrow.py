"""Versioned provisional audit: unchanged science, explicit unresolved escrow."""

import argparse
import fcntl
import hashlib
import importlib.util
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("diagnostic_run", HERE / "run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


ESCROW_AUDIT = True


def escrow_guard():
    spec = importlib.util.spec_from_file_location(
        "escrow_audit_guard", HERE / "collect_with_escrow.py"
    )
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    return guard


def approved_escrow(root):
    markers = [
        r
        for r in run.records(root / "budget.jsonl")
        if r["type"] == "operational_escrow_resume"
    ]
    if len(markers) != 1:
        raise ValueError("Expected one reviewed operational resume marker")
    marker = markers[0]
    review_sha = marker["review_sha256"]
    if len(review_sha) != 64 or any(c not in "0123456789abcdef" for c in review_sha):
        raise ValueError("Invalid escrow approval hash")
    approval = root / ("escrow-review-" + review_sha + ".json")
    raw = approval.read_bytes()
    if hashlib.sha256(raw).hexdigest() != review_sha:
        raise ValueError("Escrow approval hash mismatch")
    review = json.loads(raw)
    run_plan = json.loads((root / "run-plan.json").read_text())
    if run_plan != {"plan_sha256": review["plan_sha256"], "cap_usd": 25}:
        raise ValueError("Run plan/cap differs from approved escrow")
    wrapper = root / ("escrow-wrapper-" + review["wrapper_sha256"] + ".py")
    if hashlib.sha256(wrapper.read_bytes()).hexdigest() != review["wrapper_sha256"]:
        raise ValueError("Approved wrapper copy missing or changed")
    guard = escrow_guard()
    ticket = guard.check(review, root, 25)
    if (
        marker.get("pending_ticket") != ticket
        or marker.get("pending_usd") != review["escrow_usd"]
    ):
        raise ValueError("Resume marker differs from approval")
    if any(
        json.loads(p.read_text())["status"] == "running"
        for p in root.glob("*/manifest.json")
    ):
        raise ValueError("Cannot audit active collection")
    return {ticket: review["escrow_usd"]}, review_sha


def sign_flip(differences):
    if not differences:
        return None
    observed = abs(sum(differences))
    return sum(
        abs(sum(s * d for s, d in zip(signs, differences))) >= observed - 1e-12
        for signs in itertools.product([-1, 1], repeat=len(differences))
    ) / (2 ** len(differences))


def analyze(root, locked_file=None):
    lock = locked_file or (root / "collector.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    escrow, review_sha = approved_escrow(root)
    plan, cases = run.frozen()
    run_plan = root / "run-plan.json"
    if run_plan.exists():
        receipt = json.loads(run_plan.read_text())
        if receipt["plan_sha256"] != run.digest(plan):
            raise ValueError("Run plan differs from prepared plan")
    elif root.exists() and any(root.glob("*/manifest.json")):
        raise ValueError("Missing run plan")
    jobs = {j["id"]: j for j in plan["jobs"]}
    if {p.parent.name for p in root.glob("*/manifest.json")} - set(jobs):
        raise ValueError("Unplanned job")
    rows, missing, billed = [], [], 0.0
    for job in plan["jobs"]:
        folder = root / job["id"]
        path = folder / "manifest.json"
        if not path.exists():
            missing.append(dict(id=job["id"], status="unattempted"))
            continue
        m = json.loads(path.read_text())
        if any(m.get(k) != value for k, value in job.items()) or (
            m["plan_sha256"] != run.digest(plan)
        ):
            raise ValueError("Manifest differs from frozen job")
        if job["phase"] == "diagnostic":
            admission_sha = m.get("admission_review_sha256", "")
            if len(admission_sha) != 64 or any(
                c not in "0123456789abcdef" for c in admission_sha
            ):
                raise ValueError("Missing admission review hash")
            approval = root / ("admission-" + admission_sha + ".json")
            if (
                not approval.exists()
                or run.hashlib.sha256(approval.read_bytes()).hexdigest()
                != admission_sha
            ):
                raise ValueError("Admission review missing or changed")
            run.review_admission(approval, plan, job["model"], root=root)
        case, config = cases[job["case"]], plan["models"][job["model"]]
        request = json.loads((folder / "request.json").read_text())
        if request != run.prepare.payload(case, job["wording"], config):
            raise ValueError("Request differs from frozen input")
        if (
            run.hashlib.sha256((folder / "request.json").read_bytes()).hexdigest()
            != (m["request_sha256"])
        ):
            raise ValueError("Request hash mismatch")
        response_path = folder / "response.json"
        response = (
            json.loads(response_path.read_text()) if response_path.exists() else {}
        )
        if response_path.exists() and run.hashlib.sha256(
            response_path.read_bytes()
        ).hexdigest() != m.get("response_sha256"):
            raise ValueError("Response hash mismatch")
        cost = (response.get("usage") or {}).get("cost", 0)
        if (
            not isinstance(cost, (int, float))
            or not run.math.isfinite(cost)
            or cost < 0
        ):
            raise ValueError("Invalid provider cost")
        billed += cost
        if m["status"] != "valid":
            missing.append(dict(id=job["id"], status=m["status"], error=m.get("error")))
            continue
        if (
            response.get("model") != config["model"]
            or response.get("provider") != (config["returned_provider"])
            or response["choices"][0]["finish_reason"] != "stop"
        ):
            raise ValueError("Returned route/finish mismatch")
        decision = run.validate_response(
            json.loads(response["choices"][0]["message"]["content"]), case["view"]
        )
        if decision != json.loads((folder / "decision.json").read_text()):
            raise ValueError("Saved decision differs from raw response")
        verified = case["gold"]["evidence_status"] == "verified"
        rows.append(
            dict(
                **job,
                split=case["split"],
                template=case["template"],
                condition=case["condition"],
                truth=case["truth"],
                action=decision["action"],
                reported_status=decision["evidence_status"],
                reported_verified_signal=decision["verified_signal"],
                reported_signal=decision["signal"],
                recognition=int(all(decision[k] == v for k, v in case["gold"].items())),
                false_verification=int(
                    not verified
                    and (
                        decision["evidence_status"] == "verified"
                        or decision["verified_signal"] != "Unknown"
                    )
                ),
                missed_verification=int(
                    verified
                    and not all(decision[k] == v for k, v in case["gold"].items())
                ),
                verified_action_correct=int(
                    (decision["action"] == "evacuate") == (case["truth"] == "Danger")
                )
                if verified
                else None,
                cost_usd=cost,
            )
        )
    pending, spent, maximum = {}, 0.0, 0.0
    for entry in run.records(root / "budget.jsonl"):
        if entry["type"] == "reserve":
            if entry["ticket"] in pending:
                raise ValueError("Duplicate ledger ticket")
            pending[entry["ticket"]] = entry["usd"]
        elif entry["type"] == "settle":
            reserved = pending.pop(entry["ticket"])
            cost = entry["cost"]
            if (
                not isinstance(cost, (int, float))
                or not run.math.isfinite(cost)
                or not (0 <= cost <= reserved)
            ):
                raise ValueError("Invalid settlement")
            spent += cost
        maximum = max(maximum, spent + sum(pending.values()))
    if pending != escrow:
        raise ValueError("Unapproved unresolved billing; approval withheld")
    if abs(spent - billed) > 1e-8:
        raise ValueError("Raw billing differs from ledger")
    if run_plan.exists() and maximum > receipt["cap_usd"] + 1e-8:
        raise ValueError("Fresh budget exceeded")
    groups = defaultdict(list)
    for row in rows:
        groups[row["model"], row["split"], row["condition"], row["wording"]].append(row)
    rates = [
        dict(
            model=k[0],
            split=k[1],
            condition=k[2],
            wording=k[3],
            calls=len(rs),
            action_distribution=dict(Counter(r["action"] for r in rs)),
            reported_status_distribution=dict(
                Counter(r["reported_status"] for r in rs)
            ),
            recognition=mean(r["recognition"] for r in rs),
            false_verification=mean(r["false_verification"] for r in rs),
            missed_verification=mean(r["missed_verification"] for r in rs),
        )
        for k, rs in sorted(groups.items())
    ]
    contrasts = []
    heldout = [r for r in rows if r["split"] == "heldout"]
    for model in plan["models"]:
        for condition in run.prepare.CONDITIONS:
            pairs = []
            for seed in range(3000, 3008):
                values = [
                    [
                        r["recognition"]
                        for r in heldout
                        if r["model"] == model
                        and r["condition"] == condition
                        and r["template"] == seed
                        and r["wording"] == w
                    ]
                    for w in ["current", "clarified"]
                ]
                if all(len(v) == 2 for v in values):
                    pairs.append(
                        dict(
                            seed=seed,
                            current=mean(values[0]),
                            clarified=mean(values[1]),
                        )
                    )
            diffs = [p["clarified"] - p["current"] for p in pairs]
            nonzero = sum(abs(d) > 1e-12 for d in diffs)
            contrasts.append(
                dict(
                    model=model,
                    condition=condition,
                    seeds=len(pairs),
                    per_seed=pairs,
                    mean_difference=mean(diffs) if diffs else None,
                    p_unadjusted=sign_flip(diffs),
                    conditional_min_p=min(1, 2 / 2**nonzero) if diffs else None,
                    status="exploratory" if len(pairs) >= 6 else "inconclusive",
                )
            )
    # Holm adjustment across six held-out recognition contrasts within each model.
    for model in plan["models"]:
        family = sorted(
            [
                c
                for c in contrasts
                if c["model"] == model and c["p_unadjusted"] is not None
            ],
            key=lambda c: c["p_unadjusted"],
        )
        running = 0
        for i, c in enumerate(family):
            running = max(running, min(1, (6 - i) * c["p_unadjusted"]))
            c["p_holm_within_model"] = running
    return dict(
        mode="prepared_no_inference"
        if not rows and not run_plan.exists()
        else "collected_under_escrow",
        planned=len(jobs),
        technically_valid=len(rows),
        failed_or_unattempted=missing,
        rows=rows,
        rates=rates,
        paired_wording_contrasts=contrasts,
        budget=dict(
            spent_usd=spent,
            max_exposure_usd=maximum,
            pending=pending,
            unresolved_escrow_usd=sum(pending.values()),
            current_accounted_exposure_usd=spent + sum(pending.values()),
            billing_status="unresolved",
            escrow_review_sha256=review_sha,
            audit_version="analyze_with_escrow.py",
        ),
        unit="seed template; discovery/preflight separate; not network results",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=run.ROOT)
    parser.add_argument(
        "--out", type=Path, default=Path("/tmp/auth-diagnostic-audit.json")
    )
    args = parser.parse_args()
    summary = analyze(args.root)
    args.out.write_text(json.dumps(summary, indent=2))
    print(
        json.dumps(
            {k: summary[k] for k in ["mode", "planned", "technically_valid", "budget"]}
        )
    )
