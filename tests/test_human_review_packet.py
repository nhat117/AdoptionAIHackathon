import csv
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_packet_has_blank_human_signoffs_and_bilingual_anchors():
    module = runpy.run_path(str(ROOT / "scripts/prepare_human_review.py"))
    rows = module["rows"]()
    assert len(rows) == 24
    assert len({r["review_id"] for r in rows}) == 24
    assert all(r["reviewer_name"] == r["native_language_attestation"] == ""
               for r in rows)
    assert all(r["english_attack"] and r["local_attack"] for r in rows)


def test_packet_generation_never_erases_user_annotations(tmp_path):
    module = runpy.run_path(str(ROOT / "scripts/prepare_human_review.py"))
    path = tmp_path / "packet.csv"
    module["main"].__globals__["PATH"] = path
    module["main"]()
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    rows[0]["reviewer_name"] = "User supplied annotation, not validated by test"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    before = path.read_bytes()
    module["main"]()
    assert path.read_bytes() == before
