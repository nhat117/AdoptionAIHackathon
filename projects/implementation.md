# Evacuation implementation and pilot commands

The simulator now supports separate A and C pilots through the existing Adaption
Python SDK. Original LangGraph playground behavior is unchanged. This is a
calibration implementation, not a completed research benchmark.

## Run locally

From the repository root (after `uv sync --frozen --extra dev`):

```sh
uv run python -m swarm_lab.evacuation dataset
uv run python -m swarm_lab.evacuation run --study A --limit 20 --output runs/a-offline
uv run python -m swarm_lab.evacuation run --study C --limit 10 --output runs/c-offline
uv run python -m swarm_lab.evacuation.summarize runs/a-offline/outcomes.jsonl
```

Offline mode uses a deterministic mechanical fixture. It checks transitions; its
outcomes are not model results. Each output directory must be new.

For live Adaption calls, configure `ADAPTION_API_KEY` in ignored `.env`. The
example config selects `gemma-4-26b-a4b-it`, temperature 0, and 256 output tokens.
Use `--config` for a different model or sampling configuration.

```sh
uv run python -m swarm_lab.evacuation run --study A --mode live --arm once_fixed --limit 1 --max-calls 60 --output runs/a-live
uv run python -m swarm_lab.evacuation run --study C --mode live --arm correction --limit 1 --max-calls 60 --output runs/c-live
```

Live runs incur credits. `--max-calls` is a hard attempted-call ceiling across the
run, not per episode. No automatic retries, external tools, persistent provider
memory, or response storage are enabled. API errors or invalid actions stop the
run and mark its manifest failed. A whole-response JSON fence is accepted; prose,
invalid actions, nonexistent parent IDs, and nonlocal consultation targets fail.
Earlier completed episodes remain logged. Summaries describe completed episodes
only; always inspect manifests for failures before interpreting a summary.

## Fixed settings and supported variables

- Ten agents on a degree-four ring, own histories, hidden terminal round 4–6.
- A: once/repeated × fixed/chosen reception. First-round messages reach all four
  neighbours; later reception is capped at two. Source stays through round two,
  then chooses actions live while its signal schedule remains controlled.
- C: one shared two-round exposure snapshot per scenario, forked into none,
  removal, factual correction, linked correction, and broadcast correction arms.
  Local correction targets the removed source's neighbours. The source is forced
  to stay during exposure. Removal disables transmissions, not past memories.
- C currently selects incorrect-claim scenarios. Honest-source and sham-removal
  references, no-communication/all-informed baselines, and random-routing
  diagnostics are planned but not yet implemented. Do not treat current output as
  the full proposed evaluation.
- Source labels are stored in scenario rows and delivered as peer claims. For a
  comparison, make matched copies with distinct IDs and change only source_label.
  An emergency title does not authenticate a claim. Specific religious/political
  labels have not been piloted. Initial networks are homogeneous and English-only.

Round decisions use the pre-round state. The final signal of an evacuating agent
is delivered with that round's simultaneous transition; it cannot send later.
Receivers see it on their next decision. No decision sees another decision made
in the same round. Endpoint timing is not disclosed. Payoffs and state-appropriate
outcomes are computed outside the agents.

`manifest.json` records settings, prompt/data hashes, git revision, dirty status,
mode, call count, and completion/failure. `calls.jsonl` records model-visible views
and raw outputs. `traces.jsonl` records decisions and messages; C saves its shared
fork snapshot and hash. Outcomes exclude the controlled source from primary rates.
Raw traces contain potential/selected/delivered links and declared parent IDs;
causal influence, internal attention, and semantic lineage are not inferred.

## Invent candidate stimuli through Adaption

```sh
uv run python -m swarm_lab.evacuation.invent estimate --receipt runs/invent.json
uv run python -m swarm_lab.evacuation.invent launch --receipt runs/invent.json --max-credits 2
uv run python -m swarm_lab.evacuation.invent download --receipt runs/invent.json --output data/evacuation/invent-raw.jsonl
```

Generation uses 12 rows by default and estimates the exact request before launch.
An idempotency key prevents duplicate jobs; retain receipts. Download checks status
once and returns if still running. Reuse `download`, not `launch`, to check later.
Convert completed rows with `swarm_lab.evacuation.stimuli.convert`; the converter
accepts the specified completion JSON shape, deduplicates, and records rejected
row indices/reasons. Candidate pairs need semantic review before `approved` status.

```sh
uv run python -c 'from pathlib import Path; from swarm_lab.evacuation.stimuli import convert; print(convert(Path("data/evacuation/invent-raw.jsonl"), Path("data/evacuation/stimuli.jsonl")))'
uv run python -m swarm_lab.evacuation run --study A --arm once_fixed --stimuli data/evacuation/stimuli.jsonl --stimulus-index 0 --allow-unreviewed-stimuli --output runs/invent-calibration
```

The last command is offline calibration only. For a live calibration add `--mode
live --max-calls 60`. Generated text is attached to the controlled source's signal;
other agents currently relay structured signals and parent IDs, not free-text
paraphrases. This is a deliberate first-pilot restriction. Natural-language relay
and evidence-quality experiments need their own schema and scoring validation.

For plain scenario upload:

```sh
uv run python -m swarm_lab.evacuation.upload --receipt runs/upload.json
```

## Validation

Tests cover deterministic balanced generation, local-view isolation, synchronous
message delivery, irreversible exit, prior-round consultation selection, independent
C forks, correction targeting, payoffs, invalid responses, call budgets, and the
review gate for invented stimuli. Run `uv run pytest -q` and `uv run ruff check src tests`.

## Model comparisons

The account catalog was checked on 2026-11-08. It lists Gemma 4 26B A4B and 31B, Qwen 3.5 397B and 3.8 27B, GLM 5.2 and 5.3 Flash, and DeepSeek V4 Flash. Example configs for Qwen, GLM Flash, and DeepSeek Flash are included for subsequent comparisons. Only Gemma has been exercised in the initial smoke tests. Availability and model aliases may change; recheck the provider catalog and record versions before evaluation. Different models may require different output budgets; freeze any calibrated settings before comparing them.

Each run currently uses one model for all live participants with independent histories. The controlled source follows its assigned schedule. Mixing different models inside one network is not implemented. Invent's generator model is service-controlled and must not be assumed to be the evaluated model.

## OpenRouter as an alternative inference provider

Set `OPENROUTER_API_KEY` in ignored `.env`. Adaption remains the dataset-generation service; evaluation calls can use either provider.

```sh
uv run python -m swarm_lab.evacuation run --study A --mode live --provider openrouter --config examples/evacuation-openrouter.json --arm once_fixed --limit 1 --max-calls 60 --output runs/openrouter-a
```

The OpenRouter example selects `openai/gpt-4.1-mini`, verified in the provider catalog. Requests have no tools, no application retries, and provider fallback disabled. The adapter caps each instruction-plus-input at 16,000 UTF-8 bytes and records returned model, upstream provider, response ID, and usage. The underlying endpoint is not pinned to a named upstream provider, so check recorded metadata and pin routing before a controlled cross-provider study. Parameter support differs by model; the adapter requires requested parameters rather than silently dropping them. A model that does not support temperature needs a separately reviewed configuration/interface change.

Use `--scenario-id calibration-000-1-0` to exercise a specific disaster-present case. Each run remains homogeneous; this provider switch does not mix models inside a network. The shared parser and game rules apply to both providers.
