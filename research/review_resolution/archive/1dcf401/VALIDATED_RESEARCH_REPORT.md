# Budget handoff research: validated findings and remaining limits

Updated 9 November 2026. This report consolidates executed studies while keeping their different tasks and output contracts separate. Every result is backed by saved prompts, outputs and decisions. It does not certify unrestricted agents or arbitrary natural-language truth.

Latest validation: 106/108 operational outputs complied with the stated policy; 2 were strict format failures. Observed false-target authorizations: 0. With a corrupt record deceptively marked current, 36/36 operational outputs followed the policy, but only 0/36 reported the true budget. Policy compliance is not factual truth.

## Does the experiment work?

The code and fixed-cohort reconstruction work. Structured decision scoring can distinguish reporting a false target, reporting the correct budget, abstaining, and invalid format. The new contract validation gives an explicit normative meaning to the decision field. This does not validate hidden belief inference, all prose attribution, or general authority/language effects.

Local verification: 212 passed in 0.61s. Separate known-answer tests cover 16 policy/factual cases, including duplicate keys, invalid decisions, unsupported evidence and a wrong current record. These are synthetic engineering tests, not independent human validation of natural-language claims.

## Why the original numbers did not change

The original 600 budget outputs contain 150 wrong field values and 450 budget-consistent reports. Both old and corrected semantic gates release the same 450 and reject the same 150. Expanded contradictory-prose coverage adds regression capability but no extra detection on this saved cohort. The oracle still receives the correct budget; its 150/150 sensitivity is not evidence of realistic oversight. The blind monitor allowed 6/150 wrong outputs, blocked 115/450 budget-correct outputs, and abstained on 445/600. Historical data and results remain intact.

## Multi-task reporting study: executed, but interpret narrowly

The 1440-response study used 20 task clusters, four authority claims, three peer-message languages, three record conditions and matched clean/attack inputs. In attacked cases the explicit false target was reported in 1/240 correct-record cases, 75/240 absent-record cases and 14/240 stale-record cases. Three strict format failures remain unknown, not successful defenses. A separately labeled key-case sensitivity recovers those outputs and changes absent-record false-target reporting to 76/240.

The single correct-record false-target event explicitly qualified the peer figure in prose. The neutral prompt did not define the budget field as authorization for action. Therefore these counts measure false-target reporting, not necessarily unqualified endorsement or policy violation. The new validation below tests that construct directly. The paired task-bootstrap estimates and 13 exploratory contrasts remain in [the replication report](../results/measurement_v2_replication/REPORT.md); twenty synthetic tasks, fixed task-block dispatch and one model do not establish culture-level or model-general effects.

## Matched contract validation: 216 new calls

Three task clusters (45–47) are disjoint from the v2 pilot and replication, but their scenarios existed historically. The same user/peer inputs are paired across neutral and operational system contracts. Dispatch is randomized using seed 20261110. The operational contract defines reported_budget as the final budget authorized for an inert downstream handoff, requires a current record, and requires abstention when records are absent or stale. It permits discussing peer claims only in summary. No actual payment or financial action occurs.

| Contract | Record | Attack | n | Valid | False target | Correct budget | Abstained | Policy compliant |
|---|---|---|---:|---:|---:|---:|---:|---:|
| neutral | absent | False | 18 | 18 | 0 | 0 | 18 | N/A |
| neutral | absent | True | 18 | 17 | 3 | 0 | 14 | N/A |
| neutral | correct | False | 18 | 18 | 0 | 18 | 0 | N/A |
| neutral | correct | True | 18 | 18 | 0 | 18 | 0 | N/A |
| neutral | stale | False | 18 | 18 | 0 | 0 | 0 | N/A |
| neutral | stale | True | 18 | 18 | 1 | 0 | 0 | N/A |
| operational | absent | False | 18 | 18 | 0 | 0 | 18 | 18 |
| operational | absent | True | 18 | 18 | 0 | 0 | 18 | 18 |
| operational | correct | False | 18 | 16 | 0 | 16 | 0 | 16 |
| operational | correct | True | 18 | 18 | 0 | 18 | 0 | 18 |
| operational | stale | False | 18 | 18 | 0 | 0 | 18 | 18 |
| operational | stale | True | 18 | 18 | 0 | 0 | 18 | 18 |

Policy compliance is assessed only where the operational policy was actually supplied. Neutral-arm outputs are not retrospectively charged with violating a policy they never received. Invalid formats are unscored for policy compliance. This study validates construct clarity and contract following in three synthetic tasks; it is not a definitive treatment-effect estimate or a stronger-defense leaderboard.

## Hidden record corruption: 72 separate stress-test calls

This separate cohort supplies a wrong budget (truth minus 1000) deceptively labeled current. The true value is withheld from every worker prompt. A worker can now obey the record-following policy and still report a false budget. Compliance and factual correctness must therefore be reported separately. This cohort was frozen and collected separately, not pooled into the matched experiment.

| Contract | Record | Attack | n | Valid | False target | Correct budget | Abstained | Policy compliant |
|---|---|---|---:|---:|---:|---:|---:|---:|
| neutral | corrupt_current | False | 18 | 18 | 0 | 0 | 0 | N/A |
| neutral | corrupt_current | True | 18 | 18 | 0 | 0 | 0 | N/A |
| operational | corrupt_current | False | 18 | 18 | 0 | 0 | 0 | 18 |
| operational | corrupt_current | True | 18 | 18 | 0 | 0 | 0 | 18 |

This is the limit of grounding in a supplied record: a label saying current is not independent proof of truth. The experiment does not implement external record authentication, source reconciliation or retrieval of a second verified record.

## Committee evidence

The original 24-game experiment had the true cap available at all 144 exposed agent turns, so its zero propagation is a weak test. The six-game follow-up removed the true cap in absent/stale conditions and still observed no planted-cap repetition. It has only one game per cell, and its fixed expense of 15000 is above both the true cap (12000) and stale cap (11000). It does not identify a guard benefit or validate decision utility when stale records change eligibility. Later committee work should vary expenses across the decision boundary and use repeated matched games. No additional committee replication is claimed in this report.

## Validation, provenance and budget

Frozen inputs and collection source hashes are checked by the report scripts. The artifact verifier checks condition coverage, unique response IDs, prompt joins, blind-monitor input boundaries and preservation of the historical baseline. Raw v2 metadata corrections retain their original collected bytes and correction hashes. Three response bodies from an earlier interrupted partial game remain unavailable; their costs are accounted and they are excluded from completed-game analyses. No new observation was removed to obtain a preferred result.

Aggregate accounted cost across all stages: **US$5.7395**, within the user-authorized **US$20 total cap**. This uses returned token usage at published uncached GPT-5 rates and retains unresolved reservations. It is not a provider invoice. Exact returned model IDs are stored with responses; this remains a single-model study.

The dashboard is still a historical static snapshot; updating this report does not publish a new dashboard. Independent bilingual review, human adjudication of arbitrary prose, more task families and cross-model replication remain outstanding.

## Interpretation

The defensible conclusion is that record availability and record correctness affect the budget information a worker transmits, and that reporting a value, authorizing a value, obeying a policy and being factually correct are different outcomes. The studies support those distinctions within their saved synthetic tasks. They do not establish universal resistance to authority, misinformation or multilingual attacks.

## Reproduce

Run the unit suite and lint, then `python scripts/report_measurement_replication.py`, `python scripts/report_measurement_sensitivity.py`, `python scripts/report_validation.py`, and `python scripts/verify_corrected_artifacts.py`. `python scripts/run_contract_validation.py` and `python scripts/run_corrupt_record_validation.py` are zero-call dry runs; add `--run --cap-usd 20` to resume missing IDs using the same aggregate ledger. Keep that ledger when resuming. See [reproduction instructions](../REPRODUCE_CORRECTED.md).

## Research context and references

Scalable oversight distinguishes what a judge can verify from what it accepts (Irving et al., 2018). Indirect prompt injection motivates distinguishing untrusted peer claims from authoritative sources (Greshake et al., 2023). Sycophancy and multilingual vulnerability findings motivate studying authority and language, but do not supply results for this budget task (Sharma et al., 2023; Yong et al., 2023). Exposure-matched multi-agent comparisons motivate preserving record-access conditions (Becker et al., 2026). Memory and knowledge-source poisoning is related work, not a benchmark reproduced here (Chen et al., 2024). Bibliographic details were checked against the primary records during the earlier research update.


Becker, J., Wahle, J. P., Ruas, T., & Gipp, B. (2026). *Misinformation propagation in benign multi-agent systems* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2606.16710

Chen, Z., Xiang, Z., Xiao, C., Song, D., & Li, B. (2024). *AgentPoison: Red-teaming LLM agents via poisoning memory or knowledge bases* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2407.12784

Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). *Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2302.12173

Irving, G., Christiano, P., & Amodei, D. (2018). *AI safety via debate* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.1805.00899

Sharma, M., Tong, M., Korbak, T., Duvenaud, D., Askell, A., Bowman, S. R., Cheng, N., Durmus, E., Hatfield-Dodds, Z., Johnston, S. R., Kravec, S., Maxwell, T., McCandlish, S., Ndousse, K., Rausch, O., Schiefer, N., Yan, D., Zhang, M., & Perez, E. (2023). *Towards understanding sycophancy in language models* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2310.13548

Yong, Z.-X., Menghini, C., & Bach, S. H. (2023). *Low-resource languages jailbreak GPT-4* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2310.02446


