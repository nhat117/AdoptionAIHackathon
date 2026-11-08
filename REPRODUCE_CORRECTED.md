# Corrected budget oversight experiments

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

The last command is a zero-call dry run. Saved historical inputs and outputs
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
