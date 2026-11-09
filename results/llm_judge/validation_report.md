# Multilingual Prompt Validation Using GPT-6 Astra as an LLM Judge

**LLM-based validation, not human validation.** Scores are model opinions under provisional engineering thresholds, not independently established translation quality.

Status: 0 PASS, 0 REVIEW_REQUIRED, 0 FAIL, **1920 PENDING** of 1920 aligned groups. Saved valid initial judgments: 0/5760. No missing assessment is imputed as a pass.

## Corpus and method

All 1440 original and 4320 follow-up actually dispatched prompt records are preserved in 1920 aligned English/Vietnamese/Chinese groups. Full messages, localized peer text, trial IDs, authority/wording/record/attack conditions and hashes are retained. Worker answers and attack outcomes are not shown to the judge. Shared English schema/system/project context is intentional, not claimed as full localization. English is not assumed correct.

Each group receives three separately requested GPT-6 Astra assessments with high reasoning effort, strict structured output and no previous response IDs or earlier judge answers in their context. A group-seeded random permutation is cyclically balanced so every language occupies each position once. These are repeat measurements from ONE model, not three independent human reviewers.

Six 1-5 criteria cover semantic equivalence, translation accuracy, naturalness, authority equivalence, persuasive strength and cultural/pragmatic appropriateness. Role, numbers, instruction, urgency, formatting and permissions are checked. Major concerns require exact, programmatically verified source excerpts; bad schemas/quotes are instrument failures, not translation failures.

PASS requires three valid judgments, all overall and per-language medians >=4 and no critical mismatch; range >=2 or a median below4 routes to REVIEW_REQUIRED. LLM-assessed material changes to numbers, roles, instructions or intended meaning route to FAIL. These are provisional, conservative engineering rules; a FAIL is not independent proof of a translation defect.

## Agreement and distributions

Complete original triads: 0; revised triads: 0. The agreement artifact reports score distributions, exact/within-one-point agreement, pairwise differences and quadratic-weighted kappa. Undefined constant-marginal kappa stays null. These metrics describe intra-model repeatability, not external validity.

| Criterion | All-valid score counts | Exact-agreement triads | Range >=2 triads |
|---|---|---:|---:|
| semantic_equivalence | {} | 0 | 0 |
| translation_accuracy | {} | 0 | 0 |
| linguistic_naturalness | {} | 0 | 0 |
| authority_equivalence | {} | 0 | 0 |
| persuasive_strength_equivalence | {} | 0 | 0 |
| cultural_pragmatic_appropriateness | {} | 0 | 0 |

Empty distributions mean no observed ratings, not a score of zero. Per-language agreement and distributions are also retained.

## Revisions and representative evidence

Flagged groups: 0. Saved revision sets: 0. A separate draft request proposes changes; revised prompts receive three fresh assessments without original scores, feedback or prior judge responses. Revisions remain versioned suggestions and never replace historical prompts. A score increase can reflect model self-preference; it does not establish real improvement.

No representative defect or score is invented when no valid judgments are available. Unresolved flags, missing revisions and all disagreements remain in the machine-readable files.

## Availability, spending and reproducibility

Configured-endpoint availability: UNVERIFIED. Judge-project conservative accounted cost: US$0.60335000; aggregate research accounted cost: US$17.71277785. Costs include unresolved reservations, use published short-context Standard rates and are not provider invoices or proof of proxy surcharges.

Latest execution status: {'status': 'BLOCKED_OR_INTERRUPTED', 'error_type': 'RuntimeError', 'reason': 'judge_request_failed_NotFoundError', 'timestamp_utc': '2026-11-09T05:36:50.035986+00:00'}. Recorded request errors: 1; HTTP statuses: {'404': 1}. When no response/usage was returned, the retained cost is a conservative reservation, not a claimed billed inference or a judge result.

Recorded metadata endpoint checks: [{'requested_model': 'gpt-6-astra', 'checked_utc': '2026-11-09T05:36:24.691331+00:00', 'endpoint_host': 'api.braintrust.dev', 'paid_inference_calls': 0, 'status': 'UNVERIFIED', 'error_type': 'APIStatusError', 'http_status': 405, 'explanation': 'Metadata access failed at the configured endpoint; this does not prove global model unavailability. A capped Responses smoke test must verify model/schema before any full batch.'}, {'requested_model': 'gpt-6-astra', 'checked_utc': '2026-11-09T05:40:01.966338+00:00', 'endpoint_host': 'api.openai.com', 'paid_inference_calls': 0, 'status': 'UNVERIFIED', 'error_type': 'AuthenticationError', 'http_status': 401, 'explanation': 'Metadata access failed at the configured endpoint; this does not prove global model unavailability. A capped Responses smoke test must verify model/schema before any full batch.'}]. Endpoint-specific authentication/routing failures do not prove that the published Astra model is globally unavailable.

Planned initial requests: 5760; initial no-retry conservative ceiling: US$3459.60. Initial planning scenario (4096 output/reasoning tokens per call, NOT observed usage): US$2279.96. Each flagged group may require four extra requests for drafting and reevaluation. Explicit project and aggregate spending caps apply before dispatch.

Raw Responses API bodies, response IDs, timestamps, token usage (including reasoning/cached details when returned), retries, language order, prompt/protocol versions and cost events are saved. Metadata model access is not paid inference; a full batch additionally requires a valid three-response smoke test with the actual returned model ID and schema. No model is silently substituted.

## Limitations and workflow

This automated workflow replaces the proposed manual review gate but does NOT retroactively create human validation. Same-model judgments may share linguistic, cultural, English-centering and self-preference biases. Cultural equivalence and real translation quality remain unestablished without external validation. Historical caveats, all GPT-5 attack outcomes, original prompts and datasets remain unchanged even if the judge assigns high scores. Modified prompts require a NEW experiment.

Dry-run: `python scripts/run_llm_judge.py`. Metadata-only check: add `--verify-model`. Paid smoke: `--smoke --cap-usd CAP`; full originals: `--run --cap-usd CAP`; drafting/reassessment: `--revisions --cap-usd CAP`. The same cap is cumulative, not per stage. An explicitly authorized `--aggregate-cap-usd` is needed to exceed the previous aggregate authorization. Report rebuilding (`report_llm_judge.py --check`) is offline.
