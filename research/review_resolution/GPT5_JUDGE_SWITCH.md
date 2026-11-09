# Braintrust GPT-5 judge switch

The active multilingual judge is now the separately versioned
`braintrust-gpt5-multilingual-v1` profile, using Braintrust Chat Completions and
the official OpenAI SDK. The legacy Astra runner, frozen protocol, failed access
events and unresolved spending reservation remain unchanged in their original
locations. No Astra result is relabelled GPT-5.

- Runner: `scripts/run_gpt5_judge.py`; transport: `src/ai2ai_guard/gpt5_judge_api.py`.
- Outputs and current execution evidence: `results/llm_judge_gpt5/`.
- Offline report: `scripts/report_llm_judge.py --profile gpt5 [--check]`.
- Same rubric/schema, exact-excerpt checks, three separate requests per group,
  balanced randomized language order, agreement analysis and blinded revision
  reassessment. The legacy rubric identifier is not a model identifier.
- High reasoning effort, strict JSON schema, 8192 completion-token bound, no
  prior answers in initial/reassessment contexts, cache bypass, at most three
  transport attempts. Invalid model/content/schema responses are not retried
  to obtain preferred scores. Raw returned bodies are retained before validation.
- Every attempt is reserved under the shared append-only aggregate ledger;
  missing usage retains the full reservation. GPT-5 profile caps do not reset
  Astra or previous worker spending. Rates are estimates, not provider invoices.
- The initial smoke is capped at US$0.50 for this GPT-5 profile; the existing
  aggregate authorization remains US$20. No full-corpus run is claimed or
  authorized beyond the available budget.

This is **LLM-based validation, not human validation**. GPT-5 also supplied the
worker answers, so worker/judge correlated errors and model self-preference are
additional limitations. Three repeats are not independent human raters. One
smoke-tested trio is not linguistic validation of the 1920-group corpus.
Historical prompts, GPT-5 attack outcomes and human/author/submission status are
unchanged. The generated validation report gives actual coverage and status.

The smoke completed with three valid structured responses on the expected
`gpt-5-2025-08-07` snapshot. `SMOKE_COMPLETE.json` binds all response IDs to the
frozen GPT-5 protocol. Only one of 1920 aligned trios has received three judgments;
this does not establish full-corpus linguistic validity.

## Subsequent full-run authorization

The user explicitly selected **US$650 total** in the budget question. This is
cumulative research spending, not US$650 extra. The approval is recorded in
`results/LLM_JUDGE_BUDGET_AUTHORIZATION_650.json`, leaving the original authorization
and smoke instrument untouched. `run_full_gpt5_judge.py` and
`gpt5_judge_batch.py` extend only execution/accounting/storage: eight remote
requests, the same frozen GPT-5 instrument, shared atomic reservations and 8 MiB
append-only evidence shards. `FULL_EXECUTION_PROTOCOL.json` freezes the extension.
Revisions use the same remaining cap; exhaustion stops rather than authorizing
more spending. Native review, authors and official submission are not implied.
