"""Verify supported fields, then render release text exclusively from trusted data.

Model prose is not released or semantically certified. This deliberately limits
the product to a fixed administrative report rather than arbitrary summaries.
"""

import hashlib
import json
import re

from ai2ai_guard import GateDecision, ProtectedResult, ReportGuard
from ai2ai_guard.facts import fact_messages


class ProjectedFactsGuard:
    def check(self, raw, task):
        original = ReportGuard().check(raw, task)
        if not original.allowed:
            return original
        summary = original.report["public_summary"]
        patterns = {
            "budget": r"\bBudget\s*:\s*([0-9]+(?:,[0-9]{3})*)\b",
            "risk": r"\bRisk\s*:\s*(low|medium|high)\b",
            "deadline": r"\bDeadline\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\b",
        }
        reasons = []
        for field, pattern in patterns.items():
            values = re.findall(pattern, summary, flags=re.I)
            if len(values) != 1:
                reasons.append("missing_or_ambiguous_" + field)
                continue
            value = (
                int(values[0].replace(",", ""))
                if field == "budget"
                else values[0].lower()
            )
            if (
                type(value) is not type(task["facts"].get(field))
                or value != task["facts"][field]
            ):
                reasons.append("unsupported_" + field)
        if reasons:
            return GateDecision(False, reasons)
        # Every released value comes from the caller-owned record. In particular,
        # unchecked model prose, novel encodings and contradictory clauses vanish.
        facts = task["facts"]
        report = {
            "task_id": task["task_id"],
            "status": task["status"],
            "public_summary": f"The {task['topic']} is {task['status']}. "
            f"Budget: {facts['budget']}; Risk: {facts['risk']}; "
            f"Deadline: {facts['deadline']}; {task['milestone']}",
        }
        verified = ReportGuard().check(json.dumps(report), task)
        return verified


def projected_fact_report(task, annotations, target, *, retry_trusted=True):
    gate = ProjectedFactsGuard()
    audit = []
    for attempt in range(2 if retry_trusted else 1):
        try:
            response = target.chat(
                fact_messages(task, annotations if not attempt else []), None
            )
            raw = response["content"]
            decision = gate.check(raw, task)
            audit.append(
                {
                    "attempt": attempt + 1,
                    "trusted_only_retry": bool(attempt),
                    "candidate_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    "allowed": decision.allowed,
                    "reasons": decision.reasons,
                    "release_mode": "trusted_record_projection",
                }
            )
            if decision.allowed:
                audit[-1]["released_sha256"] = hashlib.sha256(
                    json.dumps(decision.report, sort_keys=True).encode()
                ).hexdigest()
                return ProtectedResult(True, decision.report, attempt + 1, audit)
        except Exception as error:
            audit.append(
                {
                    "attempt": attempt + 1,
                    "trusted_only_retry": bool(attempt),
                    "reasons": ["generation_error_" + type(error).__name__],
                }
            )
    return ProtectedResult(False, None, len(audit), audit)
