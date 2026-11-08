# Fresh-task check of the repaired facts guard

The repaired implementation completed **48/48 initial cases** with **0 errors**. These are new Adaption requests, separate from development replay. Both the repair and inputs were frozen before these requests.

| Model | Attacks | Targeted failures before / after guard | Correct clean releases | Correct attack-task releases | Retries |
|---|---:|---:|---:|---:|---:|
| gemma-4-26b-a4b-it | 12 | 0 / 0 | 12/12 | 12/12 | 0 |
| deepseek-v4-flash | 12 | 0 / 0 | 12/12 | 12/12 | 0 |

This small check uses four previously unused heldout task clusters, crossed with two models, three languages and clean/attack input. Numeric, categorical, distributed and composite attack families were fixed from development. All 80 tasks assigned to the stopped 500-case run, all 100 earlier 600-case tasks and all 100 live-challenge tasks were excluded before deterministic selection. Facts are synthetic. There is one clean/attack sample per condition, no bilingual review and no authority comparison.

The repair verifies supported fields and renders the released summary exclusively from caller-owned trusted data. It does not forward unchecked model prose. This is a deliberately restricted reporting product, not general semantic verification.

If both baseline and protected attack failures are zero, this confirms observed clean-task compatibility but cannot establish added security benefit. Conditional guard recall is undefined (`null`) without model failures. With only four task clusters, these results do not justify broad failure-rate bounds, language effects or universal protection claims. Development observed one genuine factual substitution accepted by the original guard; that case is documented separately and is not pooled into this fresh-task result.

Run `uv run python scripts/report_near_target_confirmation.py` to reproduce this table. See the frozen protocol, raw per-model JSONL, `CONFIRMATION_METRICS.json` and `CONFIRMATION_RESULTS_48.csv` in the evidence bundle.
