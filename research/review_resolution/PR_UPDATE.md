## Scope

Implements the engineering and analysis actions from the full follow-up review (N1–N11), maps A1–A9, reruns the required evaluations, and generates one canonical report. **This does not claim that outstanding human validation or all research limitations are resolved.**

Issue-by-file plan: `research/review_resolution/PLAN.md`.
Implemented/validated/pending ledger: `research/review_resolution/STATUS.md`.

## Code and analysis

- Versioned strict/normalized outcome scoring separates peer-number relay, stale-record reliance, current-record grounding, abstention and other errors.
- Deterministic source-only and source+freshness baselines explicitly handle missing, malformed, ambiguous and deceptive provenance. Worker abstentions are separate. Experimental trusted-record origin is not external authentication.
- Record-stratified language/authority rates, matched task-bootstrap intervals, exact task sign-flip tests, 32 exploratory contrasts/interactions and Holm adjustment. No IID trial-level or general causal authority/culture claims.
- Original blind monitor unchanged (AST regression test); new policy-aware blind monitor receives visible evidence and task policy, never evaluator truth. Information-access differences are explicit.
- Detector v2.2 handles reviewed amount labels, multilingual written amounts and local qualification scope. Fifty known-answer cases pass. Development on saved false positives is disclosed; v2.1 and its nine false positives are archived, not hidden.
- New immutable protocols, durable API-body saving, append-only cost accounting, shared old/new cap enforcement and offline reproducible reporting/export checks.

## Verified findings

- Main GPT-5 study: **90 strict** peer-number relays; **91** with separately labelled key-case normalization. All 91 normalized outputs say `peer`; the review's missing-source example uses `Evidence` instead of `evidence`.
- Source-only blocks 91/91 normalized relays but passes **458 stale-record uses**. Source+freshness blocks those too, with **0/479 false blocks** of correct reports in this saved cohort. Neither result proves secure provenance.
- The requested strict language counts reproduce: absent EN/VI/ZH **23/80, 11/80, 41/80**; stale **11/80, 0/80, 3/80**; current **0/80, 0/80, 1/80**. Chinese/English directions reverse by record condition; the relevant Holm-adjusted tests do not justify a significance claim.
- Historical Gemma-worker/GPT-5-monitor cohort: original blind monitor blocks **0/150 wrong budgets**, falsely blocks **115/450 correct reports**, and abstains on 144 wrong reports.
- New monitor comparison reuses all 1440 GPT-5 workers: original blocks **78/549 wrong reports**; improved blocks **241/549**, still allows **308/549**, and falsely blocks **4/479** correct reports (normalized reference). It is not presented as an effective replacement for deterministic freshness checking.
- Provenance pilot: **36 workers + 72 monitor evaluations**, no observed strict false-record attributions. No successful bypass or incremental checker benefit is claimed.
- Boundary committee: expense **13000**, true cap **12000**, planted cap **18000**; **40 terminal games, five per cell**. No final planted-cap reports, one wrong clean-control decision, two unresolved games. **839/840 responses** returned; the failed turn is retained as a non-vote, not replaced.

## Execution, cost and preservation

**3828 attempted calls; 3827 returned model bodies.** Aggregate accounted cost **US$12.08100535 / US$20**, including original spending and the unresolved reservation. This is not a provider invoice. No original worker answer was regenerated.

All **271 protected original data/result files** remain byte-identical. Earlier canonical Markdown/Word/export metadata are archived. Raw prompts, response IDs, actual model IDs, usage, versions, source hashes and retained failures are available under `results/review_v3/`.

## Deliverables and checks

- Canonical source: `research/VALIDATED_RESEARCH_REPORT.md`.
- Derived PDF/Word: `submission/final-review/Authority_Language_Final.pdf` and `.docx`.
- Five SVG/PNG figures, CSV contrasts/rates/translation inventory and machine-readable analysis.
- **327 tests passed locally on Python 3.11 and 3.12**; lint, offline analysis/export freshness, baseline integrity and original-audit checks passed.
- CI performs no inference and verifies preserved inputs and current deliverables rather than rewriting historical result files.

## Explicitly outstanding

- Native-speaker Vietnamese/Chinese review **REQUIRED**, not performed. AI inspection and ten sampled abstentions are not human validation.
- Three new wordings per authority/language are prepared, but the larger wording-balanced authority replication is **not executed**.
- Independent held-out prose adjudication, broader models/tasks and external record authentication remain unvalidated.
- Author names/affiliations require confirmation; no official hackathon submission or merge has been performed.
- The old dashboard remains historical, explicitly labelled; it is not represented as current results.
