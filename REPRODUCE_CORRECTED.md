# Corrected budget oversight experiments

## Round 3 validity correction

### Active Braintrust GPT-5 judge

**Current scope (supersedes full-run instructions below):** the user requested
random sampling. Run `python scripts/run_sampled_judge.py` for the no-call
preflight, or add `--workflow --cap-usd 60` for the 96-group/288-judgment sampled
workflow. The frozen design selects one of 20 groups in each of 96 strata, without
using prior scores or worker outcomes. The new sample is not pooled with old
ratings. See `research/review_resolution/SAMPLED_LLM_VALIDATION.md` for exact
selection, execution, budget and interpretation. Verify saved sample reports with
`python scripts/report_llm_judge.py --profile gpt5-sample --check`. The US$60
sample cap includes smoke/revisions and remains within the user's cumulative
US$650 approval. The older full-run/v2 attempts below are historical, not active.

**Full-run authorization update:** the user explicitly approved **US$650 total**
research spending, including all previous spending, failed reservations, retries
and revisions. The separate authorization is
`results/LLM_JUDGE_BUDGET_AUTHORIZATION_650.json`; the historical US$20 record is
unchanged. Use the new execution-only extension:

```sh
python scripts/run_full_gpt5_judge.py
python scripts/run_full_gpt5_judge.py --run --cap-usd 650 --workers 8
python scripts/run_full_gpt5_judge.py --revisions --cap-usd 650 --workers 8
```

The first command makes no API calls. The paid stages require the successful
smoke receipt and share one cumulative aggregate cap. Eight concurrent requests
keep local load modest. Original instrument/prompts/settings are unchanged;
`FULL_EXECUTION_PROTOCOL.json` freezes the execution extension and authorization.
New JSONL evidence is split into append-only 8 MiB shards; report rebuilding
combines the original smoke file with every shard. Complete raw replies saved
before interruption are recovered without paying for another answer. A
model/transport/incomplete-response failure stops dispatch; invalid rubric/quote
validation remains a recorded instrument failure rather than a fabricated score.
Completion and any budget/instrument blockers must be checked in the resulting
reports. The original serial runner described below remains a historical entry
point using the original cap and must not be used to bypass the full-run ledger.

`python scripts/complete_gpt5_validation.py --run --cap-usd 650` runs initial
judging, starts flagged-group drafting/reassessment only if all 5760 initial
judgments are valid, then regenerates truthful manuscript/appendix/PDF/Word
outputs after collection has stopped. If a stage is blocked or the cap is
reached, its incomplete status is retained. The wrapper makes no submission,
does not fill author details and cannot substitute for author-edited final
proofreading. At high reasoning effort this full run may take many hours; on
macOS `caffeinate -i` can prevent idle sleep only while the command is running.

`python scripts/run_gpt5_judge.py` freezes/checks the separate GPT-5 profile and
estimates costs without creating an API client. `--smoke --cap-usd 0.5` requests
three schema-checked, language-order-balanced judgments on the first fixed group.
`--run --cap-usd CAP` requires that successful smoke receipt; `--revisions` drafts
and blindly reassesses flagged groups in a separately versioned suggestion set.
All caps are cumulative, and all requests share aggregate accounting, including
failed Astra reservations. The smoke itself is not completed corpus validation;
the new full-run extension above reads the separately recorded US$650 approval.

Configure `OPENAI_API_KEY` and `OPENAI_BASE_URL` for `api.braintrust.dev` without
putting credentials in the repository. The official SDK sends Chat Completions,
strict JSON schema, high reasoning effort, 8192 maximum completion tokens, and
cache-bypass headers. Returned model must be `gpt-5-2025-08-07`. Raw responses,
tokens, failed attempts and cost events are retained under `results/llm_judge_gpt5/`.
Offline verification: `python scripts/report_llm_judge.py --profile gpt5 --check`.
The frozen `run_llm_judge.py` remains the legacy Astra runner, not the active
entry point. Its rubric/schema identifier is intentionally reused as a rubric
version only; the new protocol and response metadata identify the GPT-5 model.
Worker/judge model-family overlap and correlated repeat judgments are limitations.

The canonical pipeline now generates the concise eight-section main manuscript,
`research/ROUND3_APPENDIX.md`, wording×language cells/interactions, raw-field versus
strict-schema diagnostics and R1–R5 remediation under `results/round3/`.
The fixed 180-input neutral pilot is under `results/round3_neutral/`; its runner
`run_round3_neutral.py` is a zero-call preflight by default and requires `--run`
for missing assigned observations. It uses the exact existing neutral worker
system/user-task/schema, GPT-5 minimal reasoning and 512 output tokens, with the
shared aggregate US$20 guard. Do not replace returned malformed answers.

`prepare_round3_review.py` prepares six actual bilingual peer-template anchors or
checks/preserves existing annotations. It never signs native review. The exported
submission checklist distinguishes prepared files from human sign-off and official
submission. Rebuild/check analysis and Word/PDF using the same offline commands;
no API credentials are required for reproduction.

## GPT-6 Astra LLM-based multilingual QA

Install `uv sync --frozen --extra dev --extra reports --extra judge`.
`python scripts/run_llm_judge.py` extracts/alines all 5760 dispatched prompt records
into 1920 trios, freezes provenance and estimates costs without API calls.
`--verify-model` performs a metadata GET only. With working credentials,
`--smoke --cap-usd CAP` attempts three independent Responses judgments; only a
valid model/schema smoke enables `--run --cap-usd CAP --workers 4`.
`--revisions --cap-usd CAP` drafts one separate correction set per flagged group
and blindly reevaluates it three times. Historical prompts are never replaced.
Caps are cumulative; the default aggregate cap remains the previously authorized
US$20. A separately authorized higher `--aggregate-cap-usd` must be explicit.

The configured proxy's smoke returned HTTP404; direct OpenAI metadata returned
HTTP401. No Astra assessment or score was obtained. Set a rotated valid key in
`OPENAI_API_KEY` and a Responses-enabled endpoint (`OPENAI_BASE_URL` unset or
`https://api.openai.com/v1` for direct OpenAI). Do not hardcode or commit keys.
The failed request's unresolved cost reservation is retained, not represented as
verified billed inference. No model substitution or unsupported bulk run occurs.

`python scripts/report_llm_judge.py --check` reproduces the six required artifacts
offline. The canonical research pipeline also rebuilds/checks these artifacts and
the report's explicitly **LLM-based, not human** validation section. Missing
judgments are PENDING, not successful validation. The same model repeated three
times may share biases; cultural equivalence still needs external validation.

## Current canonical pipeline (post-review)

Run `uv sync --frozen --extra dev --extra reports`, then `uv run python scripts/run_research_pipeline.py` and `uv run python scripts/export_review_report.py`. Both commands are offline. Their `--check` modes reject stale analysis, tables, figures, Word and PDF exports. `report_measurement_replication.py --review` and `report_validation.py` now route to this pipeline; `report_validation.py --legacy` reconstructs the earlier report separately without replacing the canonical report.

New inference uses `scripts/run_review_followup.py --stage monitors|pilot|pilot-monitors|committee --run --cap-usd 20`. Without `--run`, it only freezes inputs and records estimates. Do not run merely to regenerate analysis. It reuses the original 1440 workers, preserves original ledgers/data, and uses a new append-only review ledger whose cap checks include the old ledger. Source hashes and assigned IDs are immutable on resume. Every returned body is saved before scoring; errors, unknown billing and pending IDs remain explicit. No credentials are written to reports. The preflight estimated 3828 calls at about US$6.43; actual totals are calculated in the canonical report.

Original result files are protected by `research/review_resolution/PRESERVED.json`. Historical scripts below reproduce older analyses and may rewrite their derived files; run them at their historical commit or in a separate checkout, not over the preserved final evidence. The earlier validation Markdown/Word/export metadata are archived at `research/review_resolution/archive/1dcf401/`.

## Historical commands and design

### Wording-balanced continuation and human handoff

`python scripts/run_authority_wording_followup.py` freezes/verifies the separate 4320-input design and records the cost forecast without inference. Only `--run --cap-usd 20` collects missing assigned IDs using the existing shared ledgers; their pre-collection prefixes are protected by hashes. This run reuses historical scenarios and is not a model-unseen-task or generic authority/culture test. Do not regenerate workers to rebuild analysis.

The same offline `run_research_pipeline.py` produces the follow-up's `analysis.json`, outcomes, wording-specific rates, strict/key-case sensitivity decisions and exploratory contrasts under `results/authority_wording_v2/`. Existing worker/monitor/committee cohorts remain separately scoped. Blind monitors were not run on the new worker-only cohort.

`export_review_report.py --check` verifies published bytes and generation-input hashes plus exact Word/PDF source-content joins. It does not rerender PNGs and require Linux raster bytes to equal macOS bytes. Same-host byte repeatability is separately tested; rendering environment metadata explains portability limits.

`prepare_human_review.py` creates an unfilled 24-row bilingual packet, or verifies and preserves an existing packet without clearing annotations. Preparing it is not human validation. `research/review_resolution/HUMAN_SIGNOFF.md` and `AUTHOR_CONFIRMATION.json` identify the human review and author details still required.

Source branch: `codex/authority-language-v3`, baseline commit
`d38bbd4b225ddebff1c8d1d412ec2902d31d6a41`.
Python 3.11 or newer is required. Run from the repository root.

```sh
python3.11 -m venv .venv311
.venv311/bin/pip install -e '.[dev]'
.venv311/bin/pytest -q
.venv311/bin/ruff check src scripts tests
.venv311/bin/python scripts/replay_corrected_budgets.py
.venv311/bin/python scripts/report_corrected_budgets.py
.venv311/bin/python scripts/run_corrected_experiments.py
.venv311/bin/python scripts/verify_corrected_artifacts.py
```

The collector command (`run_corrected_experiments.py`) is a zero-call dry run;
the last command verifies saved artifacts without inference. Saved historical inputs and outputs
under `runs/` are never overwritten by the new runners. The deterministic replay
uses all 600 rows from `runs/oversight-expansion-v2/trials.jsonl`.
Results are separate under `results/`.

Set `OPENAI_API_KEY` in your environment and `OPENAI_BASE_URL` to your configured
Braintrust proxy. Credentials are never written to output files.
The available model for this run is `gpt-5`, with minimal reasoning effort,
512 maximum completion tokens, no temperature override and no sampling seed.
The returned exact model name and usage are recorded with every completion.
Task assignment uses seed `20261109`. Eight independent worker/monitor requests
or four independent committee games may execute concurrently. Agent handoffs
inside each committee game remain sequential and round delivery is synchronous.

The authorized aggregate cap is US$10. The shared, file-locked ledger reserves
worst-case request cost before dispatch and reconciles successful requests using
returned token usage at US$1.25/M input and US$10/M output. Unknown billing retains
the full reservation. This is a conservative estimate at published model rates,
not a provider invoice; proxy-specific surcharges are not independently verified.
Keep `results/api_ledger.jsonl` when resuming; deleting it resets the accounting.

```sh
.venv311/bin/python scripts/run_corrected_experiments.py --stage pilot --run --cap-usd 10
.venv311/bin/python scripts/run_corrected_experiments.py --stage workers --run --cap-usd 10
.venv311/bin/python scripts/run_corrected_experiments.py --stage historical-monitor --run --cap-usd 10
.venv311/bin/python scripts/run_corrected_experiments.py --stage committee --run --cap-usd 10
.venv311/bin/python scripts/run_corrected_experiments.py --stage new-monitor --run --cap-usd 10
```

Planned calls: 24 pilot + 600 workers + 600 historical monitors + 504 committee
calls + 600 new monitors = 2,328. Calls that fail are retained separately; successful
trial IDs are skipped when resuming. No stopping rule depends on the observed
attack rate. Cross-model replication is blocked because only GPT-5 is available.
The comparison stage deliberately refuses to substitute another model silently.

The original 600-case authority study tests marker disclosure; it is distinct from
the budget-report baseline and is not pooled into the budget results. The completed
Deep Research report and the separately named review were not present in the
provided attachment. The implementation follows the supplied task requirements.

The saved protocol and inputs are immutable on resume. Use a separate results directory for a changed design. GitHub CI runs tests, lint, dry run, replay, report generation and coverage verification without inference credentials. Baseline integrity is checked against the fixed historical commit, including after these changes are committed.

## Improved measurement pilot

`python scripts/run_measurement_v2.py` is a zero-call dry run. Add `--run` to collect 36 worker decisions, or `--committee --run` for six record-access games (126 calls). Both share the original US$10 ledger. Run `python scripts/report_measurement_v2.py` for the saved pilot report. This changes the prospective decision contract; it does not re-label the 591 older ambiguous outputs.

## Multi-task replication

`python scripts/run_measurement_v2.py --replicate` prepares/verifies the fixed 1,440-input design without inference; `--run` resumes missing outputs under the same aggregate US$10 ledger. Use `python scripts/report_measurement_replication.py` for frozen-source/input verification and the paired 20-task analysis, then `python scripts/report_measurement_sensitivity.py` for the separately labeled key-case sensitivity. The replication report and interpretation README distinguish reporting a false target from hidden belief or executed actions.

## Contract and source-truth validation

The latest user authorization is **US$20 total**, using the same shared results/api_ledger.jsonl. Older collectors retain their lower US$10 defaults. New validation collectors use `--cap-usd 20`: `python scripts/run_contract_validation.py` prepares 216 matched inputs and `python scripts/run_corrupt_record_validation.py` prepares 72 separate hidden-corruption inputs. Both are zero-call dry runs unless `--run` is added. Run `python scripts/report_validation.py` after tests to generate the consolidated report from the saved cohorts. No arbitrary-prose or general agent-safety certification is claimed.

## Illustrated offline audit

`python scripts/audit_experiments.py` verifies current collection coverage, frozen
inputs and available source hashes, rescoring the structured worker decisions from
saved content. It generates `research/EXPERIMENT_AUDIT_REPORT.md`, five SVG figures
and `results/experiment_audit/audit.json` using only the existing Python dependencies.
Use `python scripts/audit_experiments.py --check` to fail on missing or stale artifacts.
Both modes make zero inference calls. The historical inventory is file/explicit
completion coverage, not a retrospective revalidation of every legacy scoring rule.
Run `verify_corrected_artifacts.py` separately for baseline integrity and the
existing Word-export freshness check. Do not replace failed historical runs to
obtain a more favorable result.
