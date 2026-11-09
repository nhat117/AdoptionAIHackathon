"""Prepare actual neutral-template native-review anchors without inventing sign-off."""

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "research/review_resolution/ROUND3_NATIVE_REVIEW.csv"


def rows(root=ROOT):
    inputs = [json.loads(x) for x in (root / "results/round3_neutral/inputs.jsonl").read_text().splitlines()]
    anchors = {(r["attack_type"], r["language"]): r for r in inputs if r["cluster"] == 40 and r["record_access"] == "correct"}
    result = []
    for attack in ("clean", "fake_current_record", "fake_stale_record"):
        en = anchors[attack, "en"]
        for language in ("vi", "zh"):
            local = anchors[attack, language]
            result.append({"review_id": f"round3-{attack}-{language}", "language": language, "attack_type": attack,
                           "english_prompt_id": en["trial_id"], "local_prompt_id": local["trial_id"],
                           "english_peer_text": en["peer_message"], "local_peer_text": local["peer_message"],
                           "source_peer_sha256": hashlib.sha256(local["peer_message"].encode()).hexdigest(),
                           "scope": "Actual assigned task-40 example; other tasks vary numeric values only. English is an anchor, not assumed gold.",
                           "review_status": "UNREVIEWED", "reviewer_name": "", "native_language_attestation": "",
                           "meaning_equivalence": "", "naturalness_1_to_5": "", "authority_equivalence": "",
                           "persuasive_strength_1_to_5": "", "review_date": "", "correction_or_notes": ""})
    return result


def main():
    expected = rows()
    if PATH.exists():
        with PATH.open(newline="") as stream:
            existing = list(csv.DictReader(stream))
        by_id = {r["review_id"]: r for r in existing}
        fixed = [k for k in expected[0] if k not in ("review_status", "reviewer_name", "native_language_attestation", "meaning_equivalence", "naturalness_1_to_5", "authority_equivalence", "persuasive_strength_1_to_5", "review_date", "correction_or_notes")]
        if len(by_id) != 6 or any(any(by_id.get(r["review_id"], {}).get(k) != r[k] for k in fixed) for r in expected):
            raise ValueError("Existing review anchors changed; preserve annotations and version manually")
        print("Existing Round 3 native-review sheet preserved; no sign-off inferred")
        return
    with PATH.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(expected[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(expected)
    print("Prepared 6 actual bilingual neutral-template anchors; all UNREVIEWED")


if __name__ == "__main__":
    main()
