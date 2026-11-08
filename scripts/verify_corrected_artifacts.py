"""Verify collection coverage, prompt matching, baseline integrity and provenance."""

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
BASELINE_COMMIT = "d38bbd4b225ddebff1c8d1d412ec2902d31d6a41"


def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines()]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    expected = {r["trial_id"]: r for r in rows(OUT / "authority_language/inputs.jsonl")}
    assert len(expected) == 600
    workers = rows(OUT / "workers/outputs.jsonl")
    assert len(workers) == len({r["trial_id"] for r in workers}) == 600
    for row in workers:
        for key, value in expected[row["trial_id"]].items():
            assert row[key] == value, (row["trial_id"], key)
    stages = {"workers": workers, "pilot": rows(OUT / "pilot/outputs.jsonl")}
    baseline = rows(ROOT / "runs/oversight-expansion-v2/trials.jsonl")
    for stage, source in [("historical-monitor", baseline), ("new-monitor", workers)]:
        observed = rows(OUT / stage / "outputs.jsonl")
        source_by_id = {r["trial_id"]: r for r in source}
        assert len(observed) == len({r["trial_id"] for r in observed}) == 600
        assert {r["trial_id"] for r in observed} == set(source_by_id)
        for row in observed:
            assert len(row["messages"]) == 2
            body = json.loads(row["messages"][1]["content"])
            ref = source_by_id[row["trial_id"]]
            peer = (
                json.loads(ref["messages"][1]["content"])["peer_report"]
                if stage == "historical-monitor"
                else ref["peer_message"]
            )
            assert body == {
                "peer_message": peer,
                "worker_output": ref["response"]["content"],
            }
        stages[stage] = observed
    games = rows(OUT / "committee/outputs.jsonl")
    assert len(games) == len({r["trial_id"] for r in games}) == 24
    assert Counter(r["guarded"] for r in games) == {False: 12, True: 12}
    assert all(r["completed"] and len(r["trace"]) == 21 for r in games)
    assert sum(len(r["trace"]) for r in games) == 504
    responses = [r["response"] for group in stages.values() for r in group]
    responses += [e["response"] for r in games for e in r["trace"] if "response" in e]
    assert len(responses) == 2328
    assert len({r["response_id"] for r in responses}) == 2328
    subprocess.run(
        [
            "git",
            "diff",
            "--exit-code",
            BASELINE_COMMIT,
            "--",
            "runs",
            "data",
            "submission",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    tracked = subprocess.check_output(
        ["git", "ls-files", "runs", "data", "submission"], cwd=ROOT, text=True
    ).splitlines()
    baseline_hashes = {name: digest(ROOT / name) for name in tracked}
    files = [
        p
        for folder in ["src", "scripts", "tests", "results"]
        for p in (ROOT / folder).rglob("*")
        if p.is_file()
        and "__pycache__" not in str(p)
        and p.name not in ("PROVENANCE.json", "verification_execution.json")
    ]
    ledger = rows(OUT / "api_ledger.jsonl")
    saved_ids = {r["response_id"] for r in responses}
    # Subsequent v2 completions are separate studies, not lost v1 bodies.
    v2 = OUT / "measurement_v2"
    if (v2 / "workers.jsonl").exists():
        for row in map(json.loads, (v2 / "workers.jsonl").read_text().splitlines()):
            saved_ids.add(row["response"]["response_id"])
    if (v2 / "committee.jsonl").exists():
        for game in map(json.loads, (v2 / "committee.jsonl").read_text().splitlines()):
            saved_ids.update(
                e["response"]["response_id"] for e in game["trace"] if "response" in e
            )
    replication = OUT / "measurement_v2_replication"
    if (replication / "workers.jsonl").exists():
        for row in map(
            json.loads, (replication / "workers.jsonl").read_text().splitlines()
        ):
            saved_ids.add(row["response"]["response_id"])
    for validation_stage in ("contract_validation", "corrupt_record_validation"):
        validation_path = OUT / validation_stage / "workers.jsonl"
        if validation_path.exists():
            for row in map(json.loads, validation_path.read_text().splitlines()):
                saved_ids.add(row["response"]["response_id"])
    orphaned = [
        r for r in ledger if "actual_usd" in r and r["response_id"] not in saved_ids
    ]
    files += [
        ROOT / name
        for name in [
            "README.md",
            "pyproject.toml",
            "REPRODUCE_CORRECTED.md",
            "research/CORRECTED_BUDGET_RESULTS.md",
            "research/VALIDATED_RESEARCH_REPORT.md",
            "research/VALIDATED_RESEARCH_REPORT.docx",
            ".github/workflows/ci.yml",
        ]
    ]
    v2_counts = {}
    if (v2 / "workers.jsonl").exists():
        v2_workers = rows(v2 / "workers.jsonl")
        v2_inputs = {r["trial_id"]: r for r in rows(v2 / "inputs.jsonl")}
        assert len(v2_workers) == len({r["trial_id"] for r in v2_workers}) == 36
        for row in v2_workers:
            assert all(row[k] == val for k, val in v2_inputs[row["trial_id"]].items())
            body = json.loads(row["messages"][1]["content"])
            assert body["peer_message"] == row["peer_message"]
            if row["record_access"] != "correct":
                assert str(row["verified_budget"]) not in json.dumps(row["messages"])
        v2_games = rows(v2 / "committee.jsonl")
        assert len(v2_games) == len({r["trial_id"] for r in v2_games}) == 6
        assert all(r["completed"] and len(r["trace"]) == 21 for r in v2_games)
        v2_counts = {"workers": 36, "committee_games": 6, "committee_calls": 126}
    replication_counts = {}
    if (replication / "workers.jsonl").exists():
        rep_workers = rows(replication / "workers.jsonl")
        rep_inputs = {r["trial_id"]: r for r in rows(replication / "inputs.jsonl")}
        assert len(rep_workers) == len({r["trial_id"] for r in rep_workers}) == 1440
        for row in rep_workers:
            assert all(row[k] == v for k, v in rep_inputs[row["trial_id"]].items())
        assert {r["cluster"] for r in rep_workers} == set(range(25, 45))
        replication_counts = {"workers": 1440, "task_clusters": 20}
    validation_counts = {}
    for validation_stage, count in [
        ("contract_validation", 216),
        ("corrupt_record_validation", 72),
    ]:
        folder = OUT / validation_stage
        if (folder / "workers.jsonl").exists():
            observed = rows(folder / "workers.jsonl")
            expected = {r["trial_id"]: r for r in rows(folder / "inputs.jsonl")}
            assert len(observed) == len({r["trial_id"] for r in observed}) == count
            assert all(
                all(row[k] == v for k, v in expected[row["trial_id"]].items())
                for row in observed
            )
            assert len({r["response"]["response_id"] for r in observed}) == count
            validation_counts[validation_stage] = count
    expected_saved = len(responses)
    if v2_counts:
        expected_saved += v2_counts["workers"] + v2_counts["committee_calls"]
    if replication_counts:
        expected_saved += replication_counts["workers"]
    expected_saved += sum(validation_counts.values())
    assert len(saved_ids) == expected_saved, "Duplicate response IDs across studies"
    word_export = json.loads((OUT / "WORD_REPORT_EXPORT.json").read_text())
    assert (
        digest(ROOT / word_export["source_markdown"]) == word_export["source_sha256"]
    ), "Word report is stale; regenerate it from the current Markdown report"
    assert digest(ROOT / word_export["word_file"]) == word_export["word_sha256"], (
        "Word export changed after visual verification"
    )
    provenance = {
        "branch": subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True
        ).strip(),
        "baseline_commit": BASELINE_COMMIT,
        "collection_counts": {k: len(v) for k, v in stages.items()},
        "measurement_v2_counts": v2_counts,
        "measurement_v2_replication_counts": replication_counts,
        "contract_validation_counts": validation_counts,
        "committee_games": 24,
        "committee_calls": 504,
        "successful_saved_model_calls": len(responses),
        "successful_saved_model_calls_all_studies": len(saved_ids),
        "interrupted_game_responses_without_saved_body": orphaned,
        "returned_models": dict(Counter(r["model"] for r in responses)),
        "baseline_files_unchanged": len(baseline_hashes),
        "baseline_sha256": baseline_hashes,
        "artifact_sha256": {str(p.relative_to(ROOT)): digest(p) for p in files},
    }
    (OUT / "PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in provenance.items()
                if k not in ["baseline_sha256", "artifact_sha256"]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
