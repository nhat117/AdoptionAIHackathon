# Execution evidence

Branch: codex/authority-language-v3
Baseline commit: d38bbd4b225ddebff1c8d1d412ec2902d31d6a41
Returned model: gpt-5-2025-08-07 (requested alias gpt-5).

- Tests: 182 passed; lint: passed.
- Original budget outputs replayed: 600; historical files changed: 0.
- Imperfect-record judgments: 2,400 across four synthetic record conditions.
- Pilot completions: 24.
- Corrected worker completions: 600.
- Historical blind-monitor completions: 600.
- New-output blind-monitor completions: 600.
- Committee games: 24; saved agent calls: 504.
- Total successful saved study completions: 2,328.
- Additional successful responses in an interrupted partial game: 3; ledger records retained, response bodies unavailable, excluded from completed-game analysis.
- Total successful responses accounted in ledger: 2331.
- Token cost at published uncached GPT-5 rates: US$3.388547.
- Conservative accounting including unresolved reservations: US$3.397935, within US$10 authorization.

Executed commands are listed in REPRODUCE_CORRECTED.md. All five authorized stages
were executed with --run --cap-usd 10. The initial unsupported-model attempts
returned direct-endpoint HTTP 401 and proxy HTTP 404; no completions from those
requests were analyzed. GPT-5 collection succeeded after the model correction.
The first completed committee game was saved before restarting serial collection
with parallel game scheduling; three responses from the next partial game lack
saved bodies. The final runner journals raw responses immediately.

Cross-model replication was not executed: the user confirmed GPT-5-only access.
Bilingual human validation, human adjudication of ambiguous worker claims, and
requirements in the unprovided separate review/Deep Research report remain open.
No model-general safety conclusion is made.

Primary result files:
- results/corrected_replay/decisions.jsonl
- results/corrected_replay/metrics.json
- results/pilot/outputs.jsonl
- results/workers/outputs.jsonl
- results/worker_rescored.jsonl
- results/historical-monitor/outputs.jsonl
- results/new-monitor/outputs.jsonl
- results/committee/outputs.jsonl
- results/prospective_metrics.json
- results/statistical_analysis.json
- results/summary.csv
- results/PROVENANCE.json

Final integration: frozen CI dependencies validated on Python 3.11; experiment resume rejects changed protocols; provenance uses the fixed historical baseline across later commits. GitHub CI also verifies replay, report regeneration and artifact coverage without API calls.

## Improved measurement pilot

A separate measurement_v2 pilot completed 36 workers and six committee games (126 calls). All 36 primary decisions were scorable. Tests now pass 192 cases. The original execution figures above describe the original study snapshot; the shared ledger now also includes this pilot. Absent/stale committee conditions contain no authenticated true cap. See measurement_v2/REPORT.md for counts and limitations.

## Multi-task replication

All 1,440 worker requests completed with zero collection errors on 20 matched task clusters. Strict scoring yields 1,437 valid decisions and three invalid formats; a secondary key-case normalization resolves all three without changing strict primary scores. All original raw observations remain available. There are now 194 tests. The aggregate accounted cost across studies is approximately US$5.40, within the original US$10 authorization. Paired task-bootstrap estimates, uncertainty bounds, 13 exploratory contrasts, and multiplicity-adjusted-tail intervals are saved in measurement_v2_replication/metrics.json. See its interpretation README and SENSITIVITY.md before using the reporting rates as evidence of unsafe behavior.
