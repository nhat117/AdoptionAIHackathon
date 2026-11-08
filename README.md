# AI-to-AI report protection harness — Adaption SDK

**All new model calls use Adaption**: target generation, paired monitoring and protected-report recovery. The Python gate enforces the reporting policy before anything is released. Historical Braintrust/Ollama runs are retained as separate research evidence.

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
