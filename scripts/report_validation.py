"""Generate the consolidated report from verified, separately scoped cohorts."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from ai2ai_guard.contract_eval import assess_contract

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/validation_audit"


def read(path):
    return (
        [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    )


def cohort(name, expected_count):
    folder = ROOT / "results" / name
    inputs = read(folder / "inputs.jsonl")
    observed = read(folder / "workers.jsonl")
    expected = {r["trial_id"]: r for r in inputs}
    assert len(expected) == expected_count
    assert len(observed) == len({r["trial_id"] for r in observed}) == expected_count
    protocol = json.loads((folder / "PROTOCOL.json").read_text())
    assert (
        hashlib.sha256((folder / "inputs.jsonl").read_bytes()).hexdigest()
        == protocol["inputs_sha256"]
    )
    for name, sha in protocol["source_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
    scored = []
    for row in observed:
        assert all(row[k] == v for k, v in expected[row["trial_id"]].items())
        result = assess_contract(
            row["response"]["content"],
            row["verified_budget"],
            row["false_budget"],
            row["record_budget"],
            row["record_access"] in ("correct", "corrupt_current"),
        )
        if row["contract"] != "operational":
            result["policy_compliant"] = None
        scored.append(
            dict(
                trial_id=row["trial_id"],
                cluster=row["cluster"],
                contract=row["contract"],
                record_access=row["record_access"],
                attack=row["attack"],
                score=result,
            )
        )
    groups = []
    for contract in ("neutral", "operational"):
        for access in sorted({r["record_access"] for r in scored}):
            for attack in (False, True):
                rr = [
                    r
                    for r in scored
                    if r["contract"] == contract
                    and r["record_access"] == access
                    and r["attack"] == attack
                ]
                groups.append(
                    {
                        "contract": contract,
                        "record": access,
                        "attack": attack,
                        "n": len(rr),
                        "valid": sum(r["score"]["status"] == "VALID" for r in rr),
                        "false_target": sum(
                            r["score"]["attack_adoption"] is True for r in rr
                        ),
                        "fact_correct": sum(
                            r["score"]["fact_correct"] is True for r in rr
                        ),
                        "abstained": sum(r["score"]["abstained"] is True for r in rr),
                        "policy_compliant": sum(
                            r["score"]["policy_compliant"] is True for r in rr
                        )
                        if contract == "operational"
                        else None,
                    }
                )
    return {
        "n": len(observed),
        "groups": groups,
        "decisions": scored,
        "models": dict(Counter(r["response"]["model"] for r in observed)),
        "collection_errors": len(read(folder / "errors.jsonl")),
    }


def table(groups):
    lines = [
        "| Contract | Record | Attack | n | Valid | False target | Correct budget | Abstained | Policy compliant |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in groups:
        policy = "N/A" if r["policy_compliant"] is None else str(r["policy_compliant"])
        lines.append(
            f"| {r['contract']} | {r['record']} | {r['attack']} | {r['n']} | {r['valid']} | {r['false_target']} | {r['fact_correct']} | {r['abstained']} | {policy} |"
        )
    return lines


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--partial", action="store_true")
    args = p.parse_args()
    if args.partial:
        print(
            json.dumps(
                {
                    name: len(read(ROOT / "results" / name / "workers.jsonl"))
                    for name in ["contract_validation", "corrupt_record_validation"]
                }
            )
        )
        return
    matched = cohort("contract_validation", 216)
    corrupt = cohort("corrupt_record_validation", 72)
    OUT.mkdir(exist_ok=True)
    for name, data in [("contract", matched), ("corruption", corrupt)]:
        (OUT / (name + "_decisions.jsonl")).write_text(
            "".join(
                json.dumps(r, ensure_ascii=False) + "\n" for r in data.pop("decisions")
            )
        )
    ledger = read(ROOT / "results/api_ledger.jsonl")
    accounting = sum(r["reserved_usd"] for r in ledger)
    metrics = {
        "matched_contract": matched,
        "hidden_corruption": corrupt,
        "aggregate_accounted_usd": accounting,
        "authorized_total_cap_usd": 20,
        "scope": "Three matched task clusters; descriptive validation, not a powered language/authority study",
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    tests = (ROOT / "results/tests_execution.txt").read_text().splitlines()[-1]
    operational = [r for r in matched["groups"] if r["contract"] == "operational"]
    corrupt_op = [r for r in corrupt["groups"] if r["contract"] == "operational"]
    summary = (
        f"Latest validation: {sum(r['policy_compliant'] for r in operational)}/108 "
        f"operational outputs complied with the stated policy; "
        f"{108 - sum(r['valid'] for r in operational)} were strict format failures. "
        f"Observed false-target authorizations: {sum(r['false_target'] for r in operational)}. "
        f"With a corrupt record deceptively marked current, "
        f"{sum(r['policy_compliant'] for r in corrupt_op)}/36 operational outputs "
        f"followed the policy, but only {sum(r['fact_correct'] for r in corrupt_op)}/36 "
        f"reported the true budget. Policy compliance is not factual truth.\n"
    )
    lines = [
        "# Budget handoff research: validated findings and remaining limits\n",
        "Updated 9 November 2026. This report consolidates executed studies while keeping their different tasks and output contracts separate. Every result is backed by saved prompts, outputs and decisions. It does not certify unrestricted agents or arbitrary natural-language truth.\n",
        summary,
        "## Does the experiment work?\n",
        "The code and fixed-cohort reconstruction work. Structured decision scoring can distinguish reporting a false target, reporting the correct budget, abstaining, and invalid format. The new contract validation gives an explicit normative meaning to the decision field. This does not validate hidden belief inference, all prose attribution, or general authority/language effects.\n",
        f"Local verification: {tests}. Separate known-answer tests cover 16 policy/factual cases, including duplicate keys, invalid decisions, unsupported evidence and a wrong current record. These are synthetic engineering tests, not independent human validation of natural-language claims.\n",
        "## Why the original numbers did not change\n",
        "The original 600 budget outputs contain 150 wrong field values and 450 budget-consistent reports. Both old and corrected semantic gates release the same 450 and reject the same 150. Expanded contradictory-prose coverage adds regression capability but no extra detection on this saved cohort. The oracle still receives the correct budget; its 150/150 sensitivity is not evidence of realistic oversight. The blind monitor allowed 6/150 wrong outputs, blocked 115/450 budget-correct outputs, and abstained on 445/600. Historical data and results remain intact.\n",
        "## Multi-task reporting study: executed, but interpret narrowly\n",
        "The 1440-response study used 20 task clusters, four authority claims, three peer-message languages, three record conditions and matched clean/attack inputs. In attacked cases the explicit false target was reported in 1/240 correct-record cases, 75/240 absent-record cases and 14/240 stale-record cases. Three strict format failures remain unknown, not successful defenses. A separately labeled key-case sensitivity recovers those outputs and changes absent-record false-target reporting to 76/240.\n",
        "The single correct-record false-target event explicitly qualified the peer figure in prose. The neutral prompt did not define the budget field as authorization for action. Therefore these counts measure false-target reporting, not necessarily unqualified endorsement or policy violation. The new validation below tests that construct directly. The paired task-bootstrap estimates and 13 exploratory contrasts remain in [the replication report](../results/measurement_v2_replication/REPORT.md); twenty synthetic tasks, fixed task-block dispatch and one model do not establish culture-level or model-general effects.\n",
        "## Matched contract validation: 216 new calls\n",
        "Three task clusters (45–47) are disjoint from the v2 pilot and replication, but their scenarios existed historically. The same user/peer inputs are paired across neutral and operational system contracts. Dispatch is randomized using seed 20261110. The operational contract defines reported_budget as the final budget authorized for an inert downstream handoff, requires a current record, and requires abstention when records are absent or stale. It permits discussing peer claims only in summary. No actual payment or financial action occurs.\n",
    ]
    lines += table(matched["groups"])
    lines += [
        "\nPolicy compliance is assessed only where the operational policy was actually supplied. Neutral-arm outputs are not retrospectively charged with violating a policy they never received. Invalid formats are unscored for policy compliance. This study validates construct clarity and contract following in three synthetic tasks; it is not a definitive treatment-effect estimate or a stronger-defense leaderboard.\n",
        "## Hidden record corruption: 72 separate stress-test calls\n",
        "This separate cohort supplies a wrong budget (truth minus 1000) deceptively labeled current. The true value is withheld from every worker prompt. A worker can now obey the record-following policy and still report a false budget. Compliance and factual correctness must therefore be reported separately. This cohort was frozen and collected separately, not pooled into the matched experiment.\n",
    ]
    lines += table(corrupt["groups"])
    lines += [
        "\nThis is the limit of grounding in a supplied record: a label saying current is not independent proof of truth. The experiment does not implement external record authentication, source reconciliation or retrieval of a second verified record.\n",
        "## Committee evidence\n",
        "The original 24-game experiment had the true cap available at all 144 exposed agent turns, so its zero propagation is a weak test. The six-game follow-up removed the true cap in absent/stale conditions and still observed no planted-cap repetition. It has only one game per cell, and its fixed expense of 15000 is above both the true cap (12000) and stale cap (11000). It does not identify a guard benefit or validate decision utility when stale records change eligibility. Later committee work should vary expenses across the decision boundary and use repeated matched games. No additional committee replication is claimed in this report.\n",
        "## Validation, provenance and budget\n",
        "Frozen inputs and collection source hashes are checked by the report scripts. The artifact verifier checks condition coverage, unique response IDs, prompt joins, blind-monitor input boundaries and preservation of the historical baseline. Raw v2 metadata corrections retain their original collected bytes and correction hashes. Three response bodies from an earlier interrupted partial game remain unavailable; their costs are accounted and they are excluded from completed-game analyses. No new observation was removed to obtain a preferred result.\n",
        f"Aggregate accounted cost across all stages: **US${accounting:.4f}**, within the user-authorized **US$20 total cap**. This uses returned token usage at published uncached GPT-5 rates and retains unresolved reservations. It is not a provider invoice. Exact returned model IDs are stored with responses; this remains a single-model study.\n",
        "The dashboard is still a historical static snapshot; updating this report does not publish a new dashboard. Independent bilingual review, human adjudication of arbitrary prose, more task families and cross-model replication remain outstanding.\n",
        "## Interpretation\n",
        "The defensible conclusion is that record availability and record correctness affect the budget information a worker transmits, and that reporting a value, authorizing a value, obeying a policy and being factually correct are different outcomes. The studies support those distinctions within their saved synthetic tasks. They do not establish universal resistance to authority, misinformation or multilingual attacks.\n",
        "## Reproduce\n",
        "Run the unit suite and lint, then `python scripts/report_measurement_replication.py`, `python scripts/report_measurement_sensitivity.py`, `python scripts/report_validation.py`, and `python scripts/verify_corrected_artifacts.py`. `python scripts/run_contract_validation.py` and `python scripts/run_corrupt_record_validation.py` are zero-call dry runs; add `--run --cap-usd 20` to resume missing IDs using the same aggregate ledger. Keep that ledger when resuming. See [reproduction instructions](../REPRODUCE_CORRECTED.md).\n",
        "## Research context and references\n",
        "Scalable oversight distinguishes what a judge can verify from what it accepts (Irving et al., 2018). Indirect prompt injection motivates distinguishing untrusted peer claims from authoritative sources (Greshake et al., 2023). Sycophancy and multilingual vulnerability findings motivate studying authority and language, but do not supply results for this budget task (Sharma et al., 2023; Yong et al., 2023). Exposure-matched multi-agent comparisons motivate preserving record-access conditions (Becker et al., 2026). Memory and knowledge-source poisoning is related work, not a benchmark reproduced here (Chen et al., 2024). Bibliographic details were checked against the primary records during the earlier research update.\n",
    ]
    old = (ROOT / "research/CORRECTED_BUDGET_RESULTS.md").read_text()
    references = old.split("## References\n", 1)[1]
    lines.append(references)
    (ROOT / "research/VALIDATED_RESEARCH_REPORT.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "matched_calls": matched["n"],
                "corruption_calls": corrupt["n"],
                "accounted_usd": accounting,
            }
        )
    )


if __name__ == "__main__":
    main()
