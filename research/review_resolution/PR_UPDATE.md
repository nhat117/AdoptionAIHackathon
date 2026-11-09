## Scope

### Current user-requested scope: random sampling instead of full judging

**Collection outcome:** all **288 planned initial replies** were saved;
**286** passed schema/rubric/exact-evidence checks. The sample has **94 provisional
PASS / 2 PENDING** groups. Two non-exact-quote replies remain instrument failures,
not translation failures; no case was replaced or rescored. No complete group
triggered revision drafting. Neither full-sample validation nor full-corpus/human
validation is claimed. Sample-project conservative accounting is
**US$22.17641750 / US$60**; aggregate accounting, including earlier costs and
unresolved error reservations, is **US$41.91251660 / US$650**, not an invoice.

The active profile is a frozen **5% stratified random sample: 96 aligned groups,
288 initial GPT-5 judgments**. One group is drawn uniformly from each of 96
20-group cohort/role/wording/record/clean-attack strata. Selection excludes prior
judge ratings and worker outcomes; every group has 5% inclusion probability.
Unselected groups are labelled NOT SAMPLED rather than passed or failed.

The new workflow keeps three balanced language-order requests, strict base JSON
schema, exact-evidence validation, agreement and separately versioned/blinded
revision reassessment. It uses high reasoning with a 16384-token bound and a
US$60 sampled-project allocation within the existing US$650 aggregate approval.
Earlier truncation, quote-check and HTTP400 evidence/costs remain preserved; no
ratings are pooled across attempts. See `SAMPLED_LLM_VALIDATION.md` and the actual
coverage/status in `results/llm_judge_sample/validation_report.md`. This is sampled
LLM-based validation, not full-corpus/human validation or official submission.
The prepared sampled workflow passes **404 tests on Python 3.11 and 3.12**,
lint, all 57 offline analysis artifacts and six portable export checks. The
current manuscript remains five pages. The initial planning estimate is US$28.6875
(8000 completion/reasoning tokens per call, not observed usage); the US$60 sample
cap also bounds retries and flagged-group revisions. These preparation checks
are not a claim that the sampled judgments have already completed.

### Active judge switched to Braintrust GPT-5

**Subsequent full-run approval:** the user explicitly authorized **US$650 total**
cumulative research spending. The original US$20 authorization is preserved;
the separate approval covers prior costs, new judgments, retries and revisions.
An execution-only extension (`run_full_gpt5_judge.py`) supports eight concurrent
remote requests, atomically enforced shared spending, safe recovery of saved raw
answers, and append-only evidence shards below GitHub file-size limits.
The original model, rubric, prompts, language randomization and inference
settings remain frozen. Actual coverage/status remains in the generated report;
launching a full run is not a claim of completed validation. The older smoke
allocation below documents the earlier stage and is not the new authorization.
The execution extension passes **390 tests on Python 3.11 and 3.12**, including
concurrent cap enforcement, sharded evidence preservation and no-paid-call
recovery/resume tests. Lint and offline report/export checks pass.

The user-requested switch uses a separate `braintrust-gpt5-multilingual-v1`
profile and the working Braintrust **Chat Completions** route, not the failed
Astra Responses route. See `GPT5_JUDGE_SWITCH.md` and
`results/llm_judge_gpt5/validation_report.md` for actual smoke status and coverage.
Strict structured output, three balanced language-order requests, exact-evidence
validation, agreement and versioned/blinded reassessment remain supported.
Raw API bodies and all token/cost events are retained. The old Astra evidence,
its unresolved reservation and all worker outputs remain unchanged.

The smoke allocation is US$0.50, within the existing shared US$20 cap; full
5760-request judging is not funded by that remainder and is not claimed complete.
Using GPT-5 both as worker and judge adds same-model-family bias. This remains
**LLM-based validation, not human validation**. Native review, author confirmation
and official submission remain unconfirmed.

The Braintrust smoke completed successfully: **3/3 valid structured judgments**
from `gpt-5-2025-08-07` on one fixed trio, with a hash-bound smoke receipt.
This is transport/model/schema verification, not full-corpus linguistic validation.
**384 tests pass on Python 3.11 and 3.12**; lint and offline report/export checks pass.

### Round 3 scientific-validity correction

- **R1:** reanalyzed all 4320 answers with task-blocked wording×language interactions (18 Holm-corrected contrasts per scoring definition). Strict no-record counts are 25/6/64, 66/46/50, 51/59/43 (/80 each). The review's 66/48/50 and 51/59/44 are raw numeric-field diagnostics including three contradictory ABSTAIN+nonnull-target outputs. Both definitions and all ambiguous transcripts are retained; no universal language-persuasion claim.
- **R2:** completed **180/180** neutral-prompt fake-record calls on the expected `gpt-5-2025-08-07`, minimal reasoning/512 tokens. Exact existing neutral system/user framing/schema, no new strict source warning. **71 known wrong reports, 7 unsupported record attributions, 1 invalid-format output**. All outputs retained; strict-pilot results remain separate.
- **R3:** unchanged source+freshness rule allowed **2/71** known wrong neutral reports, blocking 69/71 and falsely blocking 0/45 known correct reports. Original 549/549 and 0/479 are explicitly conditional; separate corrupt-current inputs pass 72/72 wrong reports. No post-hoc defence patch to improve the headline.
- **R4:** four plain abstract findings, eight main sections, **three main tables/two figures**. Normalized tables, detailed statistics, denominator checks and source audits moved to `ROUND3_APPENDIX.md` and machine-readable appendices. Valid references retained; OpenAI documentation citation uses APA author/date form.
- **R5:** actual neutral-template bilingual sheet prepared (6 rows), existing 24-row wording sheet retained, all UNREVIEWED. Author information and official submission remain unconfirmed. Final PDF/Word and a submission checklist are prepared; no fictitious review/sign-off.
- Remediation statuses: **R1–R4 Fixed; R5 Partially Fixed** (preparation done, external review/author/submission actions pending). Each issue's root cause, changed files, tests, results and limitations are mapped in `ROUND3_REMEDIATION.md` / `results/round3/remediation.json`.
- Neutral pilot incremental token-based accounting is US$0.1984725. Aggregate conservative accounting including the unresolved Astra reservation is **US$17.71277785 / US$20**, not a provider invoice. Historical data and archive hashes remain checked.
- Final Round 3 local checks: **366 tests pass on Python 3.11 and 3.12**, lint/data/archive checks pass, all 39 analysis artifacts and six portable export artifacts reproduce/check. The five-page manuscript's three tables/two figures were inspected; native review, authors and official submission are still not claimed complete.

Earlier engineering stages below remain evidence, not competing main manuscripts or a claim that the blocked Astra assessment ran successfully.

### Astra LLM-judge pipeline update — implementation complete, evaluation blocked

- Official OpenAI Python SDK/Responses integration targets exactly `gpt-6-astra`, high reasoning and strict structured JSON. No model substitution.
- Extracted **1920 aligned groups / 5760 actual dispatched prompt records** with raw text, condition/role/variant IDs and source hashes. Three separate position-balanced randomized evaluations per group; English is not treated as gold.
- Implemented evidence-bound rubric validation, provisional median/disagreement/critical-change outcomes, intra-model score distributions/agreement/kappa, capped exponential retries, durable responses/accounting, separate versioned revision drafts and blinded reevaluation.
- All six requested result artifacts are generated reproducibly, but **all 1920 groups remain PENDING**. Zero judge responses/scores were returned.
- Actual access checks: Braintrust metadata HTTP405, its Responses smoke HTTP404, direct OpenAI metadata HTTP401 with the configured credential. The smoke stopped; no unsupported full batch was issued. The failed request's conservative reservation is retained, not described as verified billed inference.
- The report adds the exact requested LLM-validation section, explicitly not human validation. Automated assessment replaces the proposed manual QA gate without erasing historical linguistic/cultural caveats or changing a GPT-5 outcome.
- A working Responses endpoint and a valid rotated environment key are required to resume. Full initial evaluation requires 5760 requests; the saved Standard-rate estimate and explicit cumulative spending caps remain visible.

The completed engineering/data work below remains separately scoped; it is not being presented as completed Astra judging.

### Continuation update

- **4320/4320** new wording-balanced workers completed without collection errors: 20 reused tasks × 4 roles × 3 variants × 3 languages × 3 records × clean/attack. Original data/templates and shared log prefixes are preserved.
- Strict attacked relay counts by wording are absent **95/240, 162/240, 153/240**; stale **15/240, 83/240, 87/240**; current **1/240, 2/240, 3/240**. These are literal-wording results, not causal authority/culture effects. Complete fixed-task inference and key-case sensitivity are exported separately.
- Source-only blocks **601/601** strict peer relays in this new cohort; source+freshness blocks **1809/1809** strict wrong-budget reports with **0/1430** false blocks of correct reports. These remain diagnostics, not secure provenance guarantees. New blind-monitor evaluations were not collected or extrapolated.
- Incremental accounted cost **US$4.82995**, aggregate **US$16.91095535 / US$20**. The earlier four-stage study below retains its original counts/cost scope.
- Fixed the Linux CI export failure: preserve and verify published artifact hashes and renderer inputs, exact Word text/images and ordered PDF content instead of requiring platform-specific PNG regeneration to match. Corrupted/forged content regressions remain enforced.
- Current local validation: **339 tests pass on both Python 3.11 and 3.12**, with lint, original-data/archive integrity, analysis freshness and portable Word/PDF checks passing. The updated ten-page PDF includes the new cohort and its sixth figure.
- Prepared 24 unfilled bilingual review rows, sign-off instructions and an empty author confirmation form. **Human native review and confirmed authorship remain pending**; no validation inferred from dismissed questions.

The following details describe the original `4faa911` review update; current report/exports also include the separate continuation.

Implements the engineering and analysis actions from the full follow-up review (N1–N11), maps A1–A9, reruns the required evaluations, and generates one canonical report. **This does not claim that outstanding human validation or all research limitations are resolved.**

Issue-by-file plan: `research/review_resolution/PLAN.md`.
Implemented/validated/pending ledger: `research/review_resolution/STATUS.md`.

## Code and analysis

- Versioned strict/normalized outcome scoring separates peer-number relay, stale-record reliance, current-record grounding, abstention and other errors.
- Deterministic source-only and source+freshness baselines explicitly handle missing, malformed, ambiguous and deceptive provenance. Worker abstentions are separate. Experimental trusted-record origin is not external authentication.
- Record-stratified language/authority rates, matched task-bootstrap intervals, exact task sign-flip tests, 32 exploratory contrasts/interactions and Holm adjustment. No IID trial-level or general causal authority/culture claims.
- Original blind monitor unchanged (AST regression test); new policy-aware blind monitor receives visible evidence and task policy, never evaluator truth. Information-access differences are explicit.
- Detector v2.2 handles reviewed amount labels, multilingual written amounts and local qualification scope. Fifty known-answer cases pass. Development on saved false positives is disclosed; v2.1 and its nine false positives are archived, not hidden.
- New immutable protocols, durable API-body saving, append-only cost accounting, shared old/new cap enforcement and offline reproducible reporting/export checks.

## Verified findings

- Main GPT-5 study: **90 strict** peer-number relays; **91** with separately labelled key-case normalization. All 91 normalized outputs say `peer`; the review's missing-source example uses `Evidence` instead of `evidence`.
- Source-only blocks 91/91 normalized relays but passes **458 stale-record uses**. Source+freshness blocks those too, with **0/479 false blocks** of correct reports in this saved cohort. Neither result proves secure provenance.
- The requested strict language counts reproduce: absent EN/VI/ZH **23/80, 11/80, 41/80**; stale **11/80, 0/80, 3/80**; current **0/80, 0/80, 1/80**. Chinese/English directions reverse by record condition; the relevant Holm-adjusted tests do not justify a significance claim.
- Historical Gemma-worker/GPT-5-monitor cohort: original blind monitor blocks **0/150 wrong budgets**, falsely blocks **115/450 correct reports**, and abstains on 144 wrong reports.
- New monitor comparison reuses all 1440 GPT-5 workers: original blocks **78/549 wrong reports**; improved blocks **241/549**, still allows **308/549**, and falsely blocks **4/479** correct reports (normalized reference). It is not presented as an effective replacement for deterministic freshness checking.
- Provenance pilot: **36 workers + 72 monitor evaluations**, no observed strict false-record attributions. No successful bypass or incremental checker benefit is claimed.
- Boundary committee: expense **13000**, true cap **12000**, planted cap **18000**; **40 terminal games, five per cell**. No final planted-cap reports, one wrong clean-control decision, two unresolved games. **839/840 responses** returned; the failed turn is retained as a non-vote, not replaced.

## Execution, cost and preservation

**3828 attempted calls; 3827 returned model bodies.** Aggregate accounted cost **US$12.08100535 / US$20**, including original spending and the unresolved reservation. This is not a provider invoice. No original worker answer was regenerated.

All **271 protected original data/result files** remain byte-identical. Earlier canonical Markdown/Word/export metadata are archived. Raw prompts, response IDs, actual model IDs, usage, versions, source hashes and retained failures are available under `results/review_v3/`.

## Deliverables and checks

- Canonical source: `research/VALIDATED_RESEARCH_REPORT.md`.
- Derived PDF/Word: `submission/final-review/Authority_Language_Final.pdf` and `.docx`.
- Five SVG/PNG figures, CSV contrasts/rates/translation inventory and machine-readable analysis.
- **327 tests passed locally on Python 3.11 and 3.12**; lint, offline analysis/export freshness, baseline integrity and original-audit checks passed.
- CI performs no inference and verifies preserved inputs and current deliverables rather than rewriting historical result files.

## Explicitly outstanding

- Native-speaker Vietnamese/Chinese review **REQUIRED**, not performed. AI inspection and ten sampled abstentions are not human validation.
- The wording-balanced authority replication is now completed in the continuation above; inference remains restricted to the tested fixed wordings and tasks.
- Independent held-out prose adjudication, broader models/tasks and external record authentication remain unvalidated.
- Author names/affiliations require confirmation; no official hackathon submission or merge has been performed.
- The old dashboard remains historical, explicitly labelled; it is not represented as current results.

## Current human handoff

`research/review_resolution/NATIVE_REVIEW_PACKET.csv` has 24 unfilled bilingual rows. `HUMAN_SIGNOFF.md` gives reviewer instructions; `AUTHOR_CONFIRMATION.json` contains no inferred identity. These human actions remain pending after the technical continuation.
