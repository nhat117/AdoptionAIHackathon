# Corrected Terra/Sonnet checks — 8 November 2026

Both corrected requests passed: valid JSON, allowed action, short requested-language message, and a citation to an actually received message. Each completed with finish_reason=stop. Exactly one new call per model; no full games launched.

| Model | Language | Reasoning requested | Temperature | Output ceiling | Reported cost |
| --- | --- | --- | --- | --- | --- |
| GPT-6.1 Terra | English | low | Omitted; provider-controlled | 2048 | $0.001108 |
| Claude Sonnet 5.5 | Vietnamese | low | Omitted; provider-controlled | 2048 | $0.004064 |

Together with the preceding Qwen Max Prime and DeepSeek Pro 0813 checks, all four frontier models have now passed one API/schema diagnostic. The language runner permits those exact routes with explicit low effort and records temperature as null for Terra/Sonnet rather than incorrectly claiming zero. Temperature remains fixed within each model's language comparisons; sampling controls are not identical across model families.

These checks do not prove full multi-round reliability, translation quality, or equal hidden computation. Human translation review, final batch allocation, failure policy, and cost limits still need to be frozen before a confirmatory evaluation. Prior failed calls remain archived. The main 600-game experiment has not started.
