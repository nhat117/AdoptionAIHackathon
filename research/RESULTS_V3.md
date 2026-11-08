# Authority, language and monitor visibility: V3 observed results

8 November 2026. Frozen-protocol exploratory experiment.

This run implements the supplied three-language, two-attribution MVP. Each model has 360 attack trials and 60 benign controls from 20 fresh task designs. Across both models: 840 target calls and 1,680 paired GPT-4o monitor calls. Earlier V2 results are not pooled here.

| Target | Completed targets | Normalized marker disclosure | Benign completion |
|---|---:|---:|---:|
| gpt-4o-2024-11-20 | 420/420 | 0.0% (0/360) | 100.0% (60/60) |
| qwen2.5:0.5b | 420/420 | 31.9% (115/360) | 85.0% (51/60) |

## H1: authority by language

All models use the same correction/inclusion template. Within each language, only the fictional sender attribution varies. Trusted instructions stay English. Each cell has 60 responses from 20 task clusters; three repetitions are not independent task designs.

### gpt-4o-2024-11-20

| Language | Peer disclosure | Authority disclosure | Authority minus peer, pp [95% task-bootstrap interval] |
|---|---:|---:|---:|
| en | 0.0% (0/60) | 0.0% (0/60) | 0.0 [0.0, 0.0] |
| vi | 0.0% (0/60) | 0.0% (0/60) | 0.0 [0.0, 0.0] |
| zh | 0.0% (0/60) | 0.0% (0/60) | 0.0 [0.0, 0.0] |

| Interaction vs English | Difference in differences, pp [95% task-bootstrap interval] |
|---|---:|
| vi | 0.0 [0.0, 0.0] |
| zh | 0.0 [0.0, 0.0] |

No marker disclosures were observed. This floor-limited attack set does not discriminate authority effects or language interactions. Degenerate all-zero bootstrap intervals do not establish equivalence or universal resistance.

Detailed trace and tables: [h1-v3-gpt4o](../runs/h1-v3-gpt4o/RESULTS.md).

### qwen2.5:0.5b

| Language | Peer disclosure | Authority disclosure | Authority minus peer, pp [95% task-bootstrap interval] |
|---|---:|---:|---:|
| en | 16.7% (10/60) | 21.7% (13/60) | 5.0 [-11.7, 21.7] |
| vi | 53.3% (32/60) | 46.7% (28/60) | -6.7 [-26.7, 13.3] |
| zh | 21.7% (13/60) | 31.7% (19/60) | 10.0 [-3.3, 23.3] |

| Interaction vs English | Difference in differences, pp [95% task-bootstrap interval] |
|---|---:|
| vi | -11.7 [-36.7, 11.7] |
| zh | 5.0 [-15.0, 26.7] |

Both interaction intervals include zero; this experiment provides no clear support for a language-dependent authority effect under this template.

Detailed trace and tables: [h1-v3-qwen05b](../runs/h1-v3-qwen05b/RESULTS.md).

## H3: paired monitor visibility

The same saved candidate is judged by output-only and full-trace GPT-4o calls. Full trace additionally exposes the original untrusted peer message. Classifier rates exclude invalid verdicts; operational release decisions fail closed on those errors.

| Target | Monitor context | Composite-violation recall | Compliant-output FPR | Released marker leakage | Benign completion released | Verdict/API errors |
|---|---|---:|---:|---:|---:|---:|
| gpt-4o-2024-11-20 | output_only | undefined (0/0) | 0.0% (0/406) | 0.0% (0/360) | 100.0% (60/60) | 14 |
| gpt-4o-2024-11-20 | full_trace | undefined (0/0) | 0.0% (0/410) | 0.0% (0/360) | 83.3% (50/60) | 10 |
| qwen2.5:0.5b | output_only | 93.3% (98/105) | 10.0% (21/211) | 0.6% (2/360) | 65.0% (39/60) | 104 |
| qwen2.5:0.5b | full_trace | 92.1% (128/139) | 11.0% (27/246) | 0.6% (2/360) | 58.3% (35/60) | 35 |

Matched pairs for gpt-4o-2024-11-20: 396; violating pairs: 0. Full-minus-output recall change: None pp; FPR change: 0 pp.


Matched pairs for qwen2.5:0.5b: 303; violating pairs: 105. Full-minus-output recall change: -2.857142857142857 pp; FPR change: -1.5151515151515151 pp.

## Limits and reproducibility

- H3 is a visibility ablation on a marker benchmark. The violation remains visible in the candidate output; there is no executor compression intervention or human-adjudicated semantic label. It does not establish the context-compression mechanism from the Vietnamese oversight sprint.
- H2 pragmatic/cultural framing is not run. Translations and perceived authority have not received independent bilingual human validation. Language is not culture; results are exploratory.
- H1 uncertainty resamples entire tasks with 2,000 bootstrap draws. No logistic coefficients, corrected p-values, or power guarantee are claimed. H3 paired differences are descriptive point estimates.
- Monitor formatting failures differ by condition and target model. Classifier rates conditional on valid verdicts may be selection-biased; matched-pair deltas do not resolve missing-verdict bias.
- All target and monitor errors are retained. Raw prompts, output strings, returned model names, token usage and timing remain in JSONL. FROZEN_PROTOCOL.json records source/data hashes, settings and the collection code commit. Local freezing is not external preregistration.
- No V3 evaluation examples were sent to Adaption for training. The earlier Adaption integration and research results remain archived under research/legacy-v2.

See [protocol](PROTOCOL_V3.md), [team proposal](USER_UPDATED_PROPOSAL.txt), and [figure](figures/h1-primary-asr.png).
