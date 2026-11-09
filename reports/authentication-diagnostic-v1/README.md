# Cross-model authentication diagnostic — prepared, not run

**Recommendation: authorize a fresh US$25 inference cap for the full five-configuration diagnostic.** A three-configuration Qwen/DeepSeek/GLM-only option needs a US$5 cap. No paid inference has been run, and this preparation does not authorize spending. The earlier US$35 collection remains closed.

## Prepared scope

- Proposed new configurations: Qwen3.8 27B, dated DeepSeek V4.1 Flash 1017, GLM5.3 Flash. Exact pinned Near AI routes, advertised capabilities, precision and prices are saved in `plan.json` and public endpoint snapshots. These remain candidates until technical preflights succeed and an independent judge admits them.
- References: Sonnet5.5/Google and Terra/OpenAI, evaluated on the same new diagnostic task.
- Eight fresh context templates × two hidden states × six evidence conditions × two wording arms = **192 held-out calls per configuration**.
- Four historical discovery views × two wording arms = **8 discovery calls per configuration**, analysed separately.
- Two technical preflight calls per configuration. **202 calls per configuration; 1,010 total** (606 for the three new configurations only).

The six conditions are direct verified evidence, valid relayed capsules in unauthenticated messages, truthful unverified capsules, false unverified capsules, prose falsely claiming verification, and no focal evidence (possibly with surrounding unverified peer claims). The eight contexts vary prior/later claims, absent/present ancestors, consensus, long histories and carrier/capsule disagreement. Current and clarified wording are crossed with every configuration. The clarification distinguishes carrier authentication from capsule authentication. [PLAN.md](PLAN.md) defines the labels, analysis, limits and checkpoints.

This is a targeted protocol-comprehension extension of prior source-authority auditing, with the overlap and lessons recorded in [RELATED_WORK.md](RELATED_WORK.md). It is a frozen-view diagnostic, not an interacting-network study. Both arms add evidence-status fields, which can itself change behavior relative to historical four-field games. Model size, serving precision and provider remain configuration attributes; model origin is not an explanation of behavior.

## Extra budget (USD inference cost)

Public prices were retrieved on November 9, 2026, without inference calls. Values below include all 202 planned calls per configuration, without assuming cache discounts. The illustrative scenario is **2,000 input + 600 billed output tokens per call**, including any billed reasoning. It is not an empirical forecast. The planning bound uses exact serialized request byte lengths plus a 2,048-token overhead allowance, all 4,096 output tokens and routing price ceilings. It is a conservative allowance under those assumptions, not a provider billing guarantee.

| Configuration | Route prompt/output US$/million | Illustrative cost | Conservative planning bound |
|---|---:|---:|---:|
| Qwen3.8 27B | 0.04 / 1.35 | $0.18 | $1.33 |
| DeepSeek V4.1 Flash 1017 | 0.30 / 1.20 | $0.27 | $1.84 |
| GLM5.3 Flash | 0.08 / 0.50 | $0.09 | $0.67 |
| Sonnet5.5 reference | 2.00 / 10.00 | $2.02 | $11.69 |
| Terra reference | 1.00 / 5.00 | $1.01 | $5.85 |
| **Three new configurations only** | | **$0.54** | **$3.83** |
| **Full five-configuration study** | | **$3.57** | **$21.37** |

Full-study phase bounds: technical preflight **$0.2085375**, held-out **$20.243838**, discovery **$0.921685**. Unrounded per-configuration/per-phase values and maximum request sizes are in [budget-estimate.json](budget-estimate.json). Routing price ceilings are higher than advertised prices for the new configurations and included in the bound. API requests use no tools; retries, full networks, additional hosts, larger output budgets and future revisions are outside this quote. Credit-purchase fees/taxes are not estimated here.

A **$25 fresh cap** gives room above the $21.37 planning bound. The ledger reserves before each request, keeps one request in flight, stops on uncertain billing and never retries attempted cells. The $5 option omits fresh reference-model diagnostic responses, so it cannot supply a matched comparison with the earlier four-field Sonnet/Terra results. The full study is scientifically preferable.

## Safe preparation commands (zero inference)

From the repository root:

```sh
PYTHONPATH=src .venv/bin/python reports/authentication-diagnostic-v1/run.py
PYTHONPATH=src .venv/bin/python reports/authentication-diagnostic-v1/run.py --phase diagnostic
PYTHONPATH=src .venv/bin/python reports/authentication-diagnostic-v1/analyze.py
.venv/bin/python -m pytest -q tests/test_authentication_diagnostic.py
```

These dry-run paths do not read credentials or make network requests. The analyzer reports all jobs unattempted, not failed. `prepare.py` regenerates the prepared dataset/plan only before any live manifest exists; once paid data exist, use a new protocol version for source changes.

## Future execution after explicit budget authorization

The following are documentation examples, **not executed commands or authorization**:

```sh
# Fresh authorization of the chosen full-study $25 cap is required first.
PYTHONPATH=src .venv/bin/python reports/authentication-diagnostic-v1/run.py --execute --cap-usd 25 --phase preflight
# STOP: have the independent judge review the technical receipts.
# It must supply a proceeding review with plan/receipt hashes and admitted models.
PYTHONPATH=src .venv/bin/python reports/authentication-diagnostic-v1/run.py --execute --cap-usd 25 --phase diagnostic --model qwen --preflight-review /path/to/review.json
```

Use the same cap/root across stages; do not start with a $1 frozen cap and then silently increase it. Technical preflight itself is about $0.21 of the full-study planning bound and has only ten calls. Admission uses format, finish, route and billing validity, never correct behavior. Repeat diagnostic dispatch for each admitted model. Failed/incompatible configurations remain logged; do not silently substitute hosts or raise token limits. The runner's canonical root is `runs/authentication-diagnostic-v1`; it does not touch prior ledgers.

[CHECKPOINTS.md](CHECKPOINTS.md) contains independent judge reviews and preparation decisions. The public snapshots are not live inference receipts. For provider semantics see [OpenRouter's model catalog documentation](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties), [provider routing](https://openrouter.ai/docs/guides/routing/provider-selection) and [DeepSeek's thinking controls](https://api-docs.deepseek.com/guides/thinking_mode/). Native DeepSeek low support does not prove the selected OpenRouter route's behavior.

## More adventurous directions

[EXPERIMENT_IDEAS.md](EXPERIMENT_IDEAS.md) develops the honest liar, evidence telephone, nine against one and paid verification. These are proposals for later interacting studies, with controls and a preliminary related-work check. They are outside the diagnostic budget and have not been run.
