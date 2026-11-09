"""The expanded study must preserve task splits and paired comparisons."""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from report_oversight_expansion import cluster_contrast  # noqa: E402
from run_oversight_ablation import trial  # noqa: E402
from run_oversight_expansion import prepare  # noqa: E402


def test_expansion_has_fifty_new_tasks_and_only_registry_prompt_difference():
    cases, sources = prepare()
    assert len(cases) == 600
    assert len({c["task"]["task_id"] for c in cases}) == 50
    assert Counter(c["language"] for c in cases) == {"en": 200, "vi": 200, "zh": 200}
    used = set()
    for name in sources:
        for line in (ROOT / name).read_text().splitlines():
            row = json.loads(line)
            if isinstance(row.get("task"), dict):
                used.add(row["task"].get("task_id"))
    assert not used & {c["task"]["task_id"] for c in cases}
    pairs = defaultdict(dict)
    for case in cases:
        pairs[case["source_case_id"]][case["evidence"]] = case
    assert len(pairs) == 300
    for pair in pairs.values():
        a, b = pair["absent"], pair["present"]
        assert a["messages"][0] == b["messages"][0]
        x, y = (json.loads(c["messages"][1]["content"]) for c in (a, b))
        assert x.pop("authoritative_record") is None
        assert y.pop("authoritative_record") == a["task"]["facts"]
        assert x == y


def test_cluster_interval_excludes_incomplete_tasks_and_pairs_same_candidate():
    cases, _ = prepare()
    task_id = cases[0]["task"]["task_id"]
    chosen = [
        c
        for c in cases
        if c["task"]["task_id"] == task_id and c["evidence"] == "absent"
    ]

    class FakeClient:
        def chat(self, messages, seed):
            payload = json.loads(messages[1]["content"])
            peer = json.loads(payload["peer_report"])
            peer["public_summary"] = (
                "Budget: "
                + peer["public_summary"].split("Budget: ", 1)[1].split(". ", 1)[0]
            )
            return {"content": json.dumps(peer)}

    rows = [trial(c, FakeClient()) for c in chosen]
    assert all(r["completed"] for r in rows)
    contrast = cluster_contrast(rows, "absent", resamples=100)
    assert contrast["complete_task_clusters"] == 1
    assert contrast["structural_minus_semantic_rate"] == 0.5
    assert contrast["task_cluster_bootstrap_95_percentile_interval"] == [0.5, 0.5]
    rows[0] = dict(rows[0], completed=False)
    contrast = cluster_contrast(rows, "absent", resamples=100)
    assert contrast["complete_task_clusters"] == 0
    assert contrast["excluded_incomplete_clusters"] == 1
    assert contrast["task_cluster_bootstrap_95_percentile_interval"] is None
