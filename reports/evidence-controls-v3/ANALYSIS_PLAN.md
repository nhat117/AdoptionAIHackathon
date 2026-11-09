# v3 analysis plan

Written and committed before any paid v3 game. `analyze.py` implements exactly this plan; any later analysis is labelled exploratory.

## Unit and outcomes

- **Unit:** one whole game. Seeds are the replicates. The nine agents in a game influence each other and are never counted as separate samples.
- **Section 5b outcome:** `other_recipients_correct_action_rate`, the share of the 8 non-witness agents who acted correctly. Every 5b game is a disaster game.
- **Section 6 cells:** Sonnet in disasters, Terra in disasters and Terra with no disaster, 4 seeds each. Sonnet with no disaster is excluded in advance as a predictable null.
- **Section 6 outcome:** `correct_action_rate` over the 9 recipients, plus `false_source_exposed_before_truth`, `exposed_wrong_before_truth`, `exposed_wrong_stays_then_evacuated`, `irreversible_before_truth_errors` and `active_at_truth`.

## Corrected timing and audit (before collection)

Truth is inserted after round 2. Round 1 has no peer messages; round 2 permits decisions on round-1 messages without truth; round 3 is the first possible authenticated decision. Direct source neighbors with an active round-2 decision are the source-exposed subset. Departures before truth remain in all nine-recipient final correctness denominators. A later evacuation after an exposed wrong stay is a descriptive action change, not proof that misinformation caused the earlier stay. Record every recipient's actions, first active source exposure, first active authenticated decision and evacuation round.

The same corrected prompt is used across all v3 arms. It explicitly requires `authenticated=true` for a capsule to count as verified, removing the inherited unconditional statement about capsule verification. Text/proof/unverified runs have independently generated trajectories; capsule content and relay rules are matched conditional on the same histories, not guaranteed realized paths or peer wording.

Audit every completed game by replaying raw responses and matching full views, transitions and outcomes exactly. Check frozen source/pack/ledger hashes, manifests, routes, reasoning, call counts and returned costs against the shared ledger. Enumerate all 72 planned jobs; distinguish completed, retained failures and unattempted future cells. A missing or empty plan is an error. Report selected-tranche completion separately from overall scheduling status.

Scheduling is frozen before collection: section 5b Sonnet, then Terra, then section 6 Sonnet and Terra. Within a model, use ascending seed/state and start the next matched cell only after all its arms finish. No retry or imputation. Concurrency is at most three arms (two for section 6), below the four-call ceiling. One shared collector lock and canonical run root prevent simultaneous v3 collectors or alternate roots resetting spend. The two prior ledgers are hash-matched to the original records; baseline is US$25.5456355, remaining cap US$9.4543645. Unknown billing halts; lack of room for a US$0.20 reservation stops collection. Full completion is not guaranteed.

## Contrasts

Within each model, paired by seed:

| Section | Treatment − control | Question |
|---|---|---|
| 5b | proof − unverified | Does the verified flag matter beyond the content? |
| 5b | unverified − text | Does the structured true content matter beyond plain testimony? |
| 5b | proof − text | Does the v2 Experiment 5 contrast replicate on held-out seeds? |
| 6 | delayed − none | Does late authenticated truth change actions, separately for disaster and safe? |

## Test

An exact two-sided sign-flip permutation test on the per-seed differences, with all 2ⁿ sign patterns. With 8 seeds, the smallest attainable p is 2/256 ≈ 0.008. With 4 seeds it is 2/16 = 0.125, so section 6 is reported **descriptively only**. Every result shows the per-seed numbers next to the p-value. No correction is applied across the three 5b contrasts; they are reported as three separate questions.

## Missing data

A failed or incomplete game removes its pair from that contrast. Report the number of complete pairs and list every failure. Nothing is retried or imputed. Results with fewer than 6 complete pairs in 5b are called inconclusive.

## Reporting alongside

For every condition, also report the miss, false-alarm and claim-following rates (see `reports/overnight-experiments/decision_rates.py`). Report Sonnet and Terra separately; they are never pooled.

## Exploratory patterns (not equivalence tests)

- **Proof ≫ unverified ≈ text:** a verification contribution is supported in these arms; a small content contrast does not establish zero content effect.
- **Proof ≈ unverified ≫ text:** structured unverified content can influence actions; similar observed rates do not establish equivalence or general attack success.
- **Proof > unverified > text:** both matter; report each step's size.
- **Different patterns for Sonnet and Terra:** the effect depends on the model or host; no general claim.
