# Outstanding-work continuation

Baseline: `4faa911`. This appendix records implementation work, not additional main reports.

## Wording-balanced follow-up

- Fixed 4320 workers: 20 existing task clusters × 4 role claims × 3 wording variants × 3 languages × 3 record states × clean/attack.
- Same 20 scenarios as the earlier replication, not model-unseen tasks. Three wordings are fixed exemplars, not a random sample of authority language. Native review is still required.
- Frozen config: `configs/authority-followup-v1.json`; original wording source remains byte-identical. New clean controls match role/variant without supplying a budget.
- Dispatch seed 20261113; GPT-5, minimal reasoning, 512 output tokens, no sampling seed. Twelve independent requests may run concurrently.
- Historical structured-worker mean implies US$4.834605; 15% planning allowance US$5.559796. Remaining budget before dispatch was US$7.91899465. This is a forecast, not an invoice or permission to exceed the aggregate US$20 cap.
- Worker-only: deterministic comparators run offline. No new blind-monitor performance will be inferred from the previous cohort.
- Strict primary and explicit key-case sensitivity, task-block bootstrap/sign-flip/Holm analysis; wording-specific rates/differences are descriptive pointwise summaries. No generic causal authority/culture claims.
- `results/authority_wording_v2/PROTOCOL.json` freezes inputs/sources and records the byte lengths/hashes of existing shared log prefixes. Logging is append-only; previous records cannot be rewritten.
- Fixed assigned IDs or budget/infrastructure stop, never stopping on an observed effect. Schema failures remain observations; any missing transport responses remain explicit. Existing observed answers are never replaced.

## Portable export verification

The GitHub Linux jobs passed tests and data/pipeline checks, then failed at byte-regenerating `monitor_comparison.png`. Both locally tested Python versions matched the macOS export; PNG bytes can depend on host rasterization or compression libraries. This is not evidence of changed experimental numbers.

Portable checks now verify the published artifact byte hashes; canonical source, renderer, dependency lock, SVG and embedded-font hashes; exact Word paragraphs/tables/image joins; and ordered PDF text against the canonical source. These checks do not require pixel regeneration on another OS and do not silently replace reviewed exports. Same-environment byte repeatability remains a separate test. Export metadata records the rendering environment.

Regressions include corrupted images, altered source/SVG, missing manifests and invented Word/PDF content even when an artifact's hash is re-recorded. CI must be verified on GitHub after publishing the completed continuation.

## Human work

`NATIVE_REVIEW_PACKET.csv` has 24 unfilled Vietnamese/Chinese comparisons, English anchors and clean controls. `HUMAN_SIGNOFF.md` explains sign-off, correction versioning and consent. `AUTHOR_CONFIRMATION.json` is intentionally unfilled. No reviewer, author, affiliation, completion date or human validation will be invented.
