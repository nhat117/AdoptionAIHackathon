# Record provenance and multilingual budget relay

**Swarm Alignment Hackathon · Track 4: Multi-Agent Oversight and Control**

A reproducible synthetic budget-handoff study. Message wording reverses the observed language pattern. A new neutral fake-record pilot exposes **7 unsupported record attributions** and **2 wrong releases through the source-plus-freshness rule**. Metadata filtering is conditional—not universal prompt-injection prevention.

**One canonical report:** [Read](research/VALIDATED_RESEARCH_REPORT.md) · [PDF](submission/final-review/Authority_Language_Final.pdf) · [Word](research/VALIDATED_RESEARCH_REPORT.docx)

The original replication distinguishes strict primary scoring (90 target reports) from key-case sensitivity (91) and identifies **458/480 stale-record uses**. A separate **4320-response wording-balanced follow-up** tests three variants per role/language; its results and task-cluster analyses remain separate. A new **LLM-based multilingual assessment** uses GPT-6 Astra, never claims human validation, and reports unexecuted/blocked judgments explicitly. Author confirmation remains pending; no security guarantee or official submission is claimed.

## Reproduce the final analysis without model calls

```sh
uv sync --frozen --extra dev --extra reports
uv run python scripts/run_research_pipeline.py
uv run python scripts/export_review_report.py
uv run python scripts/run_research_pipeline.py --check
uv run python scripts/export_review_report.py --check
uv run pytest -q
uv run ruff check .
```

[Machine-readable analysis](results/review_v3/analysis.json) · [Review issue ledger](research/review_resolution/PLAN.md) · [Reproduction details](REPRODUCE_CORRECTED.md) · [Submission status](SUBMISSION.md)

**Round 3:** [Concise eight-section manuscript](research/VALIDATED_RESEARCH_REPORT.md) · [Technical appendix](research/ROUND3_APPENDIX.md) · [R1–R5 remediation](research/review_resolution/ROUND3_REMEDIATION.md) · [180-call neutral evidence](results/round3_neutral/) · [Counts/interactions/denominators](results/round3/analysis.json). All 180 calls returned on the expected model; 179 outputs passed the strict schema and one remains for review. Review-count diagnostics include three contradictory nonnull ABSTAIN outputs and are not silently relabelled successful REPORTs.

**Active translation judge:** GPT-5 through Braintrust Chat Completions, in the separate [`results/llm_judge_gpt5/`](results/llm_judge_gpt5/) profile. Offline preflight: `python scripts/run_gpt5_judge.py`; paid stages require an explicit cumulative `--cap-usd`. The failed Astra profile remains preserved. Judging uses the same model family as workers and is **LLM-based, not human validation**; a smoke test does not validate the full corpus.

**Authorized full run:** the user approved a cumulative **US$650** research cap, recorded separately without changing the original US$20 authorization. `python scripts/run_full_gpt5_judge.py` is a no-call preflight; add `--run --cap-usd 650 --workers 8` for initial judging or `--revisions --cap-usd 650 --workers 8` for flagged-group drafting/reassessment. Both stages share the same remaining budget. Evidence is append-only and sharded; actual completion is reported in the validation artifacts, never inferred from a launched process.

## Automated multilingual QA

[LLM-judge status/report](results/llm_judge/validation_report.md) · [Results](results/llm_judge/validation_results.json) · [Agreement](results/llm_judge/judge_agreement.json)

```sh
uv sync --frozen --extra dev --extra reports --extra judge
uv run python scripts/run_llm_judge.py                 # no API calls
uv run python scripts/run_llm_judge.py --verify-model  # metadata GET, no inference
uv run python scripts/report_llm_judge.py --check     # offline provenance/results check
```

Paid stages require an explicit cumulative `--cap-usd`, a working Responses endpoint and `OPENAI_API_KEY`. No key is stored or hardcoded. Smoke testing verifies actual model/schema before a full batch; no different model is silently used. Published standard Astra rates make 5760 initial judge requests materially more expensive than the earlier GPT-5 research. See the saved estimate before authorizing expenditure. Scores are provisional model opinions; high scores do not erase historical translation/cultural limitations. Suggested revisions stay separate and require a new worker experiment.

The attempted smoke is currently **blocked**: the configured Braintrust proxy returned HTTP 404 for the Responses request; a metadata check against direct OpenAI returned HTTP 401 with the configured credential. **No judge scores were returned.** Set a valid rotated OpenAI key in `OPENAI_API_KEY`, and unset `OPENAI_BASE_URL` or explicitly set it to `https://api.openai.com/v1` for the judge process. Do not paste keys into code or reports. The six validation artifacts clearly mark all unexecuted judgments as pending.

Original data, prompts, configurations and results are preserved. New evidence is under `results/review_v3/`; the old dashboard remains a historical snapshot, not a current-results display. Gemma and GPT-5 studies use different prompts/tasks and are not direct model-performance comparisons.

Portable export verification checks recorded artifact bytes, source/renderer/font/SVG/dependency hashes and exact Word/PDF content against the canonical report. It does not assume identical font rasterization across operating systems. The unfilled [human packet](research/review_resolution/HUMAN_SIGNOFF.md) is retained for optional external validation; it is not presented as completed evidence or the current automated QA workflow.

<details>
<summary>Historical studies and implementation notes (not current main reports)</summary>

[Original audit draft](research/EXPERIMENT_AUDIT_REPORT.md) · [Archived validation report and Word export](research/review_resolution/archive/1dcf401/) · [Historical evidence index](ARCHIVE.md)

## Earlier corrected results — 9 November 2026

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

The corrected verifier checks all saved prompts and response IDs and preserves the historical baseline. GitHub CI checks tests, lint and offline reproduction on Python 3.11 and 3.12. Regenerate the illustrated audit with `uv run python scripts/audit_experiments.py`; use `--check` to reject stale report/figure artifacts. Historical audit scripts check source hashes from their original collection and must run against that historical commit; running them against corrected source will deliberately fail. Use the commands above for the updated results.

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

</details>
