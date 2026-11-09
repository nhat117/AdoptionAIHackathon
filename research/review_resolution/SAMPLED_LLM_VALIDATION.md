# Sampled LLM-based multilingual validation

The user replaced the full-corpus request with random sampling. The new profile
is `braintrust-gpt5-stratified-sample-v1`, separate from all previous attempts.

## Prospective design

- Frame: 1920 actual aligned EN/VI/Chinese prompt groups, without worker outcomes.
- Strata: cohort × authority role × wording variant × record condition × clean/attack.
- There are 96 strata, each containing 20 task groups. Draw one group uniformly
  from each stratum: **96 groups, a 5% equal-inclusion-probability sample**.
- Primary cohort: 24 sampled groups of 480. Wording follow-up: 72 of 1440.
- Each selected group receives three separately requested assessments with
  balanced randomized language ordering: **288 initial judgments**.
- Selection uses sorted IDs and a recorded seeded RNG; prior judge ratings and
  worker outcomes are not selection inputs. The manifest and frame/source hashes
  are frozen before inference. Difficult or invalid sampled cases are not replaced.
- Unselected groups (1824) are NOT SAMPLED, not passed/failed/pending sample cases.

## Instrument and execution

GPT-5 via Braintrust Chat Completions, expected returned snapshot
`gpt-5-2025-08-07`, high reasoning effort, 16384 maximum completion/reasoning
tokens, strict structured output using the previously working base rubric schema,
exact source-excerpt checks and explicit complete-field copying instructions.
Eight concurrent remote requests; append-only raw evidence shards, token costs,
bounded transport retries and safe recovery of saved complete replies.

The 8192-token full attempt is preserved with 23 valid judgments, two failed exact
quote checks and one reasoning-only truncated raw response. A separate v2 smoke
using a large excerpt-enum schema returned HTTP400; the exact provider reason was
not retained by that earlier transport. Neither attempt is silently repaired,
pooled into this sample or called completed validation. The new transport retains
redacted provider error codes/parameters/messages for diagnosis if another request
is rejected. Its own three-request smoke gate must pass before sample dispatch.

## Budget

Initial sample judging is expected to cost roughly US$25–30, not a guarantee or
invoice. A **US$60 cumulative sampled-project allocation** includes smoke calls,
retries and flagged-group drafting/blinded reassessment. It is an operator
allocation within the user's recorded **US$650 cumulative research approval**,
not US$60 extra permission to exceed that approval. All previous costs and
unresolved failed-call reservations still count against the aggregate cap.

## Interpretation

This is **sampled LLM-based validation, not full-corpus or human validation**.
The same model family serves as worker and judge; repeats may share biases.
Report sample counts, exact evidence, disagreements and instrument failures
descriptively. One sampled group per stratum does not permit direct within-stratum
design-variance estimation; do not claim a precise population-quality/safety rate.
Flagged revisions stay versioned suggestions and receive three blinded new
assessments without changing historical prompts or attack outcomes.

Author confirmation, final proofreading after author edits, independent human
linguistic review and official submission/receipt remain separate and unconfirmed.

## Commands

```sh
python scripts/run_sampled_judge.py
python scripts/run_sampled_judge.py --workflow --cap-usd 60
python scripts/report_llm_judge.py --profile gpt5-sample --check
```

The first command is an offline preflight. The workflow smoke-tests, collects
the remaining sample, drafts/reassesses flagged groups within the same caps, then
regenerates truthful reports and PDF/Word exports after all collectors stop.
