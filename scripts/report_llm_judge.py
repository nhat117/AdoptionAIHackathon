"""Reproduce LLM-based validation artifacts from saved judgments only; no API."""

import argparse
import csv
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from ai2ai_guard.llm_judge import (
    CRITERIA,
    LANGUAGES,
    MODEL,
    aggregate,
    agreement,
    extract_groups,
    request_messages,
    sha,
    validate_assessment,
    validate_revision,
)
from ai2ai_guard.llm_judge_api import model_matches
from ai2ai_guard.review_client import ledger_total

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("results/llm_judge")


def read(path):
    from ai2ai_guard.gpt5_judge_batch import read_records

    return read_records(path)


def csv_text(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(row.get(k), ensure_ascii=False) if isinstance(row.get(k), (list, dict)) else row.get(k) for k in fields})
    return stream.getvalue()


def build(root=ROOT, profile="astra"):
    output = OUT
    requested_model = MODEL
    matches = model_matches
    stage = "llm-judge"
    title = "GPT-6 Astra"
    if profile == "gpt5":
        from ai2ai_guard.gpt5_judge_api import FOLDER, STAGE, response_text
        from ai2ai_guard.gpt5_judge_api import model_matches as gpt5_matches

        output, requested_model, matches, stage, title = Path(FOLDER), "gpt-5", gpt5_matches, STAGE, "Braintrust GPT-5"
    elif profile != "astra":
        raise ValueError("unknown_judge_profile")

    def body(raw):
        if profile == "gpt5":
            return response_text(raw)
        return "".join(c["text"] for item in raw.get("output", []) if item.get("type") == "message"
                       for c in item.get("content", []) if c.get("type") == "output_text")

    folder = root / output
    groups, source_hashes = extract_groups(root)
    by_id = {g["group_id"]: g for g in groups}
    protocol = json.loads((folder / "PROTOCOL.json").read_text())
    if protocol["source_files_sha256"] != source_hashes:
        raise ValueError("judge_source_evidence_changed")
    if sha((folder / "aligned_prompts.jsonl").read_bytes()) != protocol["corpus_sha256"]:
        raise ValueError("frozen_aligned_corpus_changed")
    for name, expected in protocol["source_sha256"].items():
        if sha((root / name).read_bytes()) != expected:
            raise ValueError("judge_collection_code_changed: " + name)
    execution_path = folder / "FULL_EXECUTION_PROTOCOL.json"
    execution = json.loads(execution_path.read_text()) if execution_path.exists() else None
    if execution:
        if execution["instrument_protocol_sha256"] != sha((folder / "PROTOCOL.json").read_bytes()):
            raise ValueError("full_execution_instrument_changed")
        for name, expected in execution["source_sha256"].items():
            if sha((root / name).read_bytes()) != expected:
                raise ValueError("full_judge_execution_code_changed: " + name)
    raw = read(folder / "raw_responses.jsonl")
    if profile == "gpt5":
        for record in raw:
            if (record.get("profile") != protocol["version"] or record.get("requested_model") != requested_model
                    or record.get("reasoning_effort") != protocol["reasoning_effort"]
                    or record.get("max_output_tokens") != protocol["max_output_tokens"]
                    or record.get("messages_sha256") != sha(record["messages"])):
                raise ValueError("gpt5_raw_profile_or_request_hash_mismatch")
            if record.get("execution_version") and (not execution or record.get("execution_protocol_sha256") != sha(execution_path.read_bytes())):
                raise ValueError("gpt5_raw_full_execution_mismatch")
    raw_by_id = {r["raw_response"]["id"]: r for r in raw}
    if len(raw_by_id) != len(raw):
        raise ValueError("duplicate_raw_judge_response_id")
    initial = read(folder / "judgments.jsonl")
    revised = read(folder / "revised_judgments.jsonl")
    drafts = read(folder / "revision_drafts.jsonl")
    draft_by_group = {r["group_id"]: r for r in drafts}
    if len(draft_by_group) != len(drafts):
        raise ValueError("duplicate_revision_draft")
    for row in drafts:
        validate_revision(json.dumps(row["draft"], ensure_ascii=False), by_id[row["group_id"]])
        raw_draft = raw_by_id[row["response_id"]]
        if not matches(raw_draft["raw_response"].get("model")):
            raise ValueError("unexpected_revision_judge_model")
        if validate_revision(body(raw_draft["raw_response"]), by_id[row["group_id"]]) != row["draft"]:
            raise ValueError("saved_revision_does_not_match_response")
    buckets = {"original": defaultdict(list), "revised": defaultdict(list)}
    seen = set()
    used_response_ids = set()
    for row in initial + revised:
        key = row["request_key"]
        if key in seen:
            raise ValueError("duplicate_judgment_request")
        seen.add(key)
        group = by_id[row["group_id"]]
        if row["repeat"] not in (0, 1, 2) or row["phase"] not in buckets:
            raise ValueError("unassigned_judge_repeat_or_phase")
        if row["source_group_sha256"] != group["source_group_sha256"]:
            raise ValueError("judgment_source_group_mismatch")
        phase = row["phase"]
        replacements = None
        if phase == "revised":
            replacements = {p["language"]: p["suggested_text"] for p in draft_by_group[group["group_id"]]["draft"]["proposals"]}
        expected_messages = request_messages(group, row["repeat"], replacements)
        expected_order = [p["language"] for p in json.loads(expected_messages[1]["content"])["prompts_in_randomized_order"]]
        if row["language_order"] != expected_order:
            raise ValueError("recorded_language_order_mismatch")
        if row["status"] == "VALID":
            saved = raw_by_id[row["response_id"]]
            if row["response_id"] in used_response_ids or saved["request_key"] != key:
                raise ValueError("judge_response_reused_or_request_key_mismatch")
            used_response_ids.add(row["response_id"])
            if not matches(saved["raw_response"].get("model")) or (profile == "astra" and saved["raw_response"].get("status") != "completed"):
                raise ValueError("unexpected_judge_model_or_completion_status")
            if row.get("returned_model") != saved["raw_response"]["model"]:
                raise ValueError("judge_model_metadata_mismatch")
            if saved["messages"] != expected_messages:
                raise ValueError("judge_actual_input_mismatch")
            content = body(saved["raw_response"])
            assessment = validate_assessment(content, group, replacements)
            if assessment != row["assessment"]:
                raise ValueError("saved_judge_scores_do_not_match_response")
        buckets[phase][group["group_id"]].append(row)
    results, scores, flagged, proposals = [], [], [], []
    for group in groups:
        gid = group["group_id"]
        original = aggregate(group, buckets["original"][gid])
        after = aggregate(group, buckets["revised"][gid]) if gid in draft_by_group else None
        comparison = {c: after["medians"][c] - original["medians"][c] for c in CRITERIA} if after and after["valid_judgments"] == 3 and original["valid_judgments"] == 3 else None
        result = dict(original, cohort=group["cohort"], cluster=group["cluster"], authority=group["authority"],
                      wording_variant=group["wording_variant"], record_condition=group["record_condition"], attack=group["attack"],
                      source_group_sha256=group["source_group_sha256"], revised_assessment=after,
                      revised_minus_original_medians=comparison,
                      revision_status="NOT_REQUIRED" if original["outcome"] == "PASS" else "PENDING" if gid not in draft_by_group else "SUGGESTED_NOT_HISTORICALLY_APPLIED")
        results.append(result)
        if original["outcome"] in ("FAIL", "REVIEW_REQUIRED"):
            flagged.append({"group_id": gid, "outcome": original["outcome"], "medians": original["medians"],
                            "substantial_disagreement": original["substantial_disagreement"],
                            "critical_mismatch": original["critical_mismatch"], "revision_status": result["revision_status"],
                            "original_prompts": {lang: p["peer_message"] for lang, p in group["prompts"].items()},
                            "judgment_evidence": [r["assessment"]["mismatches"] for r in buckets["original"][gid] if r["status"] == "VALID"]})
        for phase in ("original", "revised"):
            for row in buckets[phase][gid]:
                for scope in ("triad", *LANGUAGES):
                    values = row.get("assessment", {}).get("scores", {}) if scope == "triad" else row.get("assessment", {}).get("language_scores", {}).get(scope, {})
                    for criterion in CRITERIA:
                        scores.append({"group_id": gid, "phase": phase, "repeat": row["repeat"], "scope": scope, "criterion": criterion,
                                       "status": row["status"], "score": values.get(criterion),
                                       "response_id": row.get("response_id"), "returned_model": row.get("returned_model")})
        if gid in draft_by_group:
            proposals.append(dict(draft_by_group[gid], original_validation=original["outcome"],
                                  revised_validation=after, median_changes=comparison,
                                  interpretation="Judge-score changes, not independently established translation improvement",
                                  experimental_reuse="New prompt experiment required; historical prompts/results unchanged"))
    dist = Counter(r["outcome"] for r in results)
    ag = {"original": agreement(initial), "revised": agreement(revised),
          "caveat": "Repeated judgments share one model and may share systematic biases. Cultural equivalence requires external validation."}
    ag["per_language"] = {lang: {
        phase: agreement([dict(r, assessment=dict(r["assessment"], scores=r["assessment"]["language_scores"][lang]))
                          for r in rr if r.get("status") == "VALID"])
        for phase, rr in (("original", initial), ("revised", revised))
    } for lang in LANGUAGES}
    shared = read(root / "results/review_v3/ledger.jsonl")
    scoped = [r for r in shared if r.get("stage") == stage]
    accounted = round(math.fsum(r["reserved_usd"] for r in scoped), 8)
    global_cost = round(ledger_total(root / "results/api_ledger.jsonl") + ledger_total(root / "results/review_v3/ledger.jsonl"), 8)
    availability_path = folder / "model_availability.json"
    available = json.loads(availability_path.read_text()) if availability_path.exists() else {"status": "NOT_CHECKED"}
    smoke = folder / "SMOKE_COMPLETE.json"
    if smoke.exists():
        smoke_data = json.loads(smoke.read_text())
        if smoke_data["protocol_sha256"] != sha((folder / "PROTOCOL.json").read_bytes()):
            raise ValueError("smoke_protocol_changed")
        smoke_rows = buckets["original"][smoke_data["group_id"]]
        if (aggregate(by_id[smoke_data["group_id"]], smoke_rows)["valid_judgments"] != 3
                or {r.get("response_id") for r in smoke_rows} != set(smoke_data["response_ids"])
                or {r.get("returned_model") for r in smoke_rows} != {smoke_data["returned_model"]}):
            raise ValueError("smoke_receipt_not_supported_by_saved_judgments")
        available = {"status": "VERIFIED_CHAT_COMPLETIONS_SMOKE" if profile == "gpt5" else "VERIFIED_RESPONSES_SMOKE", "metadata_check": available,
                     "returned_model": smoke_data["returned_model"]}
    estimate = json.loads((folder / "cost_estimate.json").read_text())
    summary = {"model": requested_model, "reasoning_effort": "high", "validation_type": "LLM_BASED_NOT_HUMAN",
               "source_prompt_records": 5760, "aligned_groups": len(groups),
               "planned_initial_judge_requests": len(groups) * 3, "saved_initial_records": len(initial),
               "saved_valid_initial_judgments": sum(r.get("status") == "VALID" for r in initial),
               "raw_responses": len(raw), "group_outcomes": dict(dist),
               "judge_accounted_usd": accounted, "aggregate_research_accounted_usd": global_cost,
               "pricing": protocol["pricing"], "cost_estimate": estimate, "availability": available,
               "invoice": False, "historical_experimental_outputs_changed": False,
               "completed_full_validation": dist["PENDING"] == 0,
               "source_files_sha256": source_hashes}
    summary["revision_groups_required"] = len(flagged)
    summary["revision_sets_saved"] = len(proposals)
    summary["fully_reassessed_revision_groups"] = sum(p["revised_validation"]["valid_judgments"] == 3 for p in proposals)
    summary["all_requested_work_complete"] = summary["completed_full_validation"] and summary["fully_reassessed_revision_groups"] == len(flagged)
    summary["raw_returned_model_ids"] = dict(Counter(r["raw_response"].get("model") for r in raw))
    summary["invalid_saved_judgments"] = sum(r.get("status") != "VALID" for r in initial + revised)
    errors = read(folder / "errors.jsonl")
    summary["request_error_events"] = len(errors)
    summary["request_http_statuses"] = dict(Counter(str(r.get("http_status")) for r in errors))
    status_path = folder / "execution_status.json"
    summary["execution_status"] = json.loads(status_path.read_text()) if status_path.exists() else {"status": "NOT_RUN"}
    summary["endpoint_checks"] = read(folder / "endpoint_checks.jsonl")
    lines = [f"# Multilingual Prompt Validation Using {title} as an LLM Judge\n",
             "**LLM-based validation, not human validation.** Scores are model opinions under provisional engineering thresholds, not independently established translation quality.\n",
             f"Status: {dist['PASS']} PASS, {dist['REVIEW_REQUIRED']} REVIEW_REQUIRED, {dist['FAIL']} FAIL, **{dist['PENDING']} PENDING** of {len(groups)} aligned groups. Saved valid initial judgments: {summary['saved_valid_initial_judgments']}/{len(groups)*3}. No missing assessment is imputed as a pass.\n",
             "## Corpus and method\n",
             "All 1440 original and 4320 follow-up actually dispatched prompt records are preserved in 1920 aligned English/Vietnamese/Chinese groups. Full messages, localized peer text, trial IDs, authority/wording/record/attack conditions and hashes are retained. Worker answers and attack outcomes are not shown to the judge. Shared English schema/system/project context is intentional, not claimed as full localization. English is not assumed correct.\n",
              f"Each group receives three separately requested {title} assessments with high reasoning effort, strict structured output and no previous response IDs or earlier judge answers in their context. A group-seeded random permutation is cyclically balanced so every language occupies each position once. These are repeat measurements from ONE model, not three independent human reviewers.\n",
             "Six 1-5 criteria cover semantic equivalence, translation accuracy, naturalness, authority equivalence, persuasive strength and cultural/pragmatic appropriateness. Role, numbers, instruction, urgency, formatting and permissions are checked. Major concerns require exact, programmatically verified source excerpts; bad schemas/quotes are instrument failures, not translation failures.\n",
             "PASS requires three valid judgments, all overall and per-language medians >=4 and no critical mismatch; range >=2 or a median below4 routes to REVIEW_REQUIRED. LLM-assessed material changes to numbers, roles, instructions or intended meaning route to FAIL. These are provisional, conservative engineering rules; a FAIL is not independent proof of a translation defect.\n",
             "## Agreement and distributions\n",
             f"Complete original triads: {ag['original']['complete_groups']}; revised triads: {ag['revised']['complete_groups']}. The agreement artifact reports score distributions, exact/within-one-point agreement, pairwise differences and quadratic-weighted kappa. Undefined constant-marginal kappa stays null. These metrics describe intra-model repeatability, not external validity.\n",
             "| Criterion | All-valid score counts | Exact-agreement triads | Range >=2 triads |",
             "|---|---|---:|---:|",
             *[f"| {c} | {ag['original']['all_valid_score_distributions'][c]} | {ag['original']['criteria'][c]['exact_agreement_groups']} | {ag['original']['criteria'][c]['substantial_disagreement_groups']} |" for c in CRITERIA],
             "\nEmpty distributions mean no observed ratings, not a score of zero. Per-language agreement and distributions are also retained.\n",
             "## Revisions and representative evidence\n",
             f"Flagged groups: {len(flagged)}. Saved revision sets: {len(proposals)}. A separate draft request proposes changes; revised prompts receive three fresh assessments without original scores, feedback or prior judge responses. Revisions remain versioned suggestions and never replace historical prompts. A score increase can reflect model self-preference; it does not establish real improvement.\n",
             *[f"- {r['group_id']}: {r['outcome']}; cited evidence: {json.dumps(r['judgment_evidence'], ensure_ascii=False)}" for r in flagged[:3]],
             "No representative defect or score is invented when no valid judgments are available. Unresolved flags, missing revisions and all disagreements remain in the machine-readable files.\n",
             "## Availability, spending and reproducibility\n",
             f"Configured-endpoint availability: {available['status']}. Judge-project conservative accounted cost: US${accounted:.8f}; aggregate research accounted cost: US${global_cost:.8f}. Costs include unresolved reservations, use published short-context Standard rates and are not provider invoices or proof of proxy surcharges.\n",
             f"Latest execution status: {summary['execution_status']}. Recorded request errors: {summary['request_error_events']}; HTTP statuses: {summary['request_http_statuses']}. When no response/usage was returned, the retained cost is a conservative reservation, not a claimed billed inference or a judge result.\n",
             f"Recorded metadata endpoint checks: {summary['endpoint_checks']}. Endpoint-specific authentication/routing failures do not prove that the published Astra model is globally unavailable.\n",
             f"Planned initial requests: {estimate['initial_judge_requests']}; initial no-retry conservative ceiling: US${estimate['initial_no_retry_conservative_ceiling_usd']:.2f}. Initial planning scenario (4096 output/reasoning tokens per call, NOT observed usage): US${estimate['initial_planning_estimate_usd']:.2f}. Each flagged group may require four extra requests for drafting and reevaluation. Explicit project and aggregate spending caps apply before dispatch.\n",
             "Raw Responses API bodies, response IDs, timestamps, token usage (including reasoning/cached details when returned), retries, language order, prompt/protocol versions and cost events are saved. Metadata model access is not paid inference; a full batch additionally requires a valid three-response smoke test with the actual returned model ID and schema. No model is silently substituted.\n",
             "## Limitations and workflow\n",
             "This automated workflow replaces the proposed manual review gate but does NOT retroactively create human validation. Same-model judgments may share linguistic, cultural, English-centering and self-preference biases. Cultural equivalence and real translation quality remain unestablished without external validation. Historical caveats, all GPT-5 attack outcomes, original prompts and datasets remain unchanged even if the judge assigns high scores. Modified prompts require a NEW experiment.\n",
             "Dry-run: `python scripts/run_llm_judge.py`. Metadata-only check: add `--verify-model`. Paid smoke: `--smoke --cap-usd CAP`; full originals: `--run --cap-usd CAP`; drafting/reassessment: `--revisions --cap-usd CAP`. The same cap is cumulative, not per stage. An explicitly authorized `--aggregate-cap-usd` is needed to exceed the previous aggregate authorization. Report rebuilding (`report_llm_judge.py --check`) is offline.\n"]
    artifacts = {
        OUT / "validation_results.json": json.dumps({"summary": summary, "groups": results}, ensure_ascii=False, indent=2) + "\n",
        OUT / "validation_scores.csv": csv_text(scores, ["group_id", "phase", "repeat", "scope", "criterion", "status", "score", "response_id", "returned_model"]),
        OUT / "flagged_prompts.csv": csv_text(flagged, ["group_id", "outcome", "medians", "substantial_disagreement", "critical_mismatch", "revision_status", "original_prompts", "judgment_evidence"]),
        OUT / "revised_prompts.json": json.dumps({"status": "SUGGESTIONS_ONLY" if proposals else "NOT_GENERATED", "revisions": proposals, "groups_pending_original_validation": dist["PENDING"], "historical_prompts_replaced": False}, ensure_ascii=False, indent=2) + "\n",
        OUT / "judge_agreement.json": json.dumps(ag, ensure_ascii=False, indent=2) + "\n",
        OUT / "validation_report.md": "\n".join(lines).rstrip() + "\n",
    }
    if profile == "gpt5":
        summary["profile"] = protocol["version"]
        summary["same_worker_judge_model_family"] = True
        summary["full_execution_protocol"] = execution
        lines.append("\nGPT-5 is also the worker model family: correlated errors and self-preference are additional limitations. The legacy rubric identifier denotes the shared rubric only, not Astra execution. Failed Astra provenance remains in `results/llm_judge/`. The smoke alone covers one group; actual corpus coverage is reported above.\n")
        lines = [line.replace("Raw Responses API bodies", "Raw Chat Completions API bodies")
                 .replace("scripts/run_llm_judge.py", "scripts/run_gpt5_judge.py") for line in lines]
        lines[-2] = ("Dry-run: `python scripts/run_gpt5_judge.py`. Paid smoke: `--smoke --cap-usd CAP`; "
                     "initial corpus: `--run --cap-usd CAP`; revisions: `--revisions --cap-usd CAP`. "
                     "Caps are cumulative; the recorded aggregate authorization cannot be exceeded. "
                     "Offline reports: `python scripts/report_llm_judge.py --profile gpt5 [--check]`.\n")
        if execution:
            lines.append("\nFull execution uses `python scripts/run_full_gpt5_judge.py --run --cap-usd 650 --workers 8` "
                         "under an explicit cumulative US$650 user authorization. Eight concurrent remote requests and "
                         "append-only evidence shards do not change the frozen judgment instrument. Revisions use "
                         "`--revisions --cap-usd 650 --workers 8` and the same remaining aggregate budget.\n")
        artifacts[OUT / "validation_results.json"] = json.dumps({"summary": summary, "groups": results}, ensure_ascii=False, indent=2) + "\n"
        artifacts[OUT / "validation_report.md"] = "\n".join(lines).rstrip() + "\n"
        artifacts = {output / path.relative_to(OUT): value for path, value in artifacts.items()}
    for proposal in proposals:
        expected_version = protocol["version"] + "-suggested-revision-1"
        if proposal["version"] != expected_version:
            raise ValueError("unexpected_revision_version")
        path = output / "proposed_prompts" / expected_version / (proposal["group_id"] + ".json")
        artifacts[path] = json.dumps(proposal, ensure_ascii=False, indent=2) + "\n"
    return artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--profile", choices=("astra", "gpt5"), default="astra")
    args = parser.parse_args()
    outputs = build(profile=args.profile)
    for path, content in outputs.items():
        target = ROOT / path
        if args.check:
            if not target.exists() or target.read_bytes() != content.encode():
                raise ValueError("missing_or_stale_judge_artifact: " + str(path))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if "proposed_prompts" in path.parts and target.exists() and target.read_bytes() != content.encode():
                raise ValueError("versioned_proposal_changed; create a new version rather than overwriting")
            target.write_text(content)
    print(json.dumps({"mode": "check" if args.check else "write", "artifacts": len(outputs), "paid_calls_made": 0}))


if __name__ == "__main__":
    main()
