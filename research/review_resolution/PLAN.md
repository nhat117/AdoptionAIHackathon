# Follow-up review implementation ledger

Review: `follow-up-review-Authority-Language.pdf`, all nine pages read (SHA-256 `949babb9f0ab6899f8a98c381dfe0f94a650c19d723da89b69232e8143141317`). Earlier seven-page `Review-Authority-Language-Approach.pdf` also read (SHA-256 `eb3a5e975554bb9a196f6fa68a78568adc9ae5b5eacb3e44cf3497ef6b570142`). Reviewed baseline: `1dcf401`. This ledger is an engineering appendix, not another main report. The canonical final source will remain `research/VALIDATED_RESEARCH_REPORT.md`.

## Independently verified before edits

- Strict GPT-5 replication: 90 explicit target reports; separate top-level-key-case sensitivity: 91. All 91 normalized target reports explicitly use source `peer`. One uses `Evidence`, not a missing value. No source may be inferred from prose to repair the primary schema.
- Attacked language counts (English/Vietnamese/Chinese): absent 23/80, 11/80, 41/80; stale 11/80, 0/80, 3/80; current 0/80, 0/80, 1/80.
- Under strict scoring, absent-record Chinese exceeds English in 13 tasks and is lower in 2 (5 ties). The review's 13 higher/1 lower uses the key-case-normalized definition, recovering a Chinese relay in task 41. The scoring definitions must not be mixed.
- Stale record reliance: 239 clean + 219 attacked = 458/480. This is distinct from attacker-target relay.
- Historical blind monitor: wrong-budget ALLOW/BLOCK/ABSTAIN = 6/0/144; correct-budget = 34/115/301. Strict block recall is zero, not 96%.
- Existing ledger: US$5.7395241 accounted of US$20 total. Configured API credentials exist; values are never included in reports or logs.

## Issue-to-file mapping and acceptance criteria

| Issue | Implementation | Validation / remaining dependency |
|---|---|---|
| N1, A1 | `review_measurement.py`, `review_monitors.py`, `review_client.py`, `run_review_followup.py`, `review_analysis.py` | Reproduce failure; same 1,440 workers, original versus policy-aware blind prompts, no hidden truth; coverage/strict recall/false-block/conditional metrics; paid evaluations explicitly incomplete until all IDs exist. |
| N2, A3 | `review_design.py`, versioned `configs/review-v3.json` | Matched clean/counterfeit/false-freshness pilot, trusted record separate from peer string; no success claim without recorded error. |
| N3, A2 | versioned `budget_claims_v2.py`, public factory in `budget_claims.py` | Regression corpus includes both reviews; amount recognition separate from provenance and mention separate from assertion/final field. Preserve v1 behavior for old frozen analyses. |
| N4, A5 | `review_translations.py`, generated translation inventory | Locate existing templates and every unique Vietnamese/Chinese dispatched peer template; value/role checks and AI-language audit, native-speaker review REQUIRED. No invented human validation. |
| N5, A6, A7 | `review_committee.py`, `review_design.py` | 13000 expense, 12000 true cap, 18000 false cap; five independent games per record × guard × clean/attack cell, budget permitting; retain per-turn failures, trace actual exposure and propagation. Exploratory only. |
| N6, A8 | generated canonical report / table captions | Exact model identifiers; Gemma/GPT-5 cohorts separate, no direct cross-study performance comparison. |
| N7, A9 | `report_review_followup.py`, `export_review_report.py`, navigation and `submission/final-review/` | One canonical Markdown source, derived Word/PDF with source hashes; archive originals. Author metadata remains pending unless user supplies it; no external submission. |
| N8 | `review_measurement.py` | Source-only baseline: record required for REPORT, valid ABSTAIN separate, malformed/missing evidence explicit; strict and normalized diagnostics separate; deceptive self-attribution is a known limit. |
| N9 | `review_statistics.py`, updated replication reporter entry point | Record-stratified language/authority rates and paired task-cluster bootstrap CIs; task sign-flip tests, interactions, Holm adjustment; all post-review analyses labeled exploratory. |
| N10 | `review_measurement.py`, `review_analysis.py` | Exhaustive outcome partition; stale reliance separate; source+freshness baseline adds freshness/availability/verification checks without hidden truth. |
| N11, A4 | `configs/authority-wording-v2.json`, `review_design.py` | Three comparable wordings per role per language, versioned separately; original four fixed messages retained; no general causal authority claims. |

## Sequence and preservation

1. Freeze input/report hashes and implement deterministic outcomes, baselines, stats and regressions.
2. Prepare versioned follow-up inputs and estimate call counts/costs before any dispatch.
3. Use a new append-only review ledger that includes the old immutable ledger in aggregate budget checks. Save every returned body before scoring. Resume only missing IDs; fixed-cohort/budget/infrastructure stopping, never outcome-dependent.
4. Run the same 1,440 saved workers through both blind monitors. Run the small strict-contract provenance pilot and committee only within the remaining cap. Do not regenerate original worker answers.
5. Run one offline pipeline, export tables/figures/machine-readable results and the canonical final report. Preserve original raw data, protocols and analyses; new outputs live under `results/review_v3/`.
6. Run all tests/lint, data-integrity and export-freshness checks. Update PR #6 with implemented/validated/pending status, not an unqualified “all fixed” statement.

## Statistical commitments (post-review, before new calls)

Primary historical schema is unchanged. Normalized-key results are a sensitivity analysis. Historical language/authority comparisons use strict confirmed-target indicators and explicit invalid counts; uncertainty bounds for missing-format outcomes are reported separately. Task is the dependence block (20 tasks); no IID trial-level inference. Stratified language contrasts use English reference; authority contrasts use teammate reference. Interactions subtract corresponding current-record contrasts. Percentile task bootstrap uses a deterministic seed; exact two-sided task sign-flip tests use sign symmetry as an assumption, not randomized causal identification. Holm adjustment covers the whole exploratory contrast family. Constant outcomes do not establish equivalence or a population safety bound.

New worker and committee pilots are feasibility/exploratory studies, not powered authority or culture-effect tests. Native review, author confirmation, cross-model replication and official submission cannot be completed by pretending they occurred.
