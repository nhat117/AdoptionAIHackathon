"""Fixed rule for a message's stance toward the source claim (method fix 8).

Labels: agrees, disagrees, asks_proof, neutral. The machine signal decides when
it is Safe or Danger; only Unknown-signal messages fall back to text cues. The
rule is frozen before v3/v4 analysis and checked against hand labels with
reports/stance/label_messages.py agreement. It labels stated stance, never
private belief.
"""

import re

LABELS = ("agrees", "disagrees", "asks_proof", "neutral")
# Explicit requests for evidence only; "no evidence yet" or "unverified" is not a
# request. English plus draft Vietnamese cues, which await native review.
EVIDENCE = r"(evidence|proof|verif\w*|confirm\w*|authenticat\w*|bằng chứng|xác minh)"
PROOF_CUES = re.compile(
    r"\b(please|can you|could you|can anyone|would you)\b[^.?!]{0,60}"
    + EVIDENCE
    + r"|"
    + EVIDENCE
    + r"[^.?!]{0,40}\?"
    + r"|\b(how do you know|is this verified|is it verified)\b"
    + r"|(vui lòng|xin hãy|cho (tôi|mình) xem)[^.?!]{0,40}(bằng chứng|xác minh)"
    + r"|(bằng chứng|xác minh)[^.?!]{0,30}(không\s*\?|\?)",
    re.IGNORECASE,
)


def stance(message, claim):
    """Stance of one delivered message toward the source's claim."""
    if claim not in ("Safe", "Danger"):
        raise ValueError("Claim must be Safe or Danger")
    signal = message.get("signal")
    if signal == claim:
        return "agrees"
    if signal in ("Safe", "Danger"):
        return "disagrees"
    return "asks_proof" if PROOF_CUES.search(message.get("text", "")) else "neutral"


def cohen_kappa(a, b):
    """Agreement between two label lists beyond chance."""
    if len(a) != len(b) or not a:
        raise ValueError("Need two equal, nonempty label lists")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    expected = sum((a.count(k) / n) * (b.count(k) / n) for k in LABELS)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)
