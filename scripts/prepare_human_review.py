"""Prepare unfilled native-speaker forms. Never creates human review or authorship."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "research/review_resolution/NATIVE_REVIEW_PACKET.csv"


def rows(root=ROOT):
    words = json.loads((root / "configs/authority-wording-v2.json").read_text())
    clean = json.loads((root / "configs/authority-followup-v1.json").read_text())["clean_wordings"]
    result = []
    for language in ("vi", "zh"):
        for authority in range(4):
            for variant in range(3):
                role = words["roles"][language][authority]
                enrole = words["roles"]["en"][authority]
                result.append({
                    "review_id": f"native-{language}-a{authority}-w{variant}",
                    "language": language, "authority": authority, "wording": variant,
                    "english_attack": words["wordings"]["en"][variant].format(role=enrole, budget=35800),
                    "local_attack": words["wordings"][language][variant].format(role=role, budget=35800),
                    "english_clean": clean["en"][variant].format(role=enrole),
                    "local_clean": clean[language][variant].format(role=role),
                    "amount_note": "35800 is a review-display placeholder, not an observed experiment result",
                    "native_language_attestation": "", "meaning_equivalence_pass_fail_uncertain": "",
                    "naturalness_1_to_5": "", "perceived_authority_1_to_5": "",
                    "persuasive_force_1_to_5": "", "reviewer_name": "", "review_date": "",
                    "proposed_correction_or_notes": "",
                })
    return result


def main():
    expected = rows()
    if PATH.exists():
        with PATH.open(newline="") as stream:
            observed = list(csv.DictReader(stream))
        if len(observed) != len(expected):
            raise ValueError("Human packet changed; never overwrite completed review")
        by_id = {row["review_id"]: row for row in observed}
        if len(by_id) != len(observed):
            raise ValueError("Duplicate human review IDs; packet preserved for manual repair")
        fixed = [key for key, value in expected[0].items() if value != ""]
        for template in expected:
            saved = by_id.get(template["review_id"], {})
            if any(saved.get(key) != str(template[key]) for key in fixed):
                raise ValueError("Review anchors changed; create a new version, never overwrite annotations")
        print(json.dumps({"status": "existing_packet_preserved", "rows": len(observed)}))
        return
    with PATH.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(expected[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(expected)
    print(json.dumps({"status": "UNREVIEWED_TEMPLATE", "rows": len(expected), "human_validation_created": False}))


if __name__ == "__main__":
    main()
