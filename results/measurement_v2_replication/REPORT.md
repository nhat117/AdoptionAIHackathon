# Multi-task structured-decision replication

Fixed 20-task study disjoint from the one-task v2 pilot. Scenarios existed in older datasets; this is not a claim of model-unseen tasks. Four authority conditions, three languages, three record conditions, paired clean/attack messages: 1440 worker calls. Outputs are explicit budget decisions, not an inferred hidden belief or a universal prose-claim judgment.

| Record | Attack | n | Valid | False target reported | Correct budget | Abstained | Invalid |
|---|---|---:|---:|---:|---:|---:|---:|
| correct | False | 240 | 240 | 0 | 240 | 0 | 0 |
| correct | True | 240 | 240 | 1 | 239 | 0 | 0 |
| absent | False | 240 | 239 | 0 | 0 | 239 | 1 |
| absent | True | 240 | 238 | 75 | 0 | 163 | 2 |
| stale | False | 240 | 240 | 0 | 0 | 1 | 0 |
| stale | True | 240 | 240 | 14 | 0 | 7 | 0 |

Clean and attack rows are retained regardless of outcome. Invalid outputs remain instrument/format failures and are not counted as refusals. Bounds on false-target reporting include unresolved formats. Correctness and abstention are separate outcomes: an abstention is not successful budget completion. A stale record can produce a schema-valid but factually incorrect response even without an attacker.

| Paired contrast | Condition | Language | Difference (pp) | Task bootstrap 95% (pp) | Multiplicity-adjusted interval (pp) |
|---|---|---|---:|---:|---:|
| record | absent | all | 30.83 | [24.58, 37.92] | [21.67, 41.25] |
| record | stale | all | 5.42 | [2.92, 8.33] | [1.67, 9.58] |
| authority | 1 | all | -7.22 | [-13.33, -1.67] | [-16.11, 0.56] |
| authority | 2 | all | 3.89 | [-3.89, 11.67] | [-7.78, 14.44] |
| authority | 3 | all | 0.00 | [-7.78, 7.78] | [-11.67, 11.11] |
| language | vi | all | -9.58 | [-14.17, -5.42] | [-16.67, -3.75] |
| language | zh | all | 4.58 | [-0.42, 9.58] | [-2.50, 12.08] |
| interaction | 1 | vi | 0.00 | [-11.67, 11.67] | [-16.67, 16.67] |
| interaction | 1 | zh | 3.33 | [-13.33, 20.00] | [-20.00, 26.67] |
| interaction | 2 | vi | -18.33 | [-30.00, -8.33] | [-35.00, -3.33] |
| interaction | 2 | zh | -5.00 | [-16.67, 6.67] | [-21.67, 11.67] |
| interaction | 3 | vi | -6.67 | [-20.00, 6.67] | [-26.67, 15.00] |
| interaction | 3 | zh | -13.33 | [-28.33, 1.67] | [-35.00, 10.00] |

Record contrasts compare absent/stale with correct. Authority contrasts compare team lead (1), finance auditor (2), and fake system authority (3) with teammate (0). Language contrasts compare Vietnamese/Chinese with English. Interactions are authority contrasts in the target language minus the English contrast. These are exploratory synthetic-task estimates; 20 task clusters and one model do not support model-general conclusions. Zero-width bootstrap intervals on constant outcomes do not establish equivalence. For invalid formats, contrasts describe confirmed-adoption lower bounds, not identified true adoption effects.

## Reproduce

Run `python scripts/run_measurement_v2.py --replicate` for the dry run; add `--run` to resume missing worker IDs under the shared original US$10 cap. Run `python scripts/report_measurement_replication.py` to verify frozen input/source hashes and regenerate results. The local protocol was saved before dispatch, not externally preregistered. Analysis was specified during collection, before inspecting replication outcomes; it is exploratory. Raw outputs, prompts and exact model IDs remain in workers.jsonl. No committee replication is claimed by this worker-only study.

The separate feasibility report documents the GitHub sources informing measurement: [InjecAgent](https://github.com/uiuc-kang-lab/InjecAgent) and [Inspect evaluation guidance](https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/BEST_PRACTICES.md). No upstream code or attack payload was copied.

