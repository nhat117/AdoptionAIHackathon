# Evidence controls v3 (72 games)

Follows up two gaps in Experiments 4 and 5:

1. **Is it the content or the authentication?** In Experiment 5, the proof capsule carried true content and an authentication flag together. Section 5b adds a content-matched unverified capsule. If unverified ≈ proof, agents respond to content and formatting. If unverified ≈ text-only, they respond to authentication.
2. **Can verified evidence undo a false claim already received?** In Experiment 4, Danger recipients evacuated before any false claim reached them. Section 6 delivers authenticated truth after a decision exposed to the false claim and counts reversals. Truth first becomes usable in round 3. Under Safe, wrong evacuations in rounds 1–2 cannot be undone and are reported separately.

The game logic is in `src/swarm_lab/evacuation/evidence_v3.py`. The frozen v2 modules are unchanged, and `tests/test_evidence_v3.py` checks their recorded hashes.

## Run

The runner reads and hash-checks both existing original ledgers, so the shared US$35 cap counts all earlier spend:

```sh
PYTHONPATH=src .venv/bin/python reports/evidence-controls-v3/run.py --plan-only
```

The plan-only check makes no calls. Paid collection is a separate, explicit step:

```sh
PYTHONPATH=src .venv/bin/python reports/evidence-controls-v3/run.py --section 5b --model sonnet
```

Cost estimate from matching Experiment 4 and 5 games, which cost about US$0.03–0.26 per game for Sonnet and US$0.01–0.08 for Terra: 5b ≈ US$5.4 and section 6 ≈ US$2.6, about US$8 in total and at most about US$8.7, against US$9.45 remaining. The budget guard stops collection at the cap. Run in priority order: `5b --model sonnet`, `5b --model terra`, `6 --model sonnet`, `6 --model terra`.

Analysis: treat each game as one unit and seeds as the replication unit. For 5b, compare non-witness correct-action rates proof vs. unverified and unverified vs. text-only within each seed, with an exact sign-flip permutation test over the 8 seeds. These results are exploratory, not confirmatory.

## Analysis

The [analysis plan](ANALYSIS_PLAN.md) fixes the unit, contrasts, test and missing-data rule before collection. Run it on saved games with no inference:

```sh
.venv/bin/python reports/evidence-controls-v3/analyze.py --root runs/evidence-controls-v3
```

It writes `summary.json` with per-seed pairs, mean differences, exact sign-flip p-values, the smallest p each contrast could reach, and every failed or missing game.

## Corrected collection checkpoint

See [CHECKPOINTS.md](CHECKPOINTS.md) for authorization, judge reviews, fixes, runs and results. The corrected protocol freezes its plan before any paid call, replays completed games from raw responses, and lists every planned cell including unattempted ones. The original US$9.4543645 remainder is a ceiling, not a guarantee of 72 completions.
