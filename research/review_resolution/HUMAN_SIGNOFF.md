# Human actions still required

**Workflow update:** the user chose sampled automated multilingual QA: 96 randomly selected aligned groups, 288 initial Braintrust GPT-5 judgments (`results/llm_judge_sample/`). The generated report states actual completion/blocker status. This is sampled LLM-based validation, not full-corpus or human validation. Earlier full-run/GPT-5/Astra attempts remain preserved separately. The native-speaker packet below is retained for optional external validation, not presented as a completed human gate or replaced with fictitious human ratings. No human validation has occurred. Author confirmation remains a separate human action.

## Native-speaker review

`NATIVE_REVIEW_PACKET.csv` contains 24 bilingual comparisons: four roles × three wordings × Vietnamese/Chinese, each with its English anchor and a matched clean control. The displayed amount is a labelled placeholder, not an experimental observation.

Ask a native Vietnamese reviewer to complete the 12 Vietnamese rows and a native Chinese reviewer to complete the 12 Chinese rows. Record native-language attestation, meaning equivalence (pass/fail/uncertain), naturalness, perceived authority and persuasive force (1–5), reviewer name/date, and corrections. Compare the full request and its persuasive strength, not just dictionary translations. Do not have an AI fill in or sign these human fields.

Import the CSV as UTF-8 in a spreadsheet application. Add corrections in the notes column rather than replacing the supplied text. Keep role rank, language naturalness and task-relevant persuasive force as separate judgments; a system administrator is not automatically the most credible authority on a budget.

No completed native-speaker linguistic review has been recorded. Running `scripts/prepare_human_review.py` preserves an existing packet rather than clearing annotations. Corrections must produce a new template version and cannot replace already-collected prompts. A post-collection review must not be represented as pre-collection validation.

The [technical handoff review of `39368ec`](TECHNICAL_HANDOFF_39368ec.md) is not a native-speaker attestation or Bao Thach's personal sign-off. Do not fill or sign any linguistic-review or author-confirmation fields from that comment; its PDF inspection covered the first page only.

## Authorship

Please supply each author's confirmed display name and affiliation, preferred order and permission to appear on the final report. A GitHub handle or commit author is not sufficient confirmation. No name or affiliation will be invented.

`AUTHOR_CONFIRMATION.json` is an intentionally unfilled record of this pending confirmation.

## Submission

After confirmed author edits and any language-review changes, regenerate and inspect the final PDF/Word. If native review has not occurred, retain that limitation rather than marking it complete. Official submission requires the actual destination, required declarations and authorized access; a pushed PR is not a hackathon submission. Retain an actual confirmation if submission succeeds.
