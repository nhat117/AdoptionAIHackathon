"""Research-only gate ablation; not a replacement for trusted output rendering.

Accepted candidates are preserved so semantic rejection is not confused with
rewriting or recovery. Arbitrary prose outside the supported fields is not
certified; production should continue using the existing projected release path.
"""

import hashlib
import json
import re

from ai2ai_guard import ReportGuard
from ai2ai_guard.fact_projection import ProjectedFactsGuard
from ai2ai_injection.evaluator import strict_json


def parse_candidate(raw, *, normalize_fence):
    if not isinstance(raw, str) or len(raw) > 65536:
        return None, "", False
    text, transformed = raw.strip(), False
    if normalize_fence:
        match = re.fullmatch(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text, flags=re.I)
        if match:
            text, transformed = match.group(1), True
    try:
        value = strict_json(text)
    except (ValueError, TypeError, RecursionError):
        return None, text, transformed
    return value, text, transformed


def ablation_check(raw, task, *, normalize_fence, semantic):
    """Both arms receive the same task/registry; only use of fact rules changes."""
    value, text, transformed = parse_candidate(raw, normalize_fence=normalize_fence)
    base = ReportGuard().check(text, task)
    reasons = list(base.reasons)
    if base.allowed and semantic:
        reasons += ProjectedFactsGuard().check(text, task).reasons
    allowed = base.allowed and not reasons
    return {
        "allowed": allowed,
        "reasons": reasons,
        "normalization_applied": transformed,
        "candidate_sha256": hashlib.sha256(raw.encode()).hexdigest()
        if isinstance(raw, str)
        else None,
        "released_object": value if allowed else None,
        "released_object_sha256": hashlib.sha256(
            json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        if allowed
        else None,
        "recovery_calls": 0,
        "rendered_from_registry": False,
    }


def all_checks(raw, task):
    return {
        f"{'normalized' if normalized else 'strict'}_{'semantic' if semantic else 'structural'}": ablation_check(
            raw, task, normalize_fence=normalized, semantic=semantic
        )
        for normalized in (False, True)
        for semantic in (False, True)
    }
