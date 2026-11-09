# Dataset locations

## Current 600-response expansion

[oversight-expansion-v2](../runs/oversight-expansion-v2/) contains 600 actual worker responses from **50 task IDs**, with 200 responses per review-note language. The experiment repeats each task across three note languages, two source conditions and two evidence-access conditions. These are not 600 independent tasks or 50 task families.

| File | Contents | Records |
|---|---|---:|
| [Expansion inputs](../runs/oversight-expansion-v2/inputs.jsonl) | Exact prompts, source reports and expected facts | 600 |
| [Raw expansion trials](../runs/oversight-expansion-v2/trials.jsonl) | Provider output, usage, oracle scoring and paired gate decisions | 600 |
| [Readable JSON outputs](../submission/expansion-v2/recorded-outputs.json) | Peer inputs, expected facts, raw worker text and release decisions | 600 |
| [Readable CSV outputs](../submission/expansion-v2/recorded-outputs.csv) | Flat inspection view | 600 |

[Protocol](../runs/oversight-expansion-v2/FROZEN_PROTOCOL.json) · [metrics](../runs/oversight-expansion-v2/metrics.json) · [report](../submission/expansion-v2/README.md). The original 24-response pilot below and the older selected 600-case authority dataset are separate cohorts.

## Preserved 24-response pilot dataset

The controlled follow-up uses **24 saved responses**, from twelve source cases evaluated with and without trusted input. There are eight responses per peer-message language (English, Vietnamese and Chinese), but only two underlying task groups. Language variants and gate checks reuse tasks and candidates.

| File | Contents | Records |
|---|---|---:|
| [Input dataset](../runs/oversight-ablation-v1/inputs.jsonl) | Exact prompts, peer reports, metadata, expected facts and evidence condition | 24 |
| [Raw run records](../runs/oversight-ablation-v1/trials.jsonl) | Original inputs, provider responses, usage, independent scoring and gate decisions | 24 |
| [Readable JSON export](../submission/figures/all-recorded-outputs.json) | Peer report, expected facts, parsed worker output and guard decisions | 24 |
| [Readable CSV export](../submission/figures/all-recorded-outputs.csv) | Trial ID, language, source type, evidence condition, expected/returned budget and decisions | 24 |

The [frozen protocol](../runs/oversight-ablation-v1/FROZEN_PROTOCOL.json) records the collection plan. [Metrics](../runs/oversight-ablation-v1/metrics.json) contain outcome counts; [figure provenance](../submission/figures/provenance.json) records source hashes and plotted values. The [archived replay](../runs/oversight-ablation-v1/archived_first_hop_replay.jsonl) is a separate retrospective check of older responses, not additional model calls.

## Earlier 600-case dataset

[authority500/selected_600_cases.jsonl](authority500/selected_600_cases.jsonl) contains **600 cases: 200 English, 200 Vietnamese and 200 Chinese**. The folder retains its historical `authority500` name even though this selected file has 600 cases. It is separate from the current 24-response controlled follow-up; its sample count must not be used as the denominator for the current report.

Generation and selection records are in [authority500/](authority500/), including the [generation protocol](authority500/GENERATION_PROTOCOL.json), [manifest](authority500/MANIFEST.json) and [quality audit](authority500/QUALITY_AUDIT.json). Other historical experiments are indexed in [ARCHIVE.md](../ARCHIVE.md).

These are synthetic research tasks. Added navigation does not modify any dataset or run record. JSONL contains one JSON object per line. Use the exact relative paths above after cloning the research branch.

## Proposed budget committee specification

[budget-review-v1](budget-review-v1/) contains a design example only. It has not been executed and must not be counted as experiment data.

## Separate live budget committee calibration

- [V1 raw traces](../runs/budget-swarm-calibration-v1/episodes.jsonl): eight responses, all stopped at offer-stage formatting; no committee outcomes.
- [V2 scenarios](../runs/budget-swarm-calibration-v2/inputs.jsonl), [raw traces](../runs/budget-swarm-calibration-v2/episodes.jsonl) and [metrics](../runs/budget-swarm-calibration-v2/metrics.json): eight assigned episodes, 145 actual responses, six complete episodes and two retained protocol failures.
- [Readable report](../submission/budget-swarm-calibration-v2/README.md), [summary CSV](../submission/budget-swarm-calibration-v2/episode-summary.csv) and [actual sample traces](../submission/budget-swarm-calibration-v2/sample-traces.json). These English-only calibration data are separate from both reporting cohorts.
