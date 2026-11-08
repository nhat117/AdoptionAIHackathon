# Technical implementation verification — 8 November 2026

**Goal achieved:** complete a small set of multi-round games with valid outputs, local next-round delivery, frozen inference settings, and auditable scores before expanding Experiment 1.

Four of four games completed. No retries, invalid citations, API failures, or trace-audit errors occurred. There were **144 calls** at a reported cost of **$0.24385475**. All returned upstream providers were OpenAI.

## Fixed settings and scope

- GPT-6.1 Terra through OpenRouter, explicit low reasoning, 2,048 output-token cap. Temperature omitted because the endpoint does not expose it.
- English and Vietnamese, one scenario seed, one run per condition.
- Ten-agent ring with four neighbours each; nine responding agents and one controlled source. Source says Danger in rounds one and two, then stops.
- Two matched states: disaster with a true warning; no disaster with a false warning. The source's outward claim is the same in both cases. This narrow check does not include Safe claims.
- Three-dollar reported-spend scheduling stop, maximum 180 calls, two concurrent games. The spend check is between games, not a hard per-call monetary limit. Actual usage was well below it.
- Draft translations remain unreviewed by a human bilingual reviewer. Legacy scenario IDs and split retain the word `calibration`; the purpose is technical implementation verification.

## Observed actions

| State and claim | English | Vietnamese |
| --- | --- | --- |
| Safe, false Danger warning | 9/9 evacuated unnecessarily | 9/9 evacuated unnecessarily |
| Disaster, true Danger warning | 9/9 evacuated correctly | 9/9 evacuated correctly |

The same final actions occurred in both languages; timing and wording differed. There is no basis for a language ranking from one run per condition. Because both states present the same Danger claim without an independent verified observation for recipients, the task gives them no guaranteed way to distinguish truth from falsehood. These results demonstrate execution and warning-following behavior, not truth detection or a safety improvement.

## Trace checks

The analysis rechecks allowed output fields and cited received-message IDs, absence of same-round/future or nonlocal messages, full delivery of the previous round's available neighbour messages, no calls after evacuation, source silence after round two, and consistent low-reasoning/temperature requests. All completed traces pass. Provider metadata shows OpenAI throughout. Output language was inspected in examples, not comprehensively human-annotated.

## Fixes discovered during code review

Applied after the live batch; historical artifacts were not rewritten:

1. The old 16KB prompt guard could reject legal multilingual histories: a synthetic legal-history test measured roughly 35–36KB for Chinese/Vietnamese versus 15KB for ASCII English. The language runner now uses a 64KB guard, with boundary tests. This did not cause a failure in these four games.
2. Save the running manifest before any API calls and update progress after each game.
3. Record the run's actual language in nested scenario metadata as well as the top-level field. Historical Vietnamese outputs still retain base scenario.language=en; their top-level language remains authoritative.
4. Record purpose explicitly as technical implementation verification. Keep historical data split identifiers for compatibility.

All **71 tests pass**, including offline paired-language runs and multilingual prompt-boundary tests. The fixes were verified offline; no paid rerun was needed because the live games had no technical failure. New experiments must preserve the fixed settings and separate infrastructure failures from model outputs. Do not tune prompts to make agents take a preferred action.

## Artifacts

[Summary](summary.json), [outcomes](outcomes.jsonl), [plan](plan.json), [manifests](manifests.json), [trace-audit script](analyze.py), [batch runner](run.py). Raw calls and traces remain under `runs/implementation-verification-20261108/`. The batch used executable code at revision `0e1b0e2`; formatting of the archived launcher changed afterward without changing its requests. Subsequent source fixes are tested separately.

Next step is another bounded block, expanding one dimension at a time. This report does not authorize or claim completion of the proposed 600-game experiment.
