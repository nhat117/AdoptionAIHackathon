# GPT-6 Astra automated multilingual validation

This replaces the proposed manual translation-review gate with a separately labelled **LLM-based** assessment. It does not create human review or independently establish translation/cultural quality. Historical caveats and all original worker outcomes remain unchanged.

## Corpus and independent measurements

- Actual dispatched inputs are joined to saved workers: 1440 primary + 4320 follow-up prompt records, aligned into 1920 English/Vietnamese/Chinese condition groups.
- Full text, trial IDs, locale, role, wording, record state, attack/control, shared context and hashes are preserved. Worker answers/attack outcomes are withheld from the judge.
- Three independent Responses API requests per group, with high reasoning and position-balanced randomized locale order. English is evaluated against the intended construct, not treated as gold.
- Six 1–5 criteria; exact source excerpts are checked. Unknown schemas, quotes, incomplete responses and unverified model identities are instrument failures, not translation failures.
- Median/range/critical-change thresholds are provisional engineering rules. One model repeated three times is not three humans. Intra-model agreement, including undefined kappa cases, is explicitly distinguished from external validity.

## Revisions

A separate draft request generates one suggested correction set for each flagged group. Three fresh reassessments do not receive the initial scores or prior judge responses. Versions are saved separately under `proposed_prompts/`; no historical prompt is replaced. Higher judge scores can reflect self-preference and require a new worker experiment before research reuse.

## Runtime and financial controls

Official `openai` Python SDK, exact `gpt-6-astra`, Responses API, high reasoning, structured JSON output, no tools/previous-response chains, `store=False`. SDK automatic retries are disabled. At most three transport attempts use exponential backoff; invalid judgments are not resampled to obtain preferred scores. Every returned body is durably saved before validation.

Before paid requests, a project cap and aggregate cap are checked under the same locks/shared research ledger as the earlier studies. Costs use documented Standard short-context Astra rates, with conservative cache-write input accounting and retained unknown-billing reservations. The judge cost ledger mirrors event IDs and must not be added again to the authoritative shared ledger total.

Full initial validation requires 5760 requests. Saved cost estimates use explicit byte bounds/output-token scenarios, not invented usage. The full batch is not enabled until a three-response smoke confirms actual model ID and schema. Caps are cumulative, not per invocation.

## Observed execution blocker

The configured Braintrust metadata endpoint returned HTTP405; its Responses smoke request returned HTTP404. A separate direct OpenAI metadata check returned HTTP401 with the configured environment credential. No model response, judge score or translation improvement was obtained. No alternative model was used. The failed request has an unresolved conservative reservation, not a claimed paid inference.

The source corpus, all six required result artifacts and the research report therefore mark the 1920 groups PENDING. Revisions/reevaluation remain unexecuted, not falsely reported as unnecessary. Set a valid rotated key in `OPENAI_API_KEY` and a Responses-enabled `OPENAI_BASE_URL` (or unset it for direct OpenAI) before resuming. Credentials are read only from the environment and never stored in code or result artifacts.

## Tests and preservation

Regression coverage includes corpus counts/alignment/duplicates, literal dispatch joins, schema bounds/types, exact quote validation, English-not-gold aggregation, missing assessments, disagreement/critical rules, kappa degeneracy, revision isolation, capped retry/backoff behavior, nonretryable errors, returned-model checks, official SDK HTTP transport, dry-run no-client behavior and pending-result nonfabrication. CI checks are offline and do not issue paid requests.
