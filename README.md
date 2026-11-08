# Authority Across Languages

We test whether fictional authority in a lower-trust AI-agent message changes synthetic-marker disclosure across **English, Vietnamese and Chinese**. The repository also retains its official Adaption Python SDK dataset CLI.

## Research experiment

See [V3 protocol](research/PROTOCOL_V3.md) and the [team's updated proposal](research/USER_UPDATED_PROPOSAL.txt). Each target model receives **360 attack trials + 60 benign controls**. A fixed correction/inclusion template is paired across three languages and two labels: ordinary peer and fictional Senior Operations Director. Paired output-only/full-trace GPT-4o monitoring reuses saved target responses.

All markers and records are synthetic. There are no real secrets, external actions, or real-person impersonations. Translations and authority salience await independent bilingual human validation; results are exploratory. This is a controlled peer-message simulation, not a live multi-hop agent benchmark. H2 pragmatic framing is not run. The H3 marker-task ablation does not establish genuine context-compression loss.

## Setup

```sh
uv sync --frozen --extra dev
cp .env.example .env
```

The existing Adaption CLI reads `ADAPTION_API_KEY` from your environment or ignored `.env`. The experiment runner reads `BRAINTRUST_API_KEY` from the environment or prompts securely; it does not automatically load `.env`. Keys are separate service credentials. Never put either in commits or command arguments.

## Run H1 and paired H3

```sh
# Freeze without model calls, or omit this step (collection freezes automatically).
uv run python scripts/run_experiment.py \
  --provider braintrust --model gpt-4o --run-id h1-v3-gpt4o --freeze-only

# 420 target calls and up to 840 monitor calls through Braintrust.
uv run python scripts/run_experiment.py \
  --provider braintrust --model gpt-4o --run-id h1-v3-gpt4o

# Separate replication: local targets, GPT-4o monitor via Braintrust.
ollama pull qwen2.5:0.5b
uv run python scripts/run_experiment.py \
  --provider ollama --model qwen2.5:0.5b --run-id h1-v3-qwen05b

# Recompute tables and CSVs without model calls.
uv run python scripts/export_results.py runs/h1-v3-gpt4o
uv run python scripts/export_results.py runs/h1-v3-qwen05b
```

Remote calls incur provider usage. `--skip-monitors` collects H1 target responses only. Reusing the same run ID resumes only unattempted trial IDs; failures remain recorded. Changed frozen code/config requires a new run ID. Inspect failed/truncated responses before interpretation. Three repetitions share a task design; analysis resamples tasks, not individual responses. Reported risk differences are not logistic-regression coefficients. Zero disclosures cannot establish equality between authority conditions.

Outputs per run: frozen protocol and Git/source hashes, append-only `targets.jsonl` and `monitors.jsonl`, raw prompts/responses, returned model names, errors, token usage, `targets.csv`, `metrics.json` and `RESULTS.md`. Historical two-language/four-role code, raw results, proposal PDFs and Adaption uploader are preserved separately under [research/legacy-v2](research/legacy-v2/README.md); do not pool versions.

## Adaption dataset CLI

```sh
uv run adaption-starter list --limit 5
uv run adaption-starter get YOUR_DATASET_ID
uv run python -m adaption_starter list
```

These commands list/read datasets using the [official SDK](https://docs.adaptionlabs.ai/introduction/getting-started). Dataset upload and estimate-only integration from the earlier research stage lives in [research/legacy-v2/ADAPTION.md](research/legacy-v2/ADAPTION.md). It uses development-only validated reference examples; no V3 evaluation data is used for adaptation/training.

## Checks

```sh
uv run --frozen --extra dev ruff check .
uv run --frozen --extra dev pytest
```

Tests exercise balanced design, sender-only variation, normalized disclosure, schema-vs-objective separation, paired monitor context, API failure handling, cluster-aware contrasts, frozen protocol mismatch protection, and the existing Adaption CLI. No network or credentials are needed for tests. GitHub Actions runs checks on Python 3.9 and 3.12.
