# Adaption-only replication and protection workflow

8 November 2026. All new target generation, monitoring and protected-report model calls use the official Adaption SDK and hosted Responses API. Dataset operations use the existing official Adaption SDK integration. The gate itself remains deterministic application code.

## Hosted models verified with the supplied key

Available IDs: glm-53-flash, glm-5.2, qwen3.5-397b, gemma-4-26b-a4b-it, qwen3.8-27b, deepseek-v4-flash, gemma-4-31b-it. Minimal live requests succeeded for Qwen3.8-27B, DeepSeek V4 Flash and Gemma 4 31B. These checks establish access, not benchmark performance. The selected replication targets are qwen3.8-27b and deepseek-v4-flash; the fixed shared monitor is deepseek-v4-flash. No account-specific stack, dataset search, training job or connected external tool is enabled.

## Frozen design

Config: configs/experiment_adaption.json. Reuse the V3 benchmark's 20 tasks, three languages (English/Vietnamese/Chinese), peer/director attributions, same correction request and three attack repetitions: 360 attacks plus 60 benign controls per model. This is a hosted-model replication on a previously inspected benchmark, not a fresh confirmatory task set or an independent translation review. No evaluation data is used for model training or data adaptation.

Target temperature 0.7; monitor temperature 0; max_output_tokens 1024 for all Adaption calls. The token cap differs from V3's 512, and models/backend also differ, so absolute rates do not isolate a provider or model change relative to V3. Within this replication the same settings and template apply to both targets. Sampling seeds are recorded for shuffle/task reproducibility but are not sent to Adaption because its SDK exposes no inference-seed parameter. Caching/underlying sampling are provider-controlled; deterministic replay is not claimed.

SDK 0.19.0 is installed and tested. Every request sends the original role-labelled message array, store=False, agentic_memory=False and tools=[]. No previous_response_id is supplied. Unexpected action/tool output is rejected. Only final output_text, returned model ID, response ID, status, token usage, output-type labels and latency are recorded; raw reasoning text is not saved. SDK automatic retries are disabled for sampled calls so unsuccessful requests are explicit attempted-trial errors rather than invisible retries. Nonempty incomplete outputs are scored as observed; absent text is a failed response, never a defended attack.

H3 reuses each saved target response for output_only and full_trace monitor calls. Only the original peer message's availability differs. Both monitor conditions use the same Adaption-hosted DeepSeek model and deterministic strict verdict parser. Malformed responses operationally fail closed and are counted/excluded from classifier metrics. With a DeepSeek target, monitor independence is context separation, not different weights.

All output counts, task-cluster risk differences, language interactions and monitor utility/security rates are exported separately from V3. Local freeze records exact source/data/config hashes and commit before dispatch. Old V3 source is available at its recorded commit; archived raw results are not overwritten.

## Protection workflow

The default protected_report CLI now uses Adaption-hosted Qwen3.8-27B, with an optional Adaption-hosted DeepSeek veto. The same deterministic ReportGuard remains the release authority. An invalid candidate can be retried once with the original untrusted peer message removed. Invalid monitor outputs fail closed. No inference provider or LLM verdict can override the deterministic policy.

Adaption-only retrospective replay is separate from a fresh 24-case protected smoke test across the two selected hosted models, two new task topics, three languages and two sender labels. Smoke calls use no LLM veto by default. This tests provider wiring and bounded recovery; it is not a general security guarantee. Retrospective replay checks the same explicit marker/schema policy as ground truth and is therefore enforcement by construction.

## Scope limits

Independent bilingual translation and perceived-authority validation are still pending. H2 pragmatic/cultural framing remains unrun. The H3 marker task cannot establish true semantic context compression because the restricted marker remains observable in candidate output. Tool execution and arbitrary semantic policies are outside this guard's validated reporting contract.

## Official sources checked

- Quickstart and SDK minimum: https://docs.adaptionlabs.ai/inference-stacks/quickstart/
- Available hosted models: https://docs.adaptionlabs.ai/inference-stacks/models/
- Stateless calls, conversation history, tool/memory overrides: https://docs.adaptionlabs.ai/inference-stacks/generate-a-model-response/
- Dataset upload: https://docs.adaptionlabs.ai/adaptive-data/create-a-dataset/
