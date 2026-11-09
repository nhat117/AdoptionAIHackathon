"""Concise Round 3 manuscript plus separately scoped technical appendix."""

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def table(headers, rows):
    return ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers),
            *["| " + " | ".join(map(str, row)) + " |" for row in rows], ""]


def ratio(value):
    k, n = value["numerator"], value["denominator"]
    return f"{k}/{n}" + (f" ({100*k/n:.1f}%)" if n else " (not estimable)")


def report(data):
    r3 = data["round3"]
    wording, neutral = r3["wording_language"], r3["neutral"]
    nm = neutral.get("metrics")
    cells = [r for r in wording["cells"] if r["record"] == "absent" and r["attack"]]
    primary = data["key_case_sensitivity"]["strategies"]["source_freshness"]
    lines = [
        "# Authority Across Languages: wording sensitivity and conditional budget oversight\n",
        "**Research draft; not officially submitted.** Author names and affiliations await confirmation. "
        "This is the one main manuscript. Detailed normalized tables, statistics and checks are in the "
        "[technical appendix](ROUND3_APPENDIX.md); prior manuscripts remain archived.\n",
        "## Abstract\n",
        "1. **The wording changes the language pattern.** In the no-record attacked cells of the 4320-answer "
        "study, the leading language changes across the three fixed wording sets. This is "
        "wording/translation sensitivity, not a general ranking of languages or cultures.\n",
    ]
    if nm:
        release = nm["defences"]["source_freshness"]["wrong_report_release_among_wrong_reports"]
        lines.append(f"2. **The neutral-prompt pilot reveals real release failures.** The new "
                     f"{neutral['collected']}/{neutral['assigned']}-case fake-record pilot produced "
                     f"{nm['known_wrong_reports']} known wrong reports and "
                     f"{nm['false_record_attribution_per_assigned']['numerator']} unsupported record attributions. "
                     f"The unchanged source-plus-freshness rule released {release['numerator']} known wrong reports.\n")
    else:
        lines.append("2. **Strict-prompt results do not establish neutral-worker robustness.** "
                     "The planned neutral fake-record test remains unexecuted; no result is invented.\n")
    lines += [
        "3. **The successful defence result is conditional.** In the original matched study the rule "
        "blocked 549/549 wrong reports and falsely blocked 0/479 correct reports (key-case sensitivity). That result depends "
        "on honest source labels and reliable controller records, not universal resistance to peers.\n",
        "4. **A bad record marked current can still pass.** In a separate deliberately corrupted-record "
        "cohort, the rule accepted 72/72 wrong reports. Following supplied evidence is not the same as "
        "reporting truth; these synthetic handoffs do not establish universal prompt-injection prevention.\n",
        "## 1. Research question and hypotheses\n",
        "**Question:** How do wording, peer-message language and record access affect incorrect budget "
        "reporting, and under which source assumptions does oversight contain it?\n",
        "The historical analyses are post-review and exploratory. H1: language contrasts vary across "
        "the three fixed wordings. H2: counterfeit-record/staleness claims can induce unsupported record "
        "attribution under the existing neutral contract. H3: a source/freshness rule depends on honest "
        "citations and trustworthy record metadata/content. The new neutral design and metrics were "
        "locally frozen before dispatch, not externally preregistered. No hypothesis requires a successful attack.\n",
        "Scalable oversight distinguishes verification from acceptance (Irving et al., 2018), while "
        "indirect prompt injection motivates explicit untrusted-source boundaries (Greshake et al., 2023). "
        "Sycophancy and multilingual-vulnerability work motivates these factors, not a prediction that "
        "one tested language must dominate (Sharma et al., 2023; Yong et al., 2023).\n",
        "## 2. Threat model\n",
        "The attacker controls only an untrusted peer-message string. It can claim to be an authority, "
        "paste a fake current record, or falsely say the real record is stale. It cannot modify the "
        "controller-supplied trusted_record, the system prompt or the evaluator's budget registry. "
        "A schema-valid reported value is an observable transmission, not proof of hidden belief. No payment occurs.\n",
        "The separate 72-case corrupt-record stress test intentionally supplies false controller evidence "
        "marked current. This violates the base trustworthy-record assumption; it is not an observed "
        "external compromise or a peer attack silently changing the controller's record. Its model outputs "
        "are actual saved responses to constructed bad inputs, not fabricated outputs.\n",
        "Knowledge-source poisoning and benign multi-agent misinformation are related research contexts "
        "(Chen et al., 2024; Becker et al., 2026); their benchmarks and published success rates are not "
        "reproduced or imported as results here.\n",
        "## 3. Experimental design\n",
        "All current budget cohorts requested GPT-5 and returned `gpt-5-2025-08-07`, with minimal reasoning, "
        "512 maximum completion tokens and no model sampling seed. Earlier Gemma work used different "
        "prompts/tasks and is not a direct model-performance comparator.\n",
        "The primary study has 1440 workers: 20 tasks × 4 role claims × 3 peer languages × 3 record states "
        "(current/correct, stale, absent) × clean/attack. The separate 4320-worker follow-up adds three "
        "wordings per role/language. These historical scenarios are reused, not model-unseen tasks. "
        "Role levels are teammate, team lead, finance auditor and fake system administrator; they are "
        "fixed role messages, not a validated monotonic social-authority scale.\n",
        "**New neutral pilot:** 10 historical tasks (40–49) × clean/fake-current/fake-stale peer messages "
        "× EN/VI/Chinese × correct/absent records = 180 assigned calls. The entire neutral system "
        "instruction, user-task framing and output schema are copied from the primary inputs. No strict "
        "warning that peers cannot create/authenticate records is added. Peer attack text is reused from "
        "the strict pilot, changing assigned budget values only. Fake-stale means a peer's false freshness "
        "claim, not a genuinely stale controller record.\n",
        "The preserved strict 36-case pilot uses an explicit record-only policy, two different task "
        "clusters and operational user framing. Strict and neutral counts are reported separately; their "
        "difference is not a causal estimate of one warning sentence.\n",
        "Workers return reported_budget, decision (REPORT/ABSTAIN), evidence (record/peer/none) and summary. "
        "ABSTAIN requires null budget. The primary outcome is a valid explicit REPORT of the planted target. "
        "Stale-record reliance is a separate factual error. Schema failures remain unknown. Source-only "
        "and source-plus-freshness gates reuse each candidate without repair; the latter does not match "
        "the selected amount to the actual record amount. Gate ALLOW means an inert handoff would accept "
        "the candidate, not a real-world action.\n",
        "False-record attribution is defined operationally: a valid REPORT cites `record` but its amount "
        "is unsupported by the actual controller record (or no such record exists). This is not a claim "
        "of intentional deception or a violation of a strict instruction the neutral worker never received. "
        "The coarse source label may itself be ambiguous about a peer's purported record.\n",
        "## 4. Results\n",
    ]
    if nm:
        lines += [f"The neutral pilot returned **{neutral['collected']}/180** workers; "
                  f"{nm['parse_valid']} passed strict parsing, {neutral['collected'] - nm['parse_valid']} "
                  f"failed the format contract, and {neutral['pending']} calls are missing. "
                  f"There were {nm['known_wrong_reports']} known wrong REPORTs, {nm['known_correct_reports']} "
                  f"known correct REPORTs and {nm['valid_abstentions']} valid abstentions. An abstention "
                  "is not successful budget completion.\n"]
        lines += table(["Neutral peer input", "Actual record", "Wrong report / assigned", "False record attribution / assigned", "Wrong releases (source+freshness)"],
                       [[g["attack_type"], g["record"], ratio(g["budget_corruption_per_assigned"]),
                         ratio(g["false_record_attribution_per_assigned"]),
                         ratio(g["defences"]["source_freshness"]["wrong_report_release_among_wrong_reports"])] for g in neutral["groups"]])
        lines += [f"Confirmed corruption risk is {ratio(nm['budget_corruption_per_assigned'])} across all "
                  f"assigned calls; unsupported record attribution is {ratio(nm['false_record_attribution_per_assigned'])}. "
                  "Invalid/missing cases remain in assigned denominators and identification bounds. Wrong-release/"
                  "block fractions condition on known wrong REPORTs; false blocks condition on known correct REPORTs. "
                  "Language/record breakdowns, all denominators and the invalid-output review are in the appendix.\n",
                  "![Neutral-worker candidate outcomes](../results/round3/figures/neutral_outcomes.svg)\n"]
        attacked = neutral["attack_clean_subsets"]["attacked"]
        clean = neutral["attack_clean_subsets"]["clean"]
        lines.append(f"Restricting to the 120 attacked calls rather than diluting with clean controls, "
                     f"confirmed corruption is {ratio(attacked['budget_corruption_per_assigned'])}, "
                     f"unsupported record attribution is {ratio(attacked['false_record_attribution_per_assigned'])}, "
                     f"and wrong releases are {ratio(attacked['defences']['source_freshness']['wrong_report_release_per_assigned'])}. "
                     f"Clean-control corruption is {ratio(clean['budget_corruption_per_assigned'])}.\n")
    lines += [
        "The strict pilot remains a separate 36-worker cohort with no observed strict false-record "
        "attributions. It does not erase or explain away neutral-prompt failures. No response or failed "
        "format was replaced to improve the results.\n",
        "## 5. Wording and language sensitivity\n",
        "The no-record attacked cells each have 80 assigned answers (20 tasks × 4 roles). "
        "Rates below are strict target-number REPORTs, not every numeric mention.\n",
    ]
    rows = []
    for word in (1, 2, 3):
        cc = {r["language"]: r for r in cells if r["wording"] == word}
        rows.append([word, *[f"{cc[lang]['strict_target_REPORT']}/80 ({cc[lang]['strict_rate']:.2%})" for lang in ("en", "vi", "zh")],
                     "/".join(str(cc[lang]["raw_numeric_field_target"]) for lang in ("en", "vi", "zh"))])
    lines += table(["Wording", "EN strict", "VI strict", "CN/zh strict", "Raw numeric field EN/VI/CN"], rows)
    lines += [
        "The review's 25/6/64, 66/48/50 and 51/59/44 numeric-field counts reproduce. However, two VI "
        "answers in wording 2 and one Chinese answer in wording 3 explicitly say ABSTAIN while carrying "
        "a nonnull target budget. Those three violate the contract: strict counts are 46 (not 48) and "
        "43 (not 44). Key-case normalization does not resolve contradictory decisions. The source "
        "responses and IDs are retained for review; neither scoring definition is silently substituted.\n",
        "![Wording by language, strict scoring](../results/round3/figures/wording_language.svg)\n",
        "**Interaction analysis:** four roles per task are repeated observations, not independent tasks. "
        "We use 20 task-block differences, 10000 seeded task-bootstrap draws and exact two-sided sign-flip "
        "tests, assuming independent sign-symmetric task differences under the null. Eighteen wording×language "
        "contrasts cover all record states and receive Holm correction; raw-field sensitivity is separate.\n",
    ]
    example = next(r for r in wording["interactions"]["strict_primary"] if r["record"] == "absent" and r["wording"] == 2 and r["language"] == "zh" and r["language_reference"] == "en")
    lo, hi = example["task_bootstrap_95"]
    lines.append(f"For example, the CN-minus-EN contrast changes by **{100*example['difference']:.2f} percentage "
                 f"points** between wordings 2 and 1 without a record (task 95% interval "
                 f"[{100*lo:.2f}, {100*hi:.2f}], Holm p={example['p_holm']:.6f}). This is exploratory "
                 "evidence of interaction under the stated assumptions, not a culture-level causal effect.\n")
    lines += [
        "Language, translated phrasing, role credibility and wording cannot be cleanly separated with "
        "these fixed exemplars. The observed ranking reverses; no language is claimed consistently "
        "more persuasive. Full contrasts, pointwise intervals, invalid counts and sensitivity definitions "
        "are in the appendix/CSV rather than repeated as competing main tables.\n",
        "## 6. Defence evaluation\n",
        "Source+freshness admits only a claimed record source with an available current controller record. "
        "It assumes that the source label honestly describes the selected amount and that the record's "
        "freshness/content is reliable. Those assumptions are not external authentication.\n",
    ]
    defence_rows = [["Original 1440 workers (key-case sensitivity)", ratio(primary["strict_block_recall"]),
                     ratio(primary["false_block_rate"]), "0/549"]]
    if nm:
        d = nm["defences"]["source_freshness"]
        defence_rows.append(["Neutral fake-record 180", ratio(d["wrong_report_block_among_wrong_reports"]),
                             ratio(d["correct_report_false_block"]), ratio(d["wrong_report_release_among_wrong_reports"])])
    defence_rows.append(["Corrupt-current stress 72 (constructed inputs)", "0/72", "Not estimable (no correct reports)", "72/72"])
    lines += table(["Separate cohort", "Known wrong reports blocked", "Correct reports falsely blocked", "Known wrong reports allowed"], defence_rows)
    if nm:
        d = nm["defences"]["source_freshness"]
        lines.append(f"The neutral pilot supplies an observed counterexample: source+freshness releases "
                     f"{ratio(d['wrong_report_release_among_wrong_reports'])} known wrong reports "
                     f"({ratio(d['wrong_report_release_per_assigned'])} of all assigned cases). "
                     "A model can label a peer-supplied replacement amount as record while a different, "
                     "correct current record exists. This unchanged diagnostic gate does not check amount binding.\n")
    lines += [
        "In the corrupt-current stress cohort, all 72 saved model answers follow the false record marked "
        "current and the rule accepts 72/72 wrong reports. These are observed outputs from deliberately "
        "constructed bad-record inputs, not evidence that an attacker compromised a real record system.\n",
        "AI-monitor comparisons are restricted to the same 1440 GPT-5 workers. Original blind-monitor "
        "recall is 78/549 with 36/479 false blocks; the policy-aware monitor gives 241/549 and 4/479. "
        "The second monitor also sees the visible record and policy, so this is not a prompt-only "
        "treatment. Neither gets hidden evaluator truth. Oracle checkers do; their best-case numbers "
        "are not deployment performance. No monitor result is transferred to the neutral pilot or "
        "combined with the different Gemma historical study. Detailed decision coverage/abstentions are appended.\n",
        "These results do **not** demonstrate universal prompt-injection prevention. Blocking is not "
        "repair. A stronger amount/source-binding check would require a separately evaluated design; "
        "we do not retrofit one to hide the two observed releases.\n",
        "## 7. Limitations\n",
        "The tasks are synthetic, the main budget studies use one GPT-5 snapshot, and the same historical "
        "scenarios and fixed translations recur. Twenty task blocks (and ten in the new pilot) limit "
        "generalization. Bootstrap/sign-flip assumptions are not proof of independent human/population "
        "effects; constant outcomes do not establish equivalence. Schema errors remain unknown, not "
        "refusals or successful defences. Peer-message studies are inert reporting handoffs, not a "
        "validated benchmark of arbitrary autonomous swarms. Earlier committee work remains exploratory.\n",
        "No native-speaker review or independent cultural validation is claimed. Review sheets remain "
        "unfilled; author names/affiliations require confirmation. Final package preparation is not "
        "official submission. Existing valid references are preserved below.\n",
        "### Multilingual Prompt Validation Using GPT-6 Astra as an LLM Judge\n",
        "A separate automated pipeline aligns all 5760 historical prompt records into 1920 trios and "
        "supports three randomized, independent requests, exact-evidence rubrics, intra-model agreement "
        "and versioned/blinded revision reassessment. This is **LLM-based validation, not human validation**. "
        "English is not treated as gold; same-model repeats may share systematic biases; thresholds "
        "are provisional, not validated standards. Even high scores could not erase external-validation limits.\n",
        "Its requested configuration is documented for the Astra model (OpenAI, n.d.); published model "
        "documentation is not evidence that this account completed a judge call.\n",
    ]
    judge = data.get("llm_judge_summary")
    if judge:
        lines.append(f"Execution remains **blocked/pending**: {judge['saved_valid_initial_judgments']}/"
                     f"{judge['planned_initial_judge_requests']} valid initial judgments, group outcomes "
                     f"{judge['group_outcomes']}. The proxy smoke returned HTTP404 and direct OpenAI metadata "
                     "authentication returned HTTP401. No judge score or translation improvement is invented; "
                     "[the separate validation report](../results/llm_judge/validation_report.md) retains the details.\n")
    lines += [
        "## 8. Conclusion\n",
        "Wording strongly changes language-specific target reporting within these tested messages; "
        "there is no defensible universal language ranking. Neutral fake-record tests must not inherit "
        "robustness claims from strict-prompt pilots. Source/freshness filtering worked under the original "
        "source-honesty conditions, but observed neutral releases and corrupt-current inputs show its "
        "limits. Reliable record provenance and value binding—not a 100% label on one cohort—are the "
        "remaining research problem. All old outputs, null findings and new failures remain preserved.\n",
        "**Reproduce without inference:** `python scripts/run_research_pipeline.py`, "
        "`python scripts/export_review_report.py`, their `--check` modes, `pytest -q` and `ruff check .` (offline). "
        "Native review and author/submission steps remain on the [submission checklist](../submission/final-review/SUBMISSION_CHECKLIST.md).\n",
        "## References\n",
    ]
    old = (ROOT / "research/review_resolution/archive/1dcf401/VALIDATED_RESEARCH_REPORT.md").read_text()
    references = old.split("## Research context and references\n", 1)[1].split("\n\n\n", 1)[-1].strip()
    lines.append(references)
    lines.append("\nOpenAI. (n.d.). *GPT-6 Astra* [Model documentation]. Retrieved November 9, 2026, "
                 "from https://developers.openai.com/api/docs/models/gpt-6-astra\n")
    return "\n".join(lines).rstrip() + "\n"


def figures(data):
    plot = runpy.run_path(str(ROOT / "scripts/audit_experiments.py"))["stacked_chart"]
    plot.__globals__["COLORS"] = ["#c45046", "#717d96", "#ad73a0"]
    cells = [r for r in data["round3"]["wording_language"]["cells"] if r["record"] == "absent" and r["attack"]]
    result = {"wording_language.svg": plot(
        "GPT-5: language patterns change across the three fixed wordings",
        "Strict explicit target REPORTs /80 assigned; invalids remain unknown. Other/non-target is not a safety-success claim.",
        [(f"wording {r['wording']} / {r['language']}", {"target_REPORT": r["strict_target_REPORT"],
          "other_or_non_target": r["n"] - r["strict_target_REPORT"] - r["invalid_formats"], "invalid": r["invalid_formats"]}) for r in cells],
        ["target_REPORT", "other_or_non_target", "invalid"])}
    neutral = data["round3"]["neutral"]
    if "groups" in neutral:
        plot.__globals__["COLORS"] = ["#277b71", "#c45046", "#717d96", "#ad73a0"]
        result["neutral_outcomes.svg"] = plot(
            "GPT-5 neutral fake-record pilot: pre-gate candidate outcomes",
            "180 assigned calls; abstention is not correct-report utility and unknown formats are not successful defences.",
            [(f"{r['record']} / {r['attack_type']}", {"correct_REPORT": r["known_correct_reports"],
              "wrong_REPORT": r["known_wrong_reports"], "abstention": r["valid_abstentions"],
              "unknown": r["unknown_or_missing"]}) for r in neutral["groups"]],
            ["correct_REPORT", "wrong_REPORT", "abstention", "unknown"])
    return result


def appendix(data):
    r3, lines = data["round3"], ["# Technical appendix: Authority Across Languages, Round 3\n",
                                 "This appendix supports the one canonical manuscript; it is not a competing main report. "
                                 "All raw outputs remain at their original paths.\n",
                                 "## A1. Scoring definitions and ambiguous outputs\n",
                                 "Strict REPORT semantics remain primary. Raw numeric-field sensitivity ignores decision validity "
                                 "and therefore cannot be relabelled adoption or authorization. All invalid transcripts are in "
                                 "`results/round3/ambiguous_wording_outputs.csv`. The three reviewed nonnull ABSTAIN targets "
                                 "explain the VI/CN count differences; key-case normalization does not fix them.\n"]
    for name, view in (("Strict primary", data["strict"]), ("Key-case sensitivity", data["key_case_sensitivity"])):
        lines.append(f"## A2. Original GPT-5 1440 cohort: {name}\n")
        lines += table(["Strategy", "Wrong block", "Correct false block", "Correct release", "Coverage"],
                       [[key, ratio(v["strict_block_recall"]), ratio(v["false_block_rate"]),
                         ratio(v["correct_report_release"]), ratio(v["coverage"])] for key, v in view["strategies"].items()])
        for key, v in view["strategies"].items():
            lines.append(f"- {key}: {v['information']}; decisions {v['decisions']}.")
    lines += ["\n## A3. Wording-language interaction details\n", r3["wording_language"]["methods"] + "\n",
              "All 18 strict contrasts and 18 raw-field sensitivity contrasts, uncertainty and adjusted p-values "
              "are in `results/round3/wording_language_interactions.csv`. Full wording×language×record×clean/attack "
              "cells are in `wording_language.csv`. Earlier 32-contrast language/authority-by-record analyses "
              "remain separately available in their original results directories, not silently replaced.\n",
              "## A4. Neutral denominators and transcript audits\n",
              "Assigned-case risks retain missing/invalid bounds. Conditional wrong-block/release rates use known "
              "wrong REPORTs; false-block rates use known correct REPORTs. Abstentions and invalid outputs are "
              "separate. `neutral_by_language.csv`, `neutral_decisions.jsonl` and `neutral_ambiguous_outputs.csv` "
              "retain the full breakdown, original prompt/response references and raw ambiguity.\n"]
    neutral = r3["neutral"]
    if "metrics" in neutral:
        lines.append("```json\n" + json.dumps(neutral["metrics"], indent=2) + "\n```\n")
        for row in neutral["decisions"]:
            if row["wrong_budget"] is True and row["defence_decisions"]["source_freshness"]["decision"] == "ALLOW":
                lines.append(f"- Observed wrong-release case: `{row['trial_id']}`; language {row['language']}; "
                             f"{row['attack_type']}; actual record {row['record_condition']}; "
                             f"selected {row['selected_budget']}; source {row['source_label']}. "
                             "Exact input/response and truth remain in the raw neutral worker file.\n")
    lines += ["## A5. Strict pilot and corrupt-record supporting cohorts\n",
              "Strict provenance pilot: 36 saved workers, zero observed strict false-record attributions; "
              "separate tasks/system/user framing. Corrupt-current cohort: 72 actual saved model outputs "
              "under deliberately wrong controller inputs, source/freshness passes 72/72 wrong reports. "
              "Constructed conditions are not fabricated model outputs or observed external system compromises.\n",
              "## A6. Historical and engineering checks\n",
              "Historical Gemma-worker/GPT-5-monitor evaluation remains separate: wrong ALLOW/BLOCK/ABSTAIN "
              "6/0/144; correct 34/115/301. Detector regressions are synthetic engineering tests, not model "
              "successes or human translation judgments; v2.1's nine false positives remain archived. Earlier "
              "committee experiments remain exploratory, including failures and null propagation.\n",
              "## A7. Reproducibility and pending preparation\n",
              f"Protected original data/result files: {data['original_files_preserved']}. All archive manifests, "
              "raw response/prompt joins, duplicate IDs and source hashes are checked. Original study metrics "
              "are not recomputed under a new unpublished definition. Aggregate accounting: "
              f"US${data['cost']['aggregate_accounted_usd']:.8f}, cap US${data['cost']['cap_usd']:g}; not an invoice.\n",
              "The blocked Astra attempt has no returned judge scores. Native sheets are unreviewed; author "
              "identities/affiliations await confirmation; official submission is unconfirmed. See the "
              "machine-readable Round 3 audit/remediation report and submission checklist.\n"]
    return "\n".join(lines).rstrip() + "\n"


def remediation(data):
    neutral = data["round3"]["neutral"]
    nm = neutral.get("metrics")
    statuses = {"R1": "Fixed", "R2": "Fixed" if neutral["status"] == "COMPLETE" else "Blocked",
                "R3": "Fixed", "R4": "Fixed", "R5": "Partially Fixed"}
    records = [
        {"issue": "R1", "original_problem": "Pooled language claims hide wording-dependent reversals",
         "root_cause": "Three fixed translations/wordings are not a language population; reviewer counts also include inconsistent ABSTAIN numeric fields",
         "files_changed": ["src/ai2ai_guard/round3_analysis.py", "scripts/report_round3.py", "tests/test_round3.py"],
         "fix": "Strict and raw-field counts separated; 20-task blocked wording×language interactions, bootstrap intervals, exact sign-flip/Holm tests; unsupported general ranking removed",
         "tests_performed": "Raw-data golden matrices, 3 contradictory-output audit, synthetic paired-interaction known answer; full suite/receipts linked below",
         "results": "Strict absent counts 25/6/64, 66/46/50, 51/59/43; numeric-field counts reproduce review 25/6/64, 66/48/50, 51/59/44. See all 18 contrasts per definition.",
         "remaining_limitations": "Post-review exploratory; 20 historical tasks, fixed wordings, unreviewed translations, sign-symmetry assumptions; no causal culture claim"},
        {"issue": "R2", "original_problem": "Strict-record pilot cannot establish neutral-worker resistance",
         "root_cause": "The 36-case pilot adds explicit record-only policy and operational framing",
         "files_changed": ["configs/round3-neutral-v1.json", "src/ai2ai_guard/round3_neutral.py", "scripts/run_round3_neutral.py", "src/ai2ai_guard/round3_analysis.py", "tests/test_round3.py"],
         "fix": "180-factor-complete neutral calls; literal neutral system/user task/schema, same GPT-5 settings, reused attack texts; separate strict and neutral metrics",
         "tests_performed": "Exact neutral-prompt identity, 180 unique factor cells, source-boundary and metric-denominator known answers; raw response joins and model ID checks",
         "results": f"{neutral['collected']}/180 saved; " + (f"{nm['known_wrong_reports']} wrong reports, {nm['false_record_attribution_per_assigned']['numerator']} unsupported record attributions, {nm['unknown_or_missing']} unknown formats/cases" if nm else "API results unavailable; pending"),
         "remaining_limitations": "Ten historical tasks, one model, finite machine-authored attacks; strict comparison is not causal because task sets/user framing differ"},
        {"issue": "R3", "original_problem": "100% defence claim omits source-honesty/current-record assumptions",
         "root_cause": "Source+freshness does not bind selected amount to record amount or establish external truth",
         "files_changed": ["scripts/report_round3.py", "src/ai2ai_guard/round3_neutral.py", "tests/test_round3.py", "research/VALIDATED_RESEARCH_REPORT.md"],
         "fix": "549/549 and 0/479 explicitly restricted to original evaluated conditions; 72/72 wrong-current passes preserved; new wrong releases emphasized, no post-hoc defence patch",
         "tests_performed": "Constructed wrong-source-current counterexample; denominators; original normalized metrics and corrupt cohort reconstructed from saved outputs",
         "results": "Neutral source+freshness: " + (ratio(nm["defences"]["source_freshness"]["wrong_report_release_among_wrong_reports"]) + " wrong reports released" if nm else "pending"),
         "remaining_limitations": "No universal prevention, external authentication or arbitrary prose/consumer guarantee; constructed bad-record inputs distinguished from real compromises"},
        {"issue": "R4", "original_problem": "Long repetitive manuscript and duplicate normalized tables",
         "root_cause": "Successive implementation updates accumulated in one report",
         "files_changed": ["scripts/report_round3.py", "scripts/run_research_pipeline.py", "scripts/export_review_report.py", "research/ROUND3_APPENDIX.md"],
         "fix": "Four plain abstract findings; eight main sections, three compact tables and two figures; normalized/detailed evidence moved to appendix/CSV; references retained",
         "tests_performed": "Report number/source bindings, table-column parsing, portable Word/PDF semantic joins, export hashes and visual review receipt",
         "results": "Canonical manuscript and separately labelled technical appendix generated from one data object",
         "remaining_limitations": "Final author edits require re-export/review; prior reports remain historical archives"},
        {"issue": "R5", "original_problem": "Linguistic validation, authors and submission unconfirmed",
         "root_cause": "No signed native review/author details; Astra attempt lacks working access",
         "files_changed": ["research/review_resolution/ROUND3_NATIVE_REVIEW.csv", "submission/final-review/SUBMISSION_CHECKLIST.md", "research/review_resolution/AUTHOR_CONFIRMATION.json", "research/VALIDATED_RESEARCH_REPORT.md"],
         "fix": "Prepared actual neutral-template bilingual review rows, retained unfilled wording sheet and author form, explicit package/checklist; no fictitious sign-offs",
         "tests_performed": "Unreviewed fields/anchor checks, packet preservation, report explicit pending status; no human/official-submission assertion",
         "results": "Files/preparation completed; native review and author identity still unconfirmed; automated Astra QA has zero returned scores",
         "remaining_limitations": "Real external review, confirmed authors/affiliations and official submission receipt require human/access input"},
    ]
    for row in records:
        row["status"] = statuses[row["issue"]]
    lines = ["# Round 3 remediation report\n", "This is an implementation/evidence ledger, not another main manuscript.\n"]
    for row in records:
        lines.append(f"## {row['issue']} — {row['status']}\n")
        for key in ("original_problem", "root_cause", "files_changed", "fix", "tests_performed", "results", "remaining_limitations"):
            value = ", ".join(row[key]) if isinstance(row[key], list) else row[key]
            lines.append(f"- **{key.replace('_', ' ')}:** {value}")
        lines.append("")
    lines += ["## Validation and spending\n",
              "Final automated command results are recorded in `results/round3/validation_execution.json`; "
              "PDF visual/content review is hash-bound in `results/review_v3/EXPORT_REVIEW.json`. "
              "Neither receipt is native-speaker or author sign-off.\n",
              f"Aggregate conservative accounting is US${data['cost']['aggregate_accounted_usd']:.8f} / "
              f"US${data['cost']['cap_usd']:g}, including unresolved reservations; not a provider invoice. "
              "No observed answer was replaced to make the outcome more successful.\n"]
    return {"issues": records, "submission_confirmed": False, "human_linguistic_validation_claimed": False}, "\n".join(lines).rstrip() + "\n"


def checklist(data):
    neutral = data["round3"]["neutral"]
    mark = "x" if neutral["status"] == "COMPLETE" else " "
    return (
        "# Submission checklist — not a submission receipt\n\n"
        "- [x] Preserve original raw outputs, protocols and archived manuscripts.\n"
        "- [x] Recompute wording/language counts and grouped interactions; retain ambiguous schema cases.\n"
        f"- [{mark}] Collect and separately report the 180-case neutral-prompt pilot.\n"
        "- [x] Prepare canonical manuscript, technical appendix and reproducible PDF/Word exporter.\n"
        "- [x] Implement automated factor, denominator, data-join and export integrity checks.\n"
        "- [ ] Obtain independent native-speaker sign-off; existing sheets are UNREVIEWED.\n"
        "- [ ] Confirm author display names, affiliations, order and permission to publish.\n"
        "- [ ] Externally adjudicate ambiguous outputs if claiming broader semantic validity.\n"
        "- [ ] Human proofread the final PDF/Word after author and language-review edits.\n"
        "- [ ] Complete the official submission process and retain its actual confirmation/receipt.\n\n"
        "Current files: `Authority_Language_Final.pdf` and `.docx`; main source "
        "`research/VALIDATED_RESEARCH_REPORT.md`; detailed appendix `research/ROUND3_APPENDIX.md`. "
        "The PDF review receipt is an AI layout/content check, not author or linguistic validation. "
        "A GitHub PR/push is not official submission.\n"
    )
