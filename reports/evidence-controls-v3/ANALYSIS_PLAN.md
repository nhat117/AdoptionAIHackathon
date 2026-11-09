# v3 analysis plan

Written and committed before any paid v3 game. `analyze.py` implements exactly this plan; any later analysis is labelled exploratory.

## Unit and outcomes

- **Unit:** one whole game. Seeds are the replicates. The nine agents in a game influence each other and are never counted as separate samples.
- **Section 5b outcome:** `other_recipients_correct_action_rate`, the share of the 8 non-witness agents who acted correctly. Every 5b game is a disaster game.
- **Section 6 cells:** Sonnet in disasters, Terra in disasters and Terra with no disaster, 4 seeds each. Sonnet with no disaster is excluded in advance as a predictable null.
- **Section 6 outcome:** `correct_action_rate` over the 9 recipients, plus `round1_wrong`, `reversals` and `irreversible_round1_errors`.

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

## What each outcome allows us to say

- **Proof ≫ unverified ≈ text:** agents respond to verification, not content.
- **Proof ≈ unverified ≫ text:** the structured content does the work, and fake notes are a real risk.
- **Proof > unverified > text:** both matter; report each step's size.
- **Different patterns for Sonnet and Terra:** the effect depends on the model or host; no general claim.
