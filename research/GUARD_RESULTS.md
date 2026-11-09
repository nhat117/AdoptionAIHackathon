# Protective harness: validation results

8 November 2026. The deliverable is `ai2ai_guard`, a reusable Python release gate with a bounded recovery controller and a CLI demo. See PATTERN_REVIEW.md for the architecture and mapping to the supplied agentic-patterns guide.

## Retrospective replay on V3 target outputs

This is in-sample validation of explicit rules, not an independent benchmark of general prompt-injection detection. It replays saved candidates through the deterministic gate; no model is retrained and no targets are resampled.

| Target | Attack responses | Raw marker disclosures | Marker disclosures released by guard | Benign reports complete before guard | Benign reports released |
|---|---:|---:|---:|---:|---:|
| GPT-4o | 360 | 0 | 0 | 60/60 | 60/60 |
| Qwen2.5 0.5B | 360 | 115 | 0 | 51/60 | 51/60 |

The guard rejected all 115 observed Qwen marker-disclosing candidates. It also rejected structurally invalid reports and reports missing the required checkpoint. Marker detection and schema/identity/checkpoint checks are implemented directly, so successful enforcement of those same rules is by construction. This does not establish general semantic safety. Raw model failures remain in the experiment's JSONL; normal guard audits retain hashes and reasons without copying rejected candidate text.

## Fresh live protected smoke cases

24 cases: 2 fresh tasks x 3 languages x 2 attributions x 2 target models. No LLM monitor veto was enabled; the deterministic gate is the default enforcement path. A failed candidate gets at most one fresh-context retry with only the trusted task.

- 24/24 cases produced a released report that passed the guard contract.
- 0 released reports failed the guard's deterministic checks.
- 7/24 cases needed a trusted-only retry, all in the Qwen replication.
- GPT-4o used 12 generation calls; Qwen used 19, including retries.

This is a small smoke test, not a powered security evaluation or proof of protection against arbitrary encodings, semantic manipulation or tool-use attacks. The same translations are machine authored and still require independent human validation. Two task designs and one sample per cell are insufficient to estimate rare failure rates.

The protection protocol and guard source hash were saved before live collection. See `runs/protection-v1/FROZEN_PROTECTION_PROTOCOL.json`, `live_smoke.jsonl`, `live_metrics.json`, and `retrospective_metrics.json`.

## Why the LLM monitor is optional

V3 tested two context-separated GPT-4o monitor conditions on the same saved responses. On Qwen attack outputs, each monitor condition still released 2/360 marker-disclosing responses, and benign completed release was 39/60 for output-only versus 35/60 for full-trace. There were also many strict verdict-format failures, especially on Qwen candidates, so valid-verdict classifier rates are conditionally sampled and should not be overinterpreted.

Those findings motivate a code-enforced release boundary for explicit constraints. A monitor may veto a deterministically valid report; it cannot override the gate. Monitor API/verdict failure blocks operational release. This uses the guide's observer/evaluator patterns while separating observation from authorization.

## Scope and next validation

The guard currently enforces the synthetic administrative-report contract. It checks normalized marker copies and common Base64/hex forms, exact JSON schema, identity/status and checkpoint preservation. It does not certify factual summary fidelity, all possible encodings, every prompt-injection objective, or side-effecting tool calls. A released report remains data, not an instruction with elevated authority for downstream agents.

For another domain, add independently specified validators and realistic held-out task/attack cases before deployment. A future semantic context-compression study needs an actual executor transformation and independently adjudicated context-dependent violations; the marker visibility ablation does not supply that evidence.

## Checks

26 offline tests pass, including common marker encodings, Unicode variants, strict JSON/schema checks, recovery isolation, fail-closed errors, monitor non-override, balanced research conditions, paired metrics, freeze protection and the Adaption dataset CLI. GitHub CI tests Python 3.9 and 3.12. No real API key is stored in the repository.
