# When Does Semantic Oversight Add Value?

**Swarm Alignment Hackathon · Track 4: Multi-Agent Oversight and Control**

A reproducible study of incorrect facts passing between AI agents, using English, Vietnamese and Chinese peer messages. A controller checks report facts before authorizing a handoff.

**Start here:** [questions and hypotheses](research/QUESTIONS_AND_HYPOTHESES.md) · [filled Word report](submission/Track4_Submission.docx) · [research proposal](research/RESEARCH_PROPOSAL.md) · [research report / submission draft](research/OVERSIGHT_ABLATION_RESULTS.md) · [submission status](SUBMISSION.md) · [historical evidence](ARCHIVE.md)

## Main finding

The controlled follow-up uses **24 new responses** on two task clusters. All responses are valid JSON. Prompts differ only in the trusted-record field. Both controller arms have the same registry and evaluate the exact same candidate, with no recovery or rewriting.

| Worker receives trusted facts | Structural check: wrong-budget releases | Semantic check: wrong-budget releases | Reports withheld by semantic check |
|---|---:|---:|---:|
| No — 12 candidates | 6 | 0 | 6 |
| Yes — 12 candidates | 0 | 0 | 0 |

All six clean candidates in the evidence-absent condition remain accepted. Six incorrect candidates are blocked, not counted as repaired tasks. With trusted input, both checks accept twelve correct reports: **this pilot shows no additional benefit over grounding in that setting**.

This is selective rejection of specified unsupported values, not a general semantic detector or proof of swarm alignment. Two task clusters and repeated language conditions cannot establish a language effect. Source poisoning is deliberately seeded. Archived replay and fresh inference are separate.

## Reproduce without new inference

Use a full Git clone so prior evidence can be checked against its baseline commit.

```sh
git clone --branch codex/authority-language-v3 https://github.com/nhat117/AdoptionAIHackathon.git
cd AdoptionAIHackathon
uv sync --frozen --extra dev
uv run python scripts/run_oversight_ablation.py
uv run python scripts/report_oversight_ablation.py
uv run pytest -q
```

The first experiment command checks the frozen plan. Adding `--run` collects only missing trials and consumes Adaption usage. It reads `ADAPTION_API_KEY` or securely prompts without saving it. Existing trials are retained. Never put credentials in code or Git.

**Validation:** the 88-test research suite and 14 existing LangGraph tests pass together (102 total); lint passes; 133 prior run files are verified unchanged. Python 3.11+ matches the existing Studio scaffold.

## Inspect the evidence

- [Frozen protocol](runs/oversight-ablation-v1/FROZEN_PROTOCOL.json): inputs, source hashes, settings and stop rule saved before inference.
- [Raw responses](runs/oversight-ablation-v1/trials.jsonl): all 24 requests, provider outputs, usage, independent scores and four gate decisions.
- [Metrics](runs/oversight-ablation-v1/metrics.json): correct releases, wrong releases, blocks, clean rejection and errors.
- [Archived replay](runs/oversight-ablation-v1/archived_first_hop_replay.jsonl): retrospective mechanism check with no model calls.
- [Preservation manifest](runs/oversight-ablation-v1/PRIOR_EVIDENCE_MANIFEST.json): hashes of all prior tracked run files.

## Implementation and scope

The existing architecture stays intact: stateless Adaption calls, controller-owned facts, deterministic checks and bounded trusted-only recovery. [Agent envelopes](src/ai2ai_guard/oversight.py) check routing, sender binding, message kinds and replay. [Context import](src/ai2ai_guard/context.py) keeps supplied history and checker feedback as data. The [production fact gate](src/ai2ai_guard/fact_projection.py) renders verified reports from trusted records.

The [research ablation](src/ai2ai_injection/oversight_eval.py) preserves accepted candidates to isolate semantic rejection. It does not replace production rendering or certify arbitrary prose. Network authentication, durable replay protection, covert-channel detection and tamper-proof logs are outside scope.

An optional synthetic demo is available with `uv run python scripts/protected_fact_report.py --history configs/priming_demo.json --feedback configs/validator_feedback_demo.json`.

Response Attack, Internal Safety Collapse and Thought Virus inform the preserved mechanism tests. Their harmful benchmarks, published success rates and subliminal-bias experiments are not reproduced here. See [ARCHIVE.md](ARCHIVE.md) for the earlier work.

## Existing LangGraph Studio playground

The generic scaffold already on `main` is retained alongside the research modules. See [LANGGRAPH_STUDIO.md](LANGGRAPH_STUDIO.md) for setup and offline fixtures. Its fixture outputs are not research results; the scored experiments above keep their original stateless Adaption path.
