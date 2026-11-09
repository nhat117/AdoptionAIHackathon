# Frontier model code and API check

One request per model, no retries. Low reasoning requested; 2,048 output-token cap; same local round-three diagnostic structure as the earlier checks. This is not the real experiment.

| Model | Result | Status |
| --- | --- | --- |
| GPT-6.1 Terra | HTTP 404, no response metadata | Adapter temperature mismatch fixed; corrected request not live-verified |
| Claude Sonnet 5.5 | HTTP 404, no response metadata | Adapter temperature mismatch fixed; corrected request not live-verified |
| Qwen3.8 Max Prime | Valid Chinese response and citation, finish=stop | Diagnostic passed; low explicitly requested |
| DeepSeek V4 Pro 0813 | Valid Chinese response and citation, finish=stop | Diagnostic passed; low explicitly requested |

The catalogue lists low for all four models. Terra/Sonnet omit temperature from supported parameters. The previous adapter sent temperature=0 with require_parameters=true, a plausible routing-rejection cause. HTTP error bodies were not retained, so this is not a confirmed explanation of the 404s. The corrected adapter now omits temperature for those two models and logs the requested temperature. Their runner gates remain closed pending a successful corrected live check. Temperature must be described as provider-controlled for these endpoints, not falsely reported as zero.

Qwen/DeepSeek are now allowed with explicit low effort; the older DeepSeek 0423 route remains blocked. Returned providers were Alibaba and Relace respectively. Reported cost for the two completed calls totals $0.0168498501. DeepSeek's usage reports more reasoning than completion tokens; preserve the raw fields and do not interpret them as a consistent exact compute accounting.

Code tests check temperature omission for Terra/Sonnet, retention for Qwen, and low-reasoning payloads. The underlying exact numeric reasoning budget is provider-specific; request acceptance and token accounting do not establish compute equivalence across families.

Remaining before the real batch: corrected Terra/Sonnet diagnostic calls; human translation review; frozen failure policy, output budgets, and roster; final batch allocation and cost limit. One call in one language does not validate every language or a full multi-round game. No 600-game run has launched.
