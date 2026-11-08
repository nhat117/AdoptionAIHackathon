# Adaption AI Hackathon starter

A Python 3.9+ starter using the [official Adaption Python SDK](https://docs.adaptionlabs.ai/api/python). Includes a read-only dataset CLI, local environment configuration, offline tests, and GitHub Actions CI.

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```sh
uv sync --frozen --extra dev
cp .env.example .env
```

Set `ADAPTION_API_KEY` in `.env` using your Adaption account's API key. Keep the key private; `.env` is ignored by Git. You can instead export the variable in your shell; exported values take precedence.

## Run

```sh
uv run adaption-starter --help
uv run adaption-starter list --limit 5
uv run adaption-starter get YOUR_DATASET_ID
# Equivalent module entry point:
uv run python -m adaption_starter list
```

Commands print JSON to stdout. `list` defaults to at most 20 results and follows SDK pagination only as needed. `get` needs a dataset ID accessible to your account. Errors go to stderr with a nonzero exit code. Requests use a 30-second timeout and up to two SDK retries; total elapsed time can be longer.

These commands read existing datasets; they do not create data or launch training. A real API key and network access are required to run them. Never paste keys into commits, PRs, or logs.

## Development

```sh
uv run --frozen --extra dev ruff check .
uv run --frozen --extra dev pytest
```

Tests use the installed SDK with a mocked HTTP transport and require no credentials or live API calls. CI runs the same checks on Python 3.9 and 3.12. `uv.lock` pins dependencies; after intentional dependency changes, regenerate it with `uv lock`.

The CLI lives in `src/adaption_starter/cli.py`. Use the official guide above to extend the starter with dataset creation, adaptation, asynchronous calls, or inference when your hackathon idea is ready.
