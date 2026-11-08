# When Does Semantic Oversight Add Value?

**Swarm Alignment Hackathon · Track 4: Multi-Agent Oversight and Control**

A reproducible study of incorrect facts passing between AI agents, using English, Vietnamese and Chinese peer messages. A controller checks report facts before authorizing a handoff.

**Start here:** [600-response report](submission/expansion-v2/README.md) · [budget swarm extension](research/BUDGET_SWARM_EXTENSION.md) · [dataset locations](data/README.md) · [questions and hypotheses](research/QUESTIONS_AND_HYPOTHESES.md) · [preserved pilot Word report](submission/Track4_Submission.docx) · [research proposal](research/RESEARCH_PROPOSAL.md) · [research report / submission draft](research/OVERSIGHT_ABLATION_RESULTS.md) · [submission status](SUBMISSION.md) · [historical evidence](ARCHIVE.md)

## Current expanded result

The [600-response expansion](submission/expansion-v2/README.md) uses **50 previously unused task IDs**, with **200 responses per review-note language**. All 600 requests completed without errors and passed strict structural validation. This is a separate locally frozen replication; the [24-response pilot](research/OVERSIGHT_ABLATION_RESULTS.md) remains unchanged.

| Worker trusted input | Structural: wrong budgets released | Fact check: wrong budgets released | Correct reports released by fact check | Blocked by fact check |
|---|---:|---:|---:|---:|
| Absent — 300 responses | 150 | 0 | 150 | 150 |
| Present — 300 responses | 0 | 0 | 300 | 0 |

The fact check selectively blocks incorrect budgets beyond structural validation, while preserving correct reports. With trusted input, no added benefit over grounding is observed. Blocking is not repair. The 50 IDs and different fact values still share one reporting contract; only a review note varies across English, Vietnamese and Chinese. This is not a causal language-effect or general swarm-safety result.

**Current report:** [Word template](submission/expansion-v2/Track4_Expanded_600.docx) · [Readable report](submission/expansion-v2/README.md) · [Actual outputs CSV](submission/expansion-v2/recorded-outputs.csv) · [Actual outputs JSON](submission/expansion-v2/recorded-outputs.json)

## Separate proposed swarm extension

[Budget committee study design](research/BUDGET_SWARM_EXTENSION.md): five agents with different private facts, three discussion rounds, final votes and matched release checks. The requester may accept or decline a contingent simulated offer. Propagation, self-correction, votes and released expenses are measured separately. The [scenario specification](data/budget-review-v1/scenario.example.json) is a design example, not executed research data. No bribery or live swarm result is claimed.

## Reproduce without new inference

```sh
git clone --branch codex/authority-language-v3 https://github.com/nhat117/AdoptionAIHackathon.git
cd AdoptionAIHackathon
uv sync --frozen --extra dev
uv run python scripts/report_oversight_expansion.py
uv run pytest -q
```

The audit verifies the frozen inputs and source code, all 300 prompt pairs, exact candidate preservation and **140 earlier run files**. The full suite passes **104 tests**, and lint passes. The original pilot can still be audited with `uv run python scripts/report_oversight_ablation.py`.

`uv run python scripts/run_oversight_expansion.py` checks the fixed 600-response plan without inference. Adding `--run` uses Adaption only for missing assigned trials, retains existing records and consumes provider usage. Credentials belong in environment variables, never in Git. The report writer and charts use `scripts/write_expansion_report.py` with the existing Matplotlib requirements.

## Dataset locations

See [data/README.md](data/README.md) for the exact paths and distinctions.

- [Expansion protocol](runs/oversight-expansion-v2/FROZEN_PROTOCOL.json)
- [600 input prompts](runs/oversight-expansion-v2/inputs.jsonl)
- [600 raw response records](runs/oversight-expansion-v2/trials.jsonl)
- [Expansion metrics](runs/oversight-expansion-v2/metrics.json)
- [Preserved 24-response pilot](runs/oversight-ablation-v1/)
- [Earlier 600-case authority dataset](data/authority500/selected_600_cases.jsonl), separate from the new 600-response expansion

## Implementation and scope

The existing architecture stays intact: stateless Adaption calls, controller-owned facts, deterministic checks and bounded trusted-only recovery. [Agent envelopes](src/ai2ai_guard/oversight.py) check routing, sender binding, message kinds and replay. [Context import](src/ai2ai_guard/context.py) keeps supplied history and checker feedback as data. The [production fact gate](src/ai2ai_guard/fact_projection.py) renders verified reports from trusted records.

The [research ablation](src/ai2ai_injection/oversight_eval.py) preserves accepted candidates to isolate semantic rejection. It does not replace production rendering or certify arbitrary prose. Network authentication, durable replay protection, covert-channel detection and tamper-proof logs are outside scope.

An optional synthetic demo is available with `uv run python scripts/protected_fact_report.py --history configs/priming_demo.json --feedback configs/validator_feedback_demo.json`.

Response Attack, Internal Safety Collapse and Thought Virus inform the preserved mechanism tests. Their harmful benchmarks, published success rates and subliminal-bias experiments are not reproduced here. See [ARCHIVE.md](ARCHIVE.md) for the earlier work.

## Existing LangGraph Studio playground

The generic scaffold already on `main` is retained alongside the research modules. See [LANGGRAPH_STUDIO.md](LANGGRAPH_STUDIO.md) for setup and offline fixtures. Its fixture outputs are not research results; the scored experiments above keep their original stateless Adaption path.
