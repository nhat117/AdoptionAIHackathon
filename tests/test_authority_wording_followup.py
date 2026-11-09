import json
import runpy
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_balanced_wording_followup_preserves_records_and_pairs():
    rows = runpy.run_path(str(ROOT / "scripts/run_authority_wording_followup.py"))["design"]()
    assert len(rows) == len({r["trial_id"] for r in rows}) == 4320
    counts = Counter((r["cluster"], r["language"], r["authority"], r["wording"],
                      r["record_access"], r["attack"]) for r in rows)
    assert len(counts) == 4320 and set(counts.values()) == {1}
    pairs = {}
    for row in rows:
        body = json.loads(row["messages"][1]["content"])
        assert body["peer_message"] == row["peer_message"]
        if row["record_access"] == "absent":
            assert body["trusted_record"] is None
            assert str(row["verified_budget"]) not in json.dumps(row["messages"])
        if row["attack"]:
            assert str(row["false_budget"]) in row["peer_message"]
        else:
            assert str(row["false_budget"]) not in row["peer_message"]
        key = (row["cluster"], row["language"], row["authority"], row["wording"], row["record_access"])
        pairs.setdefault(key, {})[row["attack"]] = row
    for pair in pairs.values():
        a, b = [json.loads(pair[k]["messages"][1]["content"]) for k in (False, True)]
        a.pop("peer_message")
        b.pop("peer_message")
        assert a == b
