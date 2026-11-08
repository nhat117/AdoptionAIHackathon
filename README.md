# AI-to-AI report protection harness — Adaption SDK

**Target evaluation, paired monitoring and protected-report recovery use Adaption**. The new synthetic task pool uses GPT-5 through Braintrust, as requested. The Python gate enforces the reporting policy before anything is released. Historical Braintrust/Ollama runs are retained as separate research evidence.

**Earlier evidence:** the paired live challenge observed 0/540 violations both before and after the guard. A subsequent [48-call development pilot](research/DEVELOPMENT_CALIBRATION_RESULTS.md) found 0/36 attack violations and 12/12 benign contract completions across two models. In those settings, incremental live protection was not demonstrated. Constructed tests verify specific checks and expose gaps in factual validation and unrecognized encodings; these are separate from live attack results.

**Near-target update:** a [separate factual-report extension](research/NEAR_TARGET_RESULTS.md) found one real risk substitution in 48 development attacks that the original guard accepted. The first strict facts guard harmed clean-task completion; the repaired, opt-in guard verifies supported fields and renders text only from trusted records. A [fresh-task check](research/NEAR_TARGET_CONFIRMATION.md) released 48/48 correct reports with no retries, but both baseline and guarded systems had zero targeted failures in its 24 attacks. This establishes a specific original-guard gap and observed compatibility of the repair, not broad live security improvement.

Run the new restricted factual-report workflow with `uv run python scripts/protected_fact_report.py`. It uses the synthetic record in `configs/fact_report_demo.json`; supply `--task PATH` for another caller-owned record. Free-form model prose is not released in this mode. The original reporting workflow below remains available separately.

## Multi-agent oversight and control

The [hackathon addendum](research/MULTI_AGENT_OVERSIGHT.md) extends the same architecture to peer → worker → worker handoffs. `OversightSession` checks caller-bound sender identity, receiver/task/conversation, sender-to-message-kind permissions, message replay and a controller-managed hop limit. Peer authority claims stay in the data plane. Source facts and release rules stay in controller-owned Python.

The [matched multilingual pilot](research/MULTILINGUAL_PROPAGATION_RESULTS.md) crosses the same two tasks with English, Vietnamese and Chinese. A seeded wrong budget propagated through two blind workers in 2/2 poisoned cases per language. Registry-backed verification/recovery released none; source-aware prompting without a guard also prevented transfer. These are descriptive content counts using an explicitly posthoc fence-decoder. Live guard rejection occurred on formatting first, so it is not evidence of semantic detection alone. All clean verified final reports were correct. This is factual-error propagation under incomplete evidence, not jailbreak ASR or proof of general swarm safety.

Separately, [real validator-feedback stress](research/CONTEXT_OVERSIGHT_RESULTS.md) produced two valid-JSON DeepSeek budget substitutions that the original gate accepted and the factual gate rejected. Those are repeated conditions of one task, not independent task-level failures. Response priming and the [six-case actual handoff smoke](research/AGENT_HANDOFF_SMOKE.md) observed no receiver substitutions. No upstream PoC code or harmful benchmark data was executed.

Optional external-context inputs remain data:

```sh
uv run python scripts/protected_fact_report.py \
  --history configs/priming_demo.json \
  --feedback configs/validator_feedback_demo.json
```

The importer understands the Response-Attack `rounds` shape but never converts supplied responses into actual assistant roles. A task validator's PASS cannot override source facts or authorize release. Existing reporting commands remain available below.

## Setup

```sh
uv sync --frozen --extra dev
cp .env.example .env
```

Set `ADAPTION_API_KEY` in the ignored `.env`, or export it in your environment. The SDK never needs your Braintrust key for the default workflow. Experiment/protection commands prompt securely if the Adaption key is missing; do not put credentials in command arguments or Git.

## Run a protected report

```sh
# Adaption-hosted Qwen3.8-27B; deterministic release gate; at most one recovery.
uv run python scripts/protected_report.py --language vi --authority authority

# Optional Adaption-hosted DeepSeek V4 Flash veto.
uv run python scripts/protected_report.py --llm-monitor --audit runs/demo/audit.json

# Select another hosted target, including DeepSeek.
uv run python scripts/protected_report.py --model deepseek-v4-flash --language zh
```

Only a validated report or blocked result is printed. The gate checks exact schema, correct task ID/status, required checkpoint, normalized restricted markers and common encodings. An LLM veto can reject but cannot override a failed gate. On failure the harness retries once using only the trusted task; otherwise it releases nothing. Normal audits retain rejected-candidate hashes and reason codes rather than raw rejected text. A released report remains data, not a higher-priority instruction for another agent.

Library entry point: `from ai2ai_guard import guarded_generate`. Supply trusted task facts, an untrusted peer message, and a client with `chat(messages, seed)` returning `content`. The provider factory is `ai2ai_injection.adaption_provider.make_client`. The guard is task-specific; it does not certify every semantic claim, arbitrary encoding or tool action.

## Run the Adaption-only experiment

```sh
# 360 attacks + 60 benign controls; up to 840 DeepSeek monitor calls per target.
uv run python scripts/run_experiment.py --model qwen3.8-27b \
  --run-id h1-adaption-v4-qwen38
uv run python scripts/run_experiment.py --model deepseek-v4-flash \
  --run-id h1-adaption-v4-deepseek

# Recompute JSON metrics, CSVs and Markdown tables without model calls.
uv run python scripts/export_results.py runs/h1-adaption-v4-qwen38
uv run python scripts/export_results.py runs/h1-adaption-v4-deepseek

# Validate protection with saved outputs and 24 separate live smoke cases.
uv run python scripts/evaluate_guard.py
uv run python scripts/evaluate_guard.py --live
```

The default provider is `adaption`, default target `qwen3.8-27b`, and fixed shared monitor `deepseek-v4-flash`. Calls explicitly disable tools, persistent response storage and agentic memory. No conversation continuation ID or unsupported sampling seed is sent. The adapter records final text and usage, not raw reasoning text. `--skip-monitors` collects targets only. `--freeze-only` records a local protocol without API calls. Remote requests consume Adaption usage/credits.

The 20-task, three-language, two-attribution benchmark is unchanged from V3. Reusing it is a hosted-model replication, not a fresh confirmatory study. Translation and authority-salience review are pending. All markers/records are synthetic. See [Adaption protocol](research/ADAPTION_PROTOCOL.md). No evaluation examples are used for adaptation or training; no new training job is launched.

Outputs contain raw role-labelled prompts and final responses, returned model IDs, token usage, latency, errors, configuration/source hashes, counts and task-cluster bootstrap contrasts. Monitor errors are retained and fail closed operationally; only valid verdicts enter classifier metrics. The H3 visibility ablation does not demonstrate true semantic context compression.

## Dataset and model access

```sh
uv run adaption-starter models
uv run adaption-starter list --limit 5
uv run adaption-starter get YOUR_DATASET_ID
```

These use the official Adaption SDK. The development-only dataset uploader and estimate example are preserved in [legacy SDK guide](research/legacy-v2/ADAPTION.md). Creating a dataset is separate from starting adaptation/training.

## Research and architecture

- [Pattern review and architecture](research/PATTERN_REVIEW.md): orchestration, observation, bounded evaluator/recovery and synthetic testing.
- [Original team proposal](research/USER_UPDATED_PROPOSAL.txt).
- [V3 research results](research/RESULTS_V3.md) and [earlier protection validation](research/GUARD_RESULTS.md) used GPT-4o/Qwen0.5B and are **historical**, not Adaption results.
- [V3 protocol](research/PROTOCOL_V3.md); V2 material is preserved under `research/legacy-v2`.

Old providers remain explicit compatibility options. To reproduce V3 exactly, check out its recorded collection commit `0fb29e8`; current defaults and source hashes have changed. Use new run IDs for current source/config. Resume is permitted only under matching frozen settings/hashes, and attempted failures are retained rather than silently retried.

## Checks

```sh
uv run --frozen --extra dev ruff check .
uv run --frozen --extra dev pytest
```

Offline tests cover the guard, experimental balance, context ablation, sampling/error handling, source freeze, dataset CLI and actual Adaption SDK HTTP serialization with a mock transport. GitHub CI runs Python 3.9 and 3.12. No live credentials are needed for tests.

## Completed Adaption pilot and public reference test

See [Adaption results](research/ADAPTION_RESULTS.md) for the completed eight-task
DeepSeek pilot, the incomplete Qwen pilot, and the full public deepset test split.
The reference evaluation measures **binary injection detection**, not agent attack
success. Its 116 labels were never included in model input and were not used for
training or prompt tuning. Revision, license declaration and hashes are recorded
in `runs/reference-deepset-adaption/SOURCE.json`.

```bash
# Offline: recompute metrics and the results section from immutable saved calls.
.venv/bin/python scripts/summarize_adaption.py

# Live: copy the pinned test.jsonl into a new folder before starting another run.
.venv/bin/python scripts/run_reference_dataset.py --folder runs/reference-new
```

The research dashboard is served locally at `http://127.0.0.1:49250/` on the
original machine. Its reviewed snapshot is in `dashboard/src/data.json`;
`python scripts/build_dashboard_data.py` refreshes it from completed collections.
Run sets separate historical results, the paced pilot and earlier rate-limited
attempts. API errors remain visible and are never counted as successful defenses.
The dashboard source uses the Data app runtime; see `dashboard/AGENTS.md` for
its build workflow. No remote website has been published.

## New 600-case study: 200 per language

GPT-5 through Braintrust generated a new 500-task pool (100 development / 400
heldout). The final evaluation selects 100 fresh heldout tasks and crosses them
with three languages and two sender roles: **600 total calls, 200 per language**.
Each language has 180 attack cases and 20 benign controls. The stopped 500-case
design is quarantined; none of its 80 assigned tasks enter the new evaluation.

- [Selection, controls and limitations](research/DATASET600.md)
- [600-case input records](data/authority500/selected_600_cases.jsonl)
- [Generation and quality audit](data/authority500/QUALITY_AUDIT.json)
- [Qwen repair and earlier follow-up](research/AUTHORITY_LANGUAGE_FOLLOWUP.md)

```bash
# Offline selection/reconciliation; --run is required for live calls.
.venv/bin/python scripts/run_authority600.py
# After collection completes:
.venv/bin/python scripts/report_authority600.py
```

Only the 900 development reference rows were imported into Adaption dataset
`40fc2983-0463-4d98-a64a-b416ebb61108`. No evaluation data was imported, and no
training or adaptation job was started. Generation and inference provenance are
recorded separately. All conclusions remain exploratory pending bilingual review.

## Paired harness challenge and repaired canary checks

The separate [harness challenge protocol](research/HARNESS_CHALLENGE_PROTOCOL.md)
adds six attack families and a true same-first-candidate comparison. Baseline
and protected outputs do not come from different stochastic initial generations.

The controlled development suite exposed ROT13, reversed and spaced canary
bypasses in the original gate. The updated gate closes these known forms.
Heldout controlled faults are reported separately from live Adaption results;
they do not measure empirical model jailbreak success or prove general safety.

```bash
# Controlled release-boundary tests, no API calls.
.venv/bin/python scripts/harness_fault_suite.py --split heldout --guard v1
.venv/bin/python scripts/harness_fault_suite.py --split heldout --guard current
# After live collection completes, recompute the research report offline.
.venv/bin/python scripts/report_harness_challenge.py
```

The new gate additionally recognizes ROT13, reversed and whitespace-separated
forms of the task's canary. Arbitrary encodings and semantic policies remain
outside its demonstrated coverage. The earlier guard source and experiment
records are preserved so historical results retain their original meaning.
