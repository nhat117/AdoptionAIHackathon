# Round 3 remediation report

This is an implementation/evidence ledger, not another main manuscript.

## R1 — Fixed

- **original problem:** Pooled language claims hide wording-dependent reversals
- **root cause:** Three fixed translations/wordings are not a language population; reviewer counts also include inconsistent ABSTAIN numeric fields
- **files changed:** src/ai2ai_guard/round3_analysis.py, scripts/report_round3.py, tests/test_round3.py
- **fix:** Strict and raw-field counts separated; 20-task blocked wording×language interactions, bootstrap intervals, exact sign-flip/Holm tests; unsupported general ranking removed
- **tests performed:** Raw-data golden matrices, 3 contradictory-output audit, synthetic paired-interaction known answer; full suite/receipts linked below
- **results:** Strict absent counts 25/6/64, 66/46/50, 51/59/43; numeric-field counts reproduce review 25/6/64, 66/48/50, 51/59/44. See all 18 contrasts per definition.
- **remaining limitations:** Post-review exploratory; 20 historical tasks, fixed wordings, unreviewed translations, sign-symmetry assumptions; no causal culture claim

## R2 — Fixed

- **original problem:** Strict-record pilot cannot establish neutral-worker resistance
- **root cause:** The 36-case pilot adds explicit record-only policy and operational framing
- **files changed:** configs/round3-neutral-v1.json, src/ai2ai_guard/round3_neutral.py, scripts/run_round3_neutral.py, src/ai2ai_guard/round3_analysis.py, tests/test_round3.py
- **fix:** 180-factor-complete neutral calls; literal neutral system/user task/schema, same GPT-5 settings, reused attack texts; separate strict and neutral metrics
- **tests performed:** Exact neutral-prompt identity, 180 unique factor cells, source-boundary and metric-denominator known answers; raw response joins and model ID checks
- **results:** 180/180 saved; 71 wrong reports, 7 unsupported record attributions, 1 unknown formats/cases
- **remaining limitations:** Ten historical tasks, one model, finite machine-authored attacks; strict comparison is not causal because task sets/user framing differ

## R3 — Fixed

- **original problem:** 100% defence claim omits source-honesty/current-record assumptions
- **root cause:** Source+freshness does not bind selected amount to record amount or establish external truth
- **files changed:** scripts/report_round3.py, src/ai2ai_guard/round3_neutral.py, tests/test_round3.py, research/VALIDATED_RESEARCH_REPORT.md
- **fix:** 549/549 and 0/479 explicitly restricted to original evaluated conditions; 72/72 wrong-current passes preserved; new wrong releases emphasized, no post-hoc defence patch
- **tests performed:** Constructed wrong-source-current counterexample; denominators; original normalized metrics and corrupt cohort reconstructed from saved outputs
- **results:** Neutral source+freshness: 2/71 (2.8%) wrong reports released
- **remaining limitations:** No universal prevention, external authentication or arbitrary prose/consumer guarantee; constructed bad-record inputs distinguished from real compromises

## R4 — Fixed

- **original problem:** Long repetitive manuscript and duplicate normalized tables
- **root cause:** Successive implementation updates accumulated in one report
- **files changed:** scripts/report_round3.py, scripts/run_research_pipeline.py, scripts/export_review_report.py, research/ROUND3_APPENDIX.md
- **fix:** Four plain abstract findings; eight main sections, three compact tables and two figures; normalized/detailed evidence moved to appendix/CSV; references retained
- **tests performed:** Report number/source bindings, table-column parsing, portable Word/PDF semantic joins, export hashes and visual review receipt
- **results:** Canonical manuscript and separately labelled technical appendix generated from one data object
- **remaining limitations:** Final author edits require re-export/review; prior reports remain historical archives

## R5 — Partially Fixed

- **original problem:** Linguistic validation, authors and submission unconfirmed
- **root cause:** No signed native review/author details; Astra attempt lacks working access
- **files changed:** research/review_resolution/ROUND3_NATIVE_REVIEW.csv, submission/final-review/SUBMISSION_CHECKLIST.md, research/review_resolution/AUTHOR_CONFIRMATION.json, research/VALIDATED_RESEARCH_REPORT.md
- **fix:** Prepared actual neutral-template bilingual review rows, retained unfilled wording sheet and author form, explicit package/checklist; no fictitious sign-offs
- **tests performed:** Unreviewed fields/anchor checks, packet preservation, report explicit pending status; no human/official-submission assertion
- **results:** Files/preparation completed; native review and author identity still unconfirmed; automated Astra QA has zero returned scores; active Braintrust GPT-5 profile: 0/288 valid initial judgments, NOT_CHECKED; LLM-based, not human validation
- **remaining limitations:** Real external review, confirmed authors/affiliations and official submission receipt require human/access input

## Validation and spending

Final automated command results are recorded in `results/round3/validation_execution.json`; PDF visual/content review is hash-bound in `results/review_v3/EXPORT_REVIEW.json`. Neither receipt is native-speaker or author sign-off.

Aggregate conservative accounting is US$19.73609910 / US$650, including unresolved reservations; not a provider invoice. No observed answer was replaced to make the outcome more successful.
