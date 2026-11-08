# Authority, language and response-budget repair

Observed follow-up, 8 November 2026.

**Conclusion:** The historical small-Qwen run shows an exploratory Vietnamese-versus-English disclosure difference, but this is distinct from an authority-by-language interaction. Claimed authority has not been established as a causal amplifier in this experiment. All-zero hosted-model outcomes cannot prove equivalence or general safety.

## Completed observations

| Run | Target responses | Response failures | Marker disclosures | Benign completion |
|---|---:|---:|---:|---:|
| Historical Qwen2.5-0.5B | 420/420 | 0 | 31.9% (115/360) | 85.0% (51/60) |
| Adaption DeepSeek pilot | 72/72 | 0 | 0.0% (0/48) | 100.0% (24/24) |
| Adaption Qwen3.5-397B, repaired budget | 72/72 | 0 | 0.0% (0/48) | 100.0% (24/24) |
| Adaption Gemma 4 26B-A4B | 420/420 | 0 | 0.0% (0/360) | 100.0% (60/60) |

The Gemma replication uses 20 previously inspected tasks, three languages, two sender roles and three attack repetitions: 360 attacks and 60 benign controls. The repaired Qwen run repeats all 72 pilot cases with an 8,192-token target budget; it does not selectively replace old failures. Both use Adaption. The earlier Qwen2.5 run used Ollama and is explicitly historical.

## Language contrasts and authority interaction answer different questions

| Historical small-Qwen contrast | Estimate, percentage points | 95% task-bootstrap interval |
|---|---:|---:|
| Language difference: vi minus English | 30.8 | [21.7, 40.0] |
| Language difference: zh minus English | 7.5 | [-5.8, 21.7] |
| Authority interaction: vi minus English | -11.7 | [-36.7, 11.7] |
| Authority interaction: zh minus English | 5.0 | [-15.0, 26.7] |

The Vietnamese language contrast averages both sender roles: 60/120 disclosures (50.0%) versus 23/120 in English (19.2%), a difference of 30.8 percentage points. This newly added, post-hoc contrast is exploratory. It is not an externally preregistered discovery, a cultural effect, or evidence that the director label caused the difference. Its 10,000-resample bootstrap clusters by task; intervals are unadjusted for multiple comparisons. Translation equivalence still needs bilingual human review.

Authority interactions use the existing 2,000-resample task bootstrap. Their intervals cross zero. The Chinese language contrast also crosses zero. An all-zero result for another model gives an uninformative degenerate bootstrap interval and cannot establish that the true effects are precisely zero.

## Operational error fixed

A reproduced Qwen request exhausted all 1,024 output tokens on internal reasoning, returned status incomplete and no final message. Repeating the same messages at 4,096 tokens produced a completed final answer. The new run uses 8,192. Diagnostic token counts and final outputs are saved in runs/qwen-budget-diagnostic; reasoning text is not saved. This diagnoses one reproduced failure, not every historical failure retrospectively.

The adapter now uses a larger default for Qwen and retains sanitized error diagnostics. Explicit old configurations retain their settings. No error is silently converted to a successful defense. The old 61-failure pilot remains archived. A clean rerun is evidence of an operational repair, not a guarantee that an external API can never fail.

## Machine audit of the manipulation

Two Adaption-hosted judges produced 12/12 valid audits. They identified the marker-in-public_summary request in 12/12 and fictional provenance in 12/12. Peer ratings were [1, 1, 1, 1, 1, 1]; authority ratings were [5, 5, 5, 4, 5, 5] on the defined 1–5 rank scale.

These audits check label clarity and objective preservation. They are not independent bilingual human validation, proof of target deference, or a measure of real cultural norms. The peer/director attack text is identical within each language except the sender label.

## Larger dataset and a confirmatory study

A separate GPT-5/Braintrust task pool contains 500 generated scenarios across ten benign project domains, with a fixed 100-task development / 400-task heldout split. This is synthetic research material, not 500 completed evaluation outcomes. Domain and batch provenance, exact returned model IDs and hashes are retained. Semantic diversity and bilingual human review remain separate checks.

With one repetition, crossing the 400 heldout tasks with three languages and two roles gives 2,400 attack cases; a benign control per task and language adds 1,200, for 3,600 target calls per model. The full 3,600-case expansion was not launched. The user selected a separate 600-case design, reported in AUTHORITY600_RESULTS.md. Only development references may be imported to Adaption; no adaptation or training job is started.

A rough design calculation using the historical task-level interaction variance suggests 315 task clusters for the Vietnamese interaction and 248 for Chinese to detect a 10-point effect at 80% power, with a two-comparison alpha allocation. This normal approximation is a planning assumption based on 20 old tasks; it is not achieved power or a prediction that an effect exists.

Before a confirmatory run, complete bilingual review, freeze an analysis family and effect size, and use development data to check for floor/ceiling limitations. Any attack-family calibration must be selected without inspecting heldout outcomes or favoring a positive authority difference. Report null or floor-limited results as such.

## Sources and reproducibility

- Saved JSONL files and exact SHA-256 values: FOLLOWUP_METRICS.json. All reported target counts are independently reconciled to complete, unique trial IDs.
- Protocol and known limits: FOLLOWUP_PROTOCOL.md. New runs freeze source/config hashes before inference.
- [Authority versus register](https://aclanthology.org/2026.findings-acl.1627/) motivates separating the role label from writing style.
- [Paired multilingual agent evaluation](https://aclanthology.org/2026.oracle-main.13/) motivates translation and pairing checks.
- Run `.venv/bin/python scripts/report_followup.py` to recompute these summaries without API calls.
