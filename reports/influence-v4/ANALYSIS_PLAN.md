# v4 influence study: design and analysis plan

Written and committed before any paid v4 game. `analyze.py` implements this plan, and the runner records this file's hash in its frozen plan. Any other analysis is labelled exploratory.

## Why v4 exists

Experiments 1–3 could not show any effect. Agents had no way to tell true claims from false ones, staying and leaving paid the same at a 50% prior, and the prompt told agents to ignore labels. v4 fixes all three problems (method fixes 1, 3 and 7):

| Problem | v4 change |
|---|---|
| The only outcome was a stay/leave choice that never moved | Every decision also reports a **0–100 disaster belief** |
| Agents had no information of their own | Each recipient gets a **private sensor that is right 70% of the time** (seeded per scenario; 68.75% realised across the frozen games) |
| Labels couldn't matter at a 50/50 payoff | Payoffs are unchanged, so the decision point stays at 50%. A source tips an agent against its own sensor only if the agent trusts it more than a 70% sensor. |
| The prompt said labels carry no authority | The **warning sentence is now a factor**: present or absent. The two prompts differ by exactly that sentence. |
| Real political and religious figures were confounded | A **ladder of fictional roles**: ordinary teammate, team lead, certified emergency officer, official emergency management agency |

The prompt states the 50% prior and the sensor's accuracy, so a belief can be compared with a Bayesian reference.

## Design

16 held-out scenarios: evaluation seeds 2008–2011 × disaster yes/no × claim true/false. These seeds don't overlap with v3 (2000–2007) or any earlier run. English only, with fixed ring networks.

- **Pilot tier, 128 games:** teammate and official agency × warning present or absent × 16 scenarios × Sonnet and Terra.
- **Ladder tier, 128 games:** the two middle roles in the same design. Run it only if the pilot is clean.

## Outcomes

- **Primary:** `mean_belief_shift_toward_claim`, measured for the source's four direct neighbours. It is the change in belief from round 1 (before any message) to round 2 (the first decision after the source's message), signed so that a positive value means a move toward the claim. Neighbours who left in round 1 have no round-2 belief; the count is reported. The round-2 view also holds neighbours' round-1 messages, so the shift is not caused by the source alone. Those messages are matched across arms, so contrasts still compare like with like.
- **Secondary:**
  - `conflict_tipping_rate`: among recipients whose sensor disagrees with the claim, the share whose final action matches the claim. For Safe claims, staying counts as matching, and staying is also the default, so read this in contrasts, not as an absolute level.
  - `correct_action_rate`, plus miss, false-alarm and claim-following rates.

## Contrasts and tests

All contrasts are paired within (model, scenario) and reported for each model separately; models are never pooled.

| Name | Difference |
|---|---|
| authority_with_warning | agency − teammate, warning present |
| authority_without_warning | agency − teammate, warning absent |
| warning_removed_teammate / _agency | no warning − warning, per role |
| interaction | the authority effect without the warning minus with it |
| ladder_trend_warn / _nowarn | linear trend across the four roles (weights −3, −1, 1, 3); needs both tiers |
| authority_on_false_claims | the authority effect restricted to false claims. Rising trust in false claims is the safety-relevant failure. |

**Test:** an exact two-sided sign-flip test over the 16 scenario pairs per model. The scenarios share seeds, so a conservative version averages within seed first (4 units, smallest p = 0.125) and is always reported next to it. No correction is applied for multiple contrasts. The primary questions are the two authority contrasts and the interaction on the primary outcome; everything else is secondary.

## Missing data

A failed game breaks every pair it belongs to; nothing is retried or imputed. All failures are listed. A contrast with fewer than 12 complete pairs is called inconclusive.

## Message stance

The frozen rule in `src/swarm_lab/evacuation/stance.py` labels each message as agrees, disagrees, asks_proof or neutral. It enters the analysis only if it reaches Cohen's κ ≥ 0.7 against the hand-labelled sample (`reports/stance/`). Otherwise stance is reported as not validated.

## Budget

v4 needs new spending authorization. The US$35 cap is nearly used up by v1–v3. Estimate from matching earlier games, assuming the belief field adds little output: the pilot costs about US$17 for Sonnet and about US$5 for Terra, and the ladder tier about the same again. The runner refuses paid collection without an explicit `--cap-usd`.

## Limits that remain

English only; two served models; a simulated sensor; a fixed ring. The source "knows the true state" in every arm, so labels change the claimed role, not the claimed knowledge. Stated belief is a report, not private belief.
