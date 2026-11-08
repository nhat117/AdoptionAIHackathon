"""Syntactic checks only: generated text still requires semantic review."""

import hashlib
import json
from pathlib import Path


def parse_object(raw):
    text = raw.strip()
    if text.startswith("```json\n") and text.endswith("\n```"):
        text = text[8:-4].strip()
    return json.loads(text)


def validate_pair(pair):
    if not isinstance(pair, dict) or set(pair) != {"safe_message", "danger_message"}:
        raise ValueError("Expected exactly two message fields")
    for message in pair.values():
        if not isinstance(message, str) or not 8 <= len(message.split()) <= 30:
            raise ValueError("Each English message must have 8--30 words")
        if "http" in message.lower() or "\n" in message:
            raise ValueError("No URLs or multiline instructions in messages")
    if pair["safe_message"] == pair["danger_message"]:
        raise ValueError("Safe and Danger messages must differ")
    return pair


def load_stimulus(path: Path, index: int, split: str, allow_unreviewed=False):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    row = rows[index]
    pair = validate_pair({k: row[k] for k in ("safe_message", "danger_message")})
    if row.get("review_status") != "approved":
        if split != "calibration" or not allow_unreviewed:
            raise ValueError("Unreviewed stimuli are calibration-only with opt-in")
    return pair


def convert(source: Path, target: Path):
    """Retain rejected rows in a sidecar; never silently repair generated content."""
    accepted, rejected, seen = [], [], set()
    for index, line in enumerate(source.read_text().splitlines()):
        try:
            row = json.loads(line)
            completion = row["completion"]
            pair = validate_pair(parse_object(completion))
            digest = hashlib.sha256(
                json.dumps(pair, sort_keys=True).encode()
            ).hexdigest()
            if digest in seen:
                raise ValueError("Duplicate pair")
            seen.add(digest)
            accepted.append(
                {
                    "id": digest[:16],
                    **pair,
                    "review_status": "pending",
                    "source_row": index,
                }
            )
        except (ValueError, KeyError, TypeError) as exc:
            rejected.append({"source_row": index, "reason": str(exc)})
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x") as stream:
        stream.write("".join(json.dumps(r) + "\n" for r in accepted))
    target.with_suffix(".rejected.json").write_text(json.dumps(rejected, indent=2))
    return len(accepted), len(rejected)
