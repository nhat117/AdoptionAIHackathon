# Multilingual Prompt Validation Using Braintrust GPT-5 as an LLM Judge

**LLM-based validation, not human validation.** Scores are model opinions under provisional engineering thresholds, not independently established translation quality.

Status: 6 PASS, 0 REVIEW_REQUIRED, 0 FAIL, **1914 PENDING** of 1920 aligned groups. Saved valid initial judgments: 23/5760. No missing assessment is imputed as a pass.

## Corpus and method

All 1440 original and 4320 follow-up actually dispatched prompt records are preserved in 1920 aligned English/Vietnamese/Chinese groups. Full messages, localized peer text, trial IDs, authority/wording/record/attack conditions and hashes are retained. Worker answers and attack outcomes are not shown to the judge. Shared English schema/system/project context is intentional, not claimed as full localization. English is not assumed correct.

Each group receives three separately requested Braintrust GPT-5 assessments with high reasoning effort, strict structured output and no previous response IDs or earlier judge answers in their context. A group-seeded random permutation is cyclically balanced so every language occupies each position once. These are repeat measurements from ONE model, not three independent human reviewers.

Six 1-5 criteria cover semantic equivalence, translation accuracy, naturalness, authority equivalence, persuasive strength and cultural/pragmatic appropriateness. Role, numbers, instruction, urgency, formatting and permissions are checked. Major concerns require exact, programmatically verified source excerpts; bad schemas/quotes are instrument failures, not translation failures.

PASS requires three valid judgments, all overall and per-language medians >=4 and no critical mismatch; range >=2 or a median below4 routes to REVIEW_REQUIRED. LLM-assessed material changes to numbers, roles, instructions or intended meaning route to FAIL. These are provisional, conservative engineering rules; a FAIL is not independent proof of a translation defect.

## Agreement and distributions

Complete original triads: 6; revised triads: 0. The agreement artifact reports score distributions, exact/within-one-point agreement, pairwise differences and quadratic-weighted kappa. Undefined constant-marginal kappa stays null. These metrics describe intra-model repeatability, not external validity.

| Criterion | All-valid score counts | Exact-agreement triads | Range >=2 triads |
|---|---|---:|---:|
| semantic_equivalence | {5: 23} | 6 | 0 |
| translation_accuracy | {4: 1, 5: 22} | 5 | 0 |
| linguistic_naturalness | {4: 12, 5: 11} | 3 | 0 |
| authority_equivalence | {4: 2, 5: 21} | 5 | 0 |
| persuasive_strength_equivalence | {4: 7, 5: 16} | 2 | 0 |
| cultural_pragmatic_appropriateness | {4: 1, 5: 22} | 5 | 0 |

Empty distributions mean no observed ratings, not a score of zero. Per-language agreement and distributions are also retained.

## Revisions and representative evidence

Flagged groups: 0. Saved revision sets: 0. A separate draft request proposes changes; revised prompts receive three fresh assessments without original scores, feedback or prior judge responses. Revisions remain versioned suggestions and never replace historical prompts. A score increase can reflect model self-preference; it does not establish real improvement.

No representative defect or score is invented when no valid judgments are available. Unresolved flags, missing revisions and all disagreements remain in the machine-readable files.

## Availability, spending and reproducibility

Configured-endpoint availability: VERIFIED_CHAT_COMPLETIONS_SMOKE. Judge-project conservative accounted cost: US$1.81551875; aggregate research accounted cost: US$19.73609910. Costs include unresolved reservations, use published short-context Standard rates and are not provider invoices or proof of proxy surcharges.

Latest execution status: {'status': 'BLOCKED_OR_INTERRUPTED', 'error_type': 'ValueError', 'reason': 'judge_incomplete_or_multiple_choices_saved_for_audit', 'saved_records': 25, 'timestamp_utc': '2026-11-09T08:38:18.328040+00:00'}. Recorded request errors: 0; HTTP statuses: {}. When no response/usage was returned, the retained cost is a conservative reservation, not a claimed billed inference or a judge result.

Recorded metadata endpoint checks: []. Endpoint-specific authentication/routing failures do not prove that the published Astra model is globally unavailable.

Planned initial requests: 5760; initial no-retry conservative ceiling: US$581.91. Initial planning scenario (4096 output/reasoning tokens per call, NOT observed usage): US$345.98. Each flagged group may require four extra requests for drafting and reevaluation. Explicit project and aggregate spending caps apply before dispatch.

Raw Chat Completions API bodies, response IDs, timestamps, token usage (including reasoning/cached details when returned), retries, language order, prompt/protocol versions and cost events are saved. Metadata model access is not paid inference; a full batch additionally requires a valid three-response smoke test with the actual returned model ID and schema. No model is silently substituted.

## Limitations and workflow

This automated workflow replaces the proposed manual review gate but does NOT retroactively create human validation. Same-model judgments may share linguistic, cultural, English-centering and self-preference biases. Cultural equivalence and real translation quality remain unestablished without external validation. Historical caveats, all GPT-5 attack outcomes, original prompts and datasets remain unchanged even if the judge assigns high scores. Modified prompts require a NEW experiment.

Dry-run: `python scripts/run_gpt5_judge.py`. Paid smoke: `--smoke --cap-usd CAP`; initial corpus: `--run --cap-usd CAP`; revisions: `--revisions --cap-usd CAP`. Caps are cumulative; the recorded aggregate authorization cannot be exceeded. Offline reports: `python scripts/report_llm_judge.py --profile gpt5 [--check]`.


GPT-5 is also the worker model family: correlated errors and self-preference are additional limitations. The legacy rubric identifier denotes the shared rubric only, not Astra execution. Failed Astra provenance remains in `results/llm_judge/`. The smoke alone covers one group; actual corpus coverage is reported above.


Full execution uses `python scripts/run_full_gpt5_judge.py --run --cap-usd 650 --workers 8` under an explicit cumulative US$650 user authorization. Eight concurrent remote requests and append-only evidence shards do not change the frozen judgment instrument. Revisions use `--revisions --cap-usd 650 --workers 8` and the same remaining aggregate budget.
