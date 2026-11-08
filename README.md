# When Does Semantic Oversight Add Value?

**Swarm Alignment Hackathon · Track 4: Multi-Agent Oversight and Control**

A reproducible study of incorrect facts passing between AI agents, using English, Vietnamese and Chinese peer messages. A controller checks report facts before authorizing a handoff.

**Latest consolidated report:** [Read the report](research/VALIDATED_RESEARCH_REPORT.md) · [Download the Word report](research/VALIDATED_RESEARCH_REPORT.docx). The new matched validation completed 216 calls plus a separate 72-call corrupt-record stress test. Operational policy compliance was 106/108, with two strict format failures; following a corrupt record produced policy-compliant but factually wrong outputs in 36/36 operational cases. The tested code and scoring work within this scope; this is not a general safety guarantee.

**Latest multi-task replication:** [1,440-response report](results/measurement_v2_replication/REPORT.md) · [Scoring sensitivity and interpretation](results/measurement_v2_replication/SENSITIVITY.md) · [Design boundaries](results/measurement_v2_replication/README.md)

The replication completed all 1,440 requests across 20 task clusters. In attacked conditions, the false target was reported in **1/240 with a correct record**, **75/240 without a record**, and **14/240 with a stale record**. Three outputs failed the strict format contract; they remain separate from refusals. Normalizing JSON key casing as a secondary check changes the absent-record count to 76/240. These are explicit false-target reporting events, not proof of hidden belief or executed unsafe actions. The one correct-record event explicitly attributed the false figure to the peer in its prose.

**Improved measurement pilot:** [Structured scoring, matched controls, and record-access results](results/measurement_v2/REPORT.md). This prospective pilot is separate from the previous 600-output studies.

**Latest results:** [Corrected GPT-5 report](research/CORRECTED_BUDGET_RESULTS.md) · [Why some numbers stayed unchanged](results/RESULTS_DIAGNOSIS.md) · [Reproduction commands](REPRODUCE_CORRECTED.md)

**Historical study:** [600-response report](submission/expansion-v2/README.md) · [budget swarm extension](research/BUDGET_SWARM_EXTENSION.md) · [dataset locations](data/README.md) · [questions and hypotheses](research/QUESTIONS_AND_HYPOTHESES.md) · [preserved pilot Word report](submission/Track4_Submission.docx) · [research proposal](research/RESEARCH_PROPOSAL.md) · [research report / submission draft](research/OVERSIGHT_ABLATION_RESULTS.md) · [submission status](SUBMISSION.md) · [historical evidence](ARCHIVE.md)

## Latest corrected results — 9 November 2026

The corrected study saved 600 new GPT-5 worker outputs, 1,200 blind-monitor evaluations, 24 committee games (504 calls), and a separate 24-call pilot. These are distinct from the historical 600 outputs below.

| Evaluation | Observed result | Interpretation |
|---|---|---|
| Corrected replay of historical outputs | 150 blocked, 450 allowed; unchanged | Oracle still has the correct budget; saved outputs do not exercise the added prose-conflict cases |
| Blind monitor on historical outputs | 6/150 wrong reports allowed; 115/450 correct reports blocked; 445/600 abstentions | Blind monitoring does not reproduce oracle oversight |
| New worker scoring | 0 confirmed adoptions; 591/600 require review | Conservative parser labels do not establish zero true adoption or a model error rate |
| Committee | 0/24 final decisions contained the planted cap | All 144 exposed turns also had the correct authenticated cap; weak evidence for harder propagation settings |

The existing dashboard is a historical static snapshot and has **not** been connected to `results/`; it does not display this corrected study. See the [diagnosis](results/RESULTS_DIAGNOSIS.md) for presentation and methodology limitations.

## Historical expanded result

The [600-response expansion](submission/expansion-v2/README.md) uses **50 previously unused task IDs**, with **200 responses per review-note language**. All 600 requests completed without errors and passed strict structural validation. This is a separate locally frozen replication; the [24-response pilot](research/OVERSIGHT_ABLATION_RESULTS.md) remains unchanged.

| Worker trusted input | Structural: wrong budgets released | Fact check: wrong budgets released | Correct reports released by fact check | Blocked by fact check |
|---|---:|---:|---:|---:|
| Absent — 300 responses | 150 | 0 | 150 | 150 |
| Present — 300 responses | 0 | 0 | 300 | 0 |

The fact check selectively blocks incorrect budgets beyond structural validation, while preserving correct reports. With trusted input, no added benefit over grounding is observed. Blocking is not repair. The 50 IDs and different fact values still share one reporting contract; only a review note varies across English, Vietnamese and Chinese. This is not a causal language-effect or general swarm-safety result.

**Historical expansion report:** [Word template](submission/expansion-v2/Track4_Expanded_600.docx) · [Readable report](submission/expansion-v2/README.md) · [Actual outputs CSV](submission/expansion-v2/recorded-outputs.csv) · [Actual outputs JSON](submission/expansion-v2/recorded-outputs.json)

## Budget swarm calibration and next study

[Budget committee study design](research/BUDGET_SWARM_EXTENSION.md): five agents with different private facts, three discussion rounds, final votes and matched release checks. The requester may accept or decline a contingent simulated offer. Propagation, self-correction, votes and released expenses are measured separately. The [scenario specification](data/budget-review-v1/scenario.example.json) remains a design example. A separate [live English calibration](submission/budget-swarm-calibration-v2/README.md) records 145 actual responses: six of eight episodes completed and two retained protocol failures. All six completed committee decisions were correct; no false-cap propagation or added controller benefit was observed. Two of four offered choices were accepted at the offer stage, including one episode that later failed. This is not evidence of successful bribery or broad swarm robustness. The [first format-failed attempt](submission/budget-swarm-calibration-v1/README.md) is preserved.

## Reproduce without new inference

```sh
git clone --branch codex/authority-language-v3 https://github.com/nhat117/AdoptionAIHackathon.git
cd AdoptionAIHackathon
uv sync --frozen --extra dev
uv run python scripts/replay_corrected_budgets.py
uv run python scripts/report_corrected_budgets.py
uv run python scripts/verify_corrected_artifacts.py
uv run pytest -q
```

The corrected verifier checks all saved prompts and response IDs and preserves the historical baseline. The suite passes **212 tests**, with lint and GitHub CI passing on Python 3.11 and 3.12. Historical audit scripts check source hashes from their original collection and must run against that historical commit; running them against corrected source will deliberately fail. Use the commands above for the updated results.

`uv run python scripts/resume_oversight_expansion.py` checks the saved 600-response inputs without reselecting tasks as new run folders are added. Adding `--run` uses Adaption only for missing assigned trials and retains existing records. The original frozen collector is preserved as historical source. Credentials belong in environment variables, never in Git. The report writer and charts use `scripts/write_expansion_report.py` with the existing Matplotlib requirements.

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

## Corrected budget oversight (9 November 2026)

The corrected budget checker, 600-response replay, GPT-5 experiments and current limitations are documented in [the generated results report](research/CORRECTED_BUDGET_RESULTS.md). See [reproduction commands](REPRODUCE_CORRECTED.md). New outputs are separate under `results/`; historical `runs/` remain unchanged.
