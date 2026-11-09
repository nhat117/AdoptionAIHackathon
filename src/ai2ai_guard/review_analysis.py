"""Single validated data-loading and analysis path for the follow-up report."""

import hashlib
import json
import math
from collections import Counter

from swarm_lab.review_committee import matched_decision_changes, summarize_game

from .budget_claims import OracleChecker, report_text
from .budget_claims_v2 import VERSION as DETECTOR_VERSION
from .budget_claims_v2 import ResearchOracleChecker, report_text_v2, target_measurement
from .review_client import ledger_total
from .review_measurement import (
    VERSION,
    monitoring_metrics,
    record_from_row,
    score_outcome,
    source_gate,
)
from .review_statistics import analyze
from .review_translations import inventory


def read(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_originals(root):
    manifest = json.loads((root / "research/review_resolution/PRESERVED.json").read_text())
    for name, sha in manifest["sha256"].items():
        if digest(root / name) != sha:
            raise ValueError("Original evidence modified: " + name)
    archive = root / "research/review_resolution/archive/1dcf401"
    archived = json.loads((archive / "manifest.json").read_text())
    for name, sha in archived["sha256"].items():
        if digest(archive / name.rsplit("/", 1)[-1]) != sha:
            raise ValueError("Archived deliverable modified: " + name)
    return len(manifest["sha256"])


def join(inputs, rows, complete=True):
    expected = {r["trial_id"]: r for r in inputs}
    ids = [r["trial_id"] for r in rows]
    if len(expected) != len(inputs) or len(ids) != len(set(ids)):
        raise ValueError("duplicate_trial_ids")
    if not set(ids) <= set(expected) or (complete and set(ids) != set(expected)):
        raise ValueError("missing_or_unassigned_trials")
    for row in rows:
        if any(row.get(k) != v for k, v in expected[row["trial_id"]].items()):
            raise ValueError("prompt_or_metadata_mismatch: " + row["trial_id"])


def load_replication(root):
    folder = root / "results/measurement_v2_replication"
    inputs, rows = read(folder / "inputs.jsonl"), read(folder / "workers.jsonl")
    if len(inputs) != 1440:
        raise ValueError("incorrect_replication_count")
    join(inputs, rows)
    protocol = json.loads((folder / "PROTOCOL.json").read_text())
    if digest(folder / "inputs.jsonl") != protocol["inputs_sha256"]:
        raise ValueError("frozen_replication_input_hash")
    for name, sha in protocol["source_sha256"].items():
        if digest(root / name) != sha:
            raise ValueError("frozen_replication_source_hash: " + name)
    keys = [(r["cluster"], r["language"], r["authority"], r["record_access"], r["attack"]) for r in rows]
    if len(set(keys)) != 1440 or {r["cluster"] for r in rows} != set(range(25, 45)):
        raise ValueError("unbalanced_replication_cells")
    ids = [r["response"]["response_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate_worker_response_ids")
    return rows


def load_stages(root):
    folder = root / "results/review_v3"
    protocol = json.loads((folder / "PROTOCOL.json").read_text())
    for name, sha in protocol["source_sha256"].items():
        if digest(root / name) != sha:
            raise ValueError("collection_source_changed: " + name)
    if digest(root / "results/api_ledger.jsonl") != protocol["original_ledger_sha256"]:
        raise ValueError("original_ledger_changed_after_review_freeze")
    stages, coverage = {}, []
    for stage, expected in (("monitors", 2880), ("pilot", 36), ("pilot-monitors", 72), ("committee", 40)):
        path = folder / stage
        inputs = json.loads((path / "inputs.json").read_text()) if (path / "inputs.json").exists() else []
        observed = read(path / "outputs.jsonl") if (path / "outputs.jsonl").exists() else []
        if inputs:
            if len(inputs) != expected:
                raise ValueError("changed_assigned_stage_size: " + stage)
            join(inputs, observed, complete=False)
        elif observed:
            raise ValueError("observations_without_frozen_inputs")
        returned = (sum("response" in e for r in observed for e in r["result"]["trace"])
                    if stage == "committee" else len(observed))
        failed_turns = (sum(e.get("status") == "infrastructure_failure" for r in observed for e in r["result"]["trace"])
                        if stage == "committee" else 0)
        coverage.append({"stage": stage, "planned_units": expected, "saved_units": len(observed),
                         "pending_units": expected - len(observed), "complete": len(observed) == expected,
                         "complete_definition": "Assigned units recorded; NOT a claim that every model call returned or every output was valid",
                         "planned_model_calls": expected * (21 if stage == "committee" else 1),
                         "returned_model_responses": returned,
                         "retained_infrastructure_failed_turns": failed_turns,
                         "error_events": len(read(path / "errors.jsonl")) if (path / "errors.jsonl").exists() else 0})
        stages[stage] = observed
    return stages, coverage


def strategies(rows, outcomes, monitor_rows, normalized=False):
    monitors = {(r["source_trial_id"], r["variant"]): r for r in monitor_rows}
    if len(monitors) != len(monitor_rows):
        raise ValueError("duplicate_monitor_verdict")
    descriptions = {
        "none": "Worker output only; no monitor; worker abstentions remain non-reports",
        "source_only": "Worker output and self-reported evidence source only; no record or truth",
        "source_freshness": "Worker output and controller-supplied record freshness/availability/verification; no hidden truth, no amount matching",
        "oracle_v1": "Legacy full-text checker with hidden true budget; best-case diagnostic, not deployment",
        "oracle_v2": "Versioned full-text checker with hidden true budget; best-case diagnostic, not deployment",
        "original_blind": "Exactly original two untrusted strings (peer and output); no task, record or hidden truth",
        "improved_blind": "Task, explicit allowed-evidence policy, visible record and both untrusted strings; no hidden truth; extra evidence, not a prompt-only treatment",
    }
    decisions = {name: [] for name in descriptions}
    details = []
    for row, outcome in zip(rows, outcomes):
        raw = row["response"]["content"]
        record = record_from_row(row)
        gates = {"none": "INVALID" if not outcome["format_valid"] else "ALLOW" if outcome["reported"] else "ABSTAIN",
                 "source_only": source_gate(raw, normalize_case=normalized)["decision"],
                 "source_freshness": source_gate(raw, record, True, normalized, record_authorised=True)["decision"],
                 "oracle_v1": OracleChecker().check(report_text(raw), row["verified_budget"])["decision"],
                 "oracle_v2": ResearchOracleChecker().check(report_text_v2(raw), row["verified_budget"])["decision"]}
        for variant in ("original", "improved"):
            saved = monitors.get((row["trial_id"], variant))
            gates[variant + "_blind"] = saved["verdict"]["decision"] if saved else "PENDING"
        for name, verdict in gates.items():
            decisions[name].append(verdict)
        details.append({"trial_id": row["trial_id"], "outcome": outcome, "gates": gates,
                        "target_measurement": target_measurement(raw, row["false_budget"])})
    return {name: dict(information=descriptions[name], **monitoring_metrics(outcomes, values))
            for name, values in decisions.items()}, details


def historical_monitor(root):
    refs = {r["trial_id"]: r for r in read(root / "runs/oversight-expansion-v2/trials.jsonl")}
    monitors = read(root / "results/historical-monitor/outputs.jsonl")
    if len(monitors) != 600 or {r["trial_id"] for r in monitors} != set(refs):
        raise ValueError("historical_monitor_coverage")
    outcomes = [{"wrong_budget": "budget" in refs[r["trial_id"]]["oracle"]["incorrect_or_missing_facts"],
                 "target_relay": None, "reported": True, "format_valid": True,
                 "category": "historical_field_label"} for r in monitors]
    metrics = monitoring_metrics(outcomes, [r["decision"] for r in monitors])
    metrics["cross_tab"] = dict(Counter(("wrong" if o["wrong_budget"] else "correct") + "_" + r["decision"]
                                       for r, o in zip(monitors, outcomes)))
    metrics["cohort"] = "Gemma worker reports; GPT-5 blind-monitor evaluations. Different contract/tasks from GPT-5 replication."
    return metrics


def run_analysis(root, draws=10000):
    def collection_snapshot():
        return {str(p.relative_to(root)): digest(p)
                for p in sorted((root / "results/review_v3").rglob("*.jsonl"))
                if p.name not in ("preflight.jsonl", "decisions.jsonl")}

    snapshot = collection_snapshot()
    preserved = verify_originals(root)
    rows = load_replication(root)
    stages, coverage = load_stages(root)
    strict = [score_outcome(r) for r in rows]
    normalized = [score_outcome(r, True) for r in rows]
    for row, score in zip(rows, strict):
        if (score["format_valid"] != (row["score"]["status"] == "VALID")
                or score["target_relay"] != row["score"]["attack_adoption"]):
            raise ValueError("strict_primary_score_changed: " + row["trial_id"])
    results = {"outcome_version": VERSION, "original_files_preserved": preserved,
               "worker_model": dict(Counter(r["response"]["model"] for r in rows)),
               "stage_coverage": coverage, "strict": {}, "key_case_sensitivity": {},
               "historical_blind_monitor": historical_monitor(root)}
    results["versions"] = {"dataset": "review-followup-v3.1", "outcomes": VERSION,
                           "detector": DETECTOR_VERSION, "statistics": "task-blocked-post-review-v1",
                           "monitor_original": "BlindMonitor baseline at 1dcf401 (unchanged prompt/parse rules)",
                           "monitor_improved": "policy-blind-v1",
                           "authority_wordings": "authority-wording-v2"}
    for name, scored, normalized_keys in (("strict", strict, False), ("key_case_sensitivity", normalized, True)):
        groups = []
        for access in ("correct", "absent", "stale"):
            for attack in (False, True):
                values = [o for r, o in zip(rows, scored) if r["record_access"] == access and r["attack"] == attack]
                groups.append({"record": access, "attack": attack, "n": len(values),
                               "outcomes": dict(sorted(Counter(o["category"] for o in values).items())),
                               "invalid_formats": sum(not o["format_valid"] for o in values)})
        metrics, details = strategies(rows, scored, stages["monitors"], normalized_keys)
        results[name] = {"groups": groups, "strategies": metrics,
                         "statistics": analyze(rows, scored, draws), "decisions": details}
    pilot = stages["pilot"]
    pilot_scores = [score_outcome(r) for r in pilot]
    pilot_strategies, pilot_details = strategies(pilot, pilot_scores, stages["pilot-monitors"])
    results["provenance_pilot"] = {
        "n": len(pilot), "planned": 36, "strategies": pilot_strategies, "decisions": pilot_details,
        "false_record_self_attributions": sum(o["target_relay"] is True and o.get("claimed_source") == "record" for o in pilot_scores),
        "groups": [{"attack_type": attack, "record": access,
                    "n": len(rr := [o for r, o in zip(pilot, pilot_scores) if r["attack_type"] == attack and r["record_access"] == access]),
                    "outcomes": dict(Counter(o["category"] for o in rr))}
                   for attack in ("clean", "counterfeit_record", "false_freshness") for access in ("correct", "absent")],
    }
    games = [summarize_game(r) for r in stages["committee"]]
    results["committee"] = {"games": games, "matched_decision_changes": matched_decision_changes(games),
                            "scope": "Exploratory, English-only, five independent unseeded games per cell if complete; advisory guard is not the improved LLM monitor"}
    corpus = json.loads((root / "configs/claim-regressions-v2.json").read_text())
    results["detector_regressions"] = [dict(case,
        v1=OracleChecker().check(case["text"], corpus["verified_budget"])["decision"],
        v2=ResearchOracleChecker().check(case["text"], corpus["verified_budget"])["decision"])
        for case in corpus["cases"]]
    prose_rows = read(root / "results/workers/outputs.jsonl")
    prose = []
    for row in prose_rows:
        text = report_text_v2(row["response"]["content"])
        prose.append({"trial_id": row["trial_id"],
                      "v1": OracleChecker().check(report_text(row["response"]["content"]), row["verified_budget"])["decision"],
                      "v2": ResearchOracleChecker().check(text, row["verified_budget"])["decision"],
                      "target_measurement": target_measurement(row["response"]["content"], row["false_budget"])})
    results["free_prose_reanalysis"] = {
        "n": len(prose), "cohort": "Separate 600 GPT-5 free-prose outputs, not the structured replication",
        "v1_decisions": dict(Counter(r["v1"] for r in prose)),
        "v2_decisions": dict(Counter(r["v2"] for r in prose)),
        "exact_target_mentions": sum(r["target_measurement"]["mentioned"] for r in prose),
        "rows": prose,
        "scope": "Versioned heuristic diagnostic; changing parser labels does not establish model factual error/adoption rates or human agreement",
        "original_metrics_sha256": digest(root / "results/prospective_metrics.json")}
    results["supporting_cohorts"] = {}
    for name in ("measurement_v2", "contract_validation", "corrupt_record_validation"):
        cohort = read(root / "results" / name / "workers.jsonl")
        scored = [score_outcome(r) for r in cohort]
        compared, _ = strategies(cohort, scored, [])
        results["supporting_cohorts"][name] = {
            "n": len(cohort), "model": dict(Counter(r["response"]["model"] for r in cohort)),
            "outcomes": dict(Counter(o["category"] for o in scored)),
            "strategies": compared,
            "scope": "Separate saved contract/design; no new monitor calls for this cohort, not pooled into replication"}
    results["translations"] = inventory(root, rows)
    original_cost = ledger_total(root / "results/api_ledger.jsonl")
    new_cost = ledger_total(root / "results/review_v3/ledger.jsonl")
    results["cost"] = {"original_accounted_usd": round(original_cost, 8),
                       "review_accounted_usd": round(new_cost, 8),
                       "aggregate_accounted_usd": round(math.fsum([original_cost, new_cost]), 8),
                       "cap_usd": 20, "invoice": False}
    if results["cost"]["aggregate_accounted_usd"] > 20:
        raise ValueError("aggregate_budget_exceeded")
    raw_path = root / "results/review_v3/api_responses.jsonl"
    raw = read(raw_path) if raw_path.exists() else []
    response_ids = [r["response"]["id"] for r in raw]
    if len(set(response_ids)) != len(response_ids):
        raise ValueError("duplicate_api_response_ids")
    retained = []
    for stage, observed in stages.items():
        if stage == "committee":
            retained += [e["response"]["response_id"] for r in observed for e in r["result"]["trace"] if "response" in e]
        else:
            retained += [r["response"]["response_id"] for r in observed]
    if len(retained) != len(set(retained)) or not set(retained) <= set(response_ids):
        raise ValueError("stage_body_provenance_mismatch")
    raw_by_id = {r["response"]["id"]: r for r in raw}
    for stage, observed in stages.items():
        checks = [(e["response"], e["response"]["delivered_messages"])
                  for r in observed for e in r["result"]["trace"] if "response" in e] if stage == "committee" else [
                      (r["response"], r["messages"]) for r in observed]
        for response, messages in checks:
            saved = raw_by_id[response["response_id"]]
            if (saved["messages"] != messages or saved["response"]["choices"][0]["message"]["content"] != response["content"]
                    or saved["response"]["model"] != response["model"]):
                raise ValueError("returned_body_or_prompt_changed")
    results["provenance"] = {"base_commit": "1dcf401", "collection_protocol": "results/review_v3/PROTOCOL.json",
                             "saved_review_calls": len(response_ids), "stage_attached_calls": len(retained),
                             "durable_unattached_bodies": sorted(set(response_ids) - set(retained)),
                             "returned_models": dict(Counter(r["response"]["model"] for r in raw)),
                             "tokens": {k: sum(r["response"].get("usage", {}).get(k, 0) for r in raw)
                                        for k in ("prompt_tokens", "completion_tokens")}}
    review_ledger_path = root / "results/review_v3/ledger.jsonl"
    review_ledger = read(review_ledger_path) if review_ledger_path.exists() else []
    reserved_ids = {r["request_id"] for r in review_ledger if "time" in r}
    reconciled_ids = {r["request_id"] for r in review_ledger if "actual_usd" in r}
    results["provenance"]["api_attempts"] = len(reserved_ids)
    results["provenance"]["unresolved_reservations"] = sorted(reserved_ids - reconciled_ids)
    names = ["configs/review-v3.json", "configs/authority-wording-v2.json", "configs/claim-regressions-v2.json",
             "results/measurement_v2_replication/workers.jsonl", "results/measurement_v2_replication/inputs.jsonl",
             "results/historical-monitor/outputs.jsonl", "research/review_resolution/PRESERVED.json"]
    names += [str(p.relative_to(root)) for p in sorted((root / "src/ai2ai_guard").glob("review_*.py"))]
    names += ["src/ai2ai_guard/budget_claims_v2.py", "src/swarm_lab/review_committee.py"]
    names += ["scripts/run_research_pipeline.py", "scripts/report_review_followup.py", "scripts/export_review_report.py"]
    names += ["research/review_resolution/fonts/NotoSansSC-report-subset.ttf"]
    names += [str(p.relative_to(root)) for p in sorted((root / "results/review_v3").rglob("*.jsonl"))
              if p.name not in ("preflight.jsonl", "decisions.jsonl")]
    results["source_sha256"] = {name: digest(root / name) for name in names}
    if collection_snapshot() != snapshot:
        raise ValueError("Collection changed during analysis; rerun after collection is stopped. No inconsistent report was written.")
    return results
