# Three bounded swarm pilots

This work continues PR #5 on `codex/two-research-proposals`. The scope is the user-approved exploratory pilot, not the full proposed six-model matrix or a submission. The durable goal is tracked in Codex; [GOAL.md](GOAL.md) records the protocol and handoff checklist.

## Frozen design

Sonnet 5.5 is served through OpenRouter with only `google-vertex/global` allowed, fallbacks disabled, required parameter support, explicit low reasoning, strict JSON, a 2,048-token output ceiling, and a 64,000-byte input ceiling. The upstream provider is verified in every returned response. We retain the original English/Vietnamese packs, marked **pending bilingual review**. Identity labels are fictional source attributions and grant no additional evidence or permissions.

| Section | New games | Conditions and reuse |
|---|---:|---|
| 1: language | 16 | Two scenario seeds × four disaster/accuracy cases × English/Vietnamese; ordinary peer, ring. |
| 2: identity | 40 | One seed × four cases × two languages × five additional labels. Eight ordinary-peer games are shared from section 1. |
| 3: network | 16 | Two scenario/graph seeds × four cases × two languages on connected random-regular graphs. Sixteen ring baselines are shared from section 1. |
| Total | 72 | Unique new games; no double-counting shared baselines. |

Both graph types have ten nodes, four neighbours per node, and twenty undirected edges. Seeds 1000 and 1001 rotate the controlled source between positions 6 and 0 and generate distinct random graphs. They provide only two graph/source configurations, not broad evidence about networks. Identity contrasts have one scenario seed per state/accuracy case. All experiments use a controlled broadcaster in rounds 1–2 and live interacting recipient agents.

The maximum newly reported API spend is **US$35**, shared across all sections. Before each request, the runner reserves US$0.20, conservatively above the allowed prompt/output charges. A pending or uncertain request is never replayed. Missing cost metadata, unexpected upstream routing or reasoning metadata, and uncertain billing stop new requests. Invalid decisions remain failed games, with no automatic retries or silent repairs. Game order is deterministically shuffled within sections; sections run sequentially with at most four concurrent games.

Provider routing follows [OpenRouter's official provider selection documentation](https://openrouter.ai/docs/guides/routing/provider-selection). The endpoint was checked before launch: input US$2/million tokens and output US$10/million tokens; the live ledger reserves against these verified prices. A review during collection found that the optional `max_price` field is added by a callback after request serialization, so that server-side price filter is **not transmitted in collection version 1**. The per-call reservation ledger, bounded token sizes, endpoint restriction, returned-cost validation and US$35 total stop remain active. The serialization order was corrected and regression-tested after the frozen batches completed; the separately versioned diagnostic runner transmits the filter before any request. Historical v1 evidence remains auditable at revision `4971692`. Low is a requested provider-specific setting, not equal computation across model families or proof of a particular hidden reasoning process.

## Verification and interpretation

[analyze.py](analyze.py) replays each saved completed round from the raw model response and exact local view. It compares every transition and state hash with its recorded trace and recomputes the final outcome. It also verifies frozen source/pack hashes, call counts, provider, model, reasoning request, and finish status. Each section retains a compressed raw archive, per-game CSV, frozen plan, machine-readable audit, and plots. Partial failed games remain in the archive and reliability denominator; behavioral contrasts use only completed matched pairs and disclose missing pairs.

Whole games are the analysis units. Individual agents influence one another and are not independent samples. Dots show individual games; bars are descriptive means. No confidence intervals, hypothesis-test claims, or general language/cultural/political conclusions are justified by this pilot. Shared baselines create dependence across comparisons. A claim-matching signal is an enum, not a semantic audit; citing a message does not establish agreement, and receiving a warning does not establish belief. Translation compliance and refusals still need human review.

## Reproduce or continue

From the repository root, with the local virtual environment and a local `.env`:

```sh
PYTHONPATH=src .venv/bin/python reports/overnight-experiments/run.py --section 1
PYTHONPATH=src .venv/bin/python reports/overnight-experiments/analyze.py --section 1 --source-revision 4971692
```

Repeat for sections 2 and 3 only after auditing, analyzing, committing, pushing and reporting the prior section. An existing attempted game, including a failure, is skipped rather than reissued. Protocol/source changes require a new versioned run root. Analysis uses Matplotlib 3.11.2 and NumPy 2.5.4; these are plotting dependencies, separate from the inference runtime. The optional commands above do not authorize additional paid runs beyond the frozen plan.

## New diagnostic extension

The user approved a second-model check and evidence/control experiments 4–5. [Decision log](DECISIONS.md), [frozen diagnostic plan](extension-plan.json), and [dataset card](../../data/diagnostics-v2/README.md) document forty separately versioned games. Use `extensions.py --section terra`, then `--section 4` and `--section 5`, with analysis and reporting between sections. The original three-factor findings and failures remain unchanged.
