# One-call model compatibility checks — 8 November 2026

Exactly one inference request was sent per routable planned model, with no retries. Each request used the Experiment 1 language instructions, a local round-three history containing one received warning, temperature 0, and a 512-token output cap. These are schema/API probes, not experimental outcomes or full multilingual validation.

| Model | Language | Result | Readiness |
| --- | --- | --- | --- |
| GPT-4.1 mini | English | Valid JSON, action, and received-message citation | One-call check passed; reasoning N/A |
| Claude Haiku 4.5 | Vietnamese | Valid response; low requested, zero reasoning tokens reported | Low reasoning enforcement unverified; remains blocked |
| Qwen3.8 27B | Chinese | Did not finish normally; 512 completion tokens reported | Low supported, but this cap did not yield a usable response; needs a new bounded budget check |
| DeepSeek V4 Flash | Chinese | Did not finish normally; 512 completion tokens reported | Catalogue excludes low; remains blocked even though request was accepted |
| Mistral Small 3.2 | French | Valid JSON, action, and received-message citation | One-call check passed; reasoning N/A |
| Apertus 70B | German | No request sent: no endpoint found in current OpenRouter catalogue | Endpoint pending; checkpoint ID is not an API route |

Qwen's provider reported 533 reasoning tokens against 512 completion tokens, an inconsistent usage breakdown. Do not infer exact internal compute from these numbers. The original adapter did not log finish_reason, so budget exhaustion is suggested by the reported token totals but not independently established by a retained finish code. Future calls now record it. A returned response does not prove a low setting was enforced: Claude and DeepSeek are not cleared by mere request acceptance.

## Fixes made after the checks

- Removed DeepSeek from the verified-low allowlist after checking the current catalogue.
- Added Mistral as a verified non-reasoning route.
- Added `--max-output-tokens` (128–4096; default 512), recorded in the manifest and used in requests. Hold it fixed within each language contrast. Reasoning stays low; increasing this total output ceiling is not increasing reasoning effort.
- Record requested reasoning effort and finish reason alongside provider usage for future diagnostics.
- Retain strict invalid-citation handling. Do not repair or silently retry failed experimental outputs.

The main experiment has not started. A second request would be needed to verify a revised Qwen output cap; none was sent because the user requested one call per model. Claude reasoning control, DeepSeek's lack of low, Apertus access, and human translation review remain explicit limitations.

Raw diagnostic records and the catalogue snapshot are in this directory. No credentials are stored. The generation requests used the existing adapter before the diagnostic improvements, so they do not include newly added metadata fields.
