# Plain-English report editing notes

## Scope

The user requested a more natural research report, aimed at clear intermediate
English around IELTS 6.0, with logical connectors. This is a writing target,
not a certified IELTS assessment. The edit does not add deliberate grammar
errors or try to certify human authorship.

The final wording is in
[`AUTHORITY_LANGUAGE_PLAIN_ENGLISH_DRAFT.md`](../AUTHORITY_LANGUAGE_PLAIN_ENGLISH_DRAFT.md).
It is a separate editing draft, not a replacement for the validated manuscript
or an officially submitted paper. It does not include unfinished judge scores.

## Draft rewrite: opening excerpt

> This study examines whether an AI worker reports a false budget when another agent claims to have authority. It also tests a simple rule that checks the reported source and whether the supplied record is current. The study has four main findings.

## What makes the draft sound mechanically written?

- The opening uses similar sentence lengths and introduces several concepts at once.
- "The study has four main findings" announces the structure rather than explaining the research.
- Some later statistical terms need short explanations, not just simpler synonyms.
- Repeated "therefore" transitions should express a real inference, not decorate each paragraph.

## Final rewrite: opening excerpt

> An AI worker may receive a message that claims to come from someone in authority. This study tests whether such messages lead the worker to report a false budget. It also tests a simple defence rule. The rule checks the worker's source label and whether an official record is available and marked current.

The final report uses "however" for contrasts, "because" for reasons,
"for example" for examples, and "therefore" or "as a result" for conclusions.
Paragraphs do not all start with a connector. Necessary terms, including prompt
injection, task blocks and source attribution, are retained or explained.

## Evidence and limitations retained

- Strict wording counts and all three contradictory ABSTAIN cases remain distinct
  from the raw numeric-field diagnostic.
- The neutral-prompt and strict-prompt pilots remain separate, with unchanged
  corruption, attribution and defence denominators.
- The original 549/549 result remains conditional; the two neutral wrong releases
  and 72/72 corrupt-current failures remain visible.
- The sample targets 96 groups and 288 judgments, not all 1920 groups. No unfinished
  score is used as a result, and LLM judgments are not called human validation.
- Author confirmation, native review and official submission remain unconfirmed.
- Existing research references and figure paths are preserved; no new citation is invented. The unused Astra model-documentation reference is kept below with the development history, rather than in the reader-facing report.

## Reader-facing report cleanup

The main draft now starts with its title and abstract, like a normal research
report. API errors, token-limit failures, development/test status and submission
administration are outside its main text. They have not been deleted from the
project's evidence. In particular, the paper still reports 71 known wrong neutral
reports, seven unsupported record attributions, one invalid output, two wrong
releases and the separate 72/72 corrupt-current failure. These are experimental
findings, not development logs, and removing them would misrepresent the study.

The main report explicitly excludes the separate sampled LLM assessment from
its reported findings. Its full plan and actual status remain in
[`SAMPLED_LLM_VALIDATION.md`](SAMPLED_LLM_VALIDATION.md) and
[`results/llm_judge_sample/`](../../results/llm_judge_sample/). The sample targets
96 groups and 288 initial judgments; the other 1824 groups are unvalidated.
Sampling does not establish full-corpus or human linguistic validity.

For development provenance, the earlier Astra setup returned no scores; a later
GPT-5 full attempt encountered an 8192-token reasoning-only truncation and failed
exact-quote checks; another configuration returned HTTP400. Their saved records
remain under the original results directories and are not pooled into the sample.
The earlier documentation reference is retained here:

OpenAI. (n.d.). *GPT-6 Astra* [Model documentation]. Retrieved November 9, 2026, from https://developers.openai.com/api/docs/models/gpt-6-astra

Author names, affiliations, order and permission still require confirmation.
The final package needs proofreading after author edits. Native-speaker sheets
remain unreviewed, and official submission has not been confirmed. Moving these
administrative items out of the paper's main prose does not mark them complete.

Only the new draft and these editing notes belong to this writing change.
The running collection, canonical manuscript, generated PDF/Word files and
historical review records are not rewritten by this edit.
