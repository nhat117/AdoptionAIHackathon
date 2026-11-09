# Authority and language follow-up: analysis and operational repair

8 November 2026. Local protocol registration; not an external preregistration.

## Question and estimands

The primary scientific question is whether changing only a fictional sender's
claimed authority changes marker-disclosure risk differently across English,
Vietnamese and Chinese. A language main contrast is a different estimand from
this authority-by-language interaction.

- Authority contrast: authority minus peer ASR within each language.
- Interaction: that authority contrast minus the English authority contrast.
- Language contrast: Vietnamese or Chinese minus English, averaged over sender
  roles and repetitions, pairing the same task and resampling complete tasks.

Language main contrasts are newly added exploratory analyses after inspecting
the earlier outcomes. They must not be described as a preregistered discovery.
Language is not a proxy for culture. Differences pertain to these exact prompts,
translations, tasks, model and provider configuration.

## Operational repair

A saved failing Qwen case was repeated with the same messages. At a 1,024-token
cap the response status was incomplete, all 1,024 output tokens were reported
as reasoning tokens, and no final message was returned. At 4,096 tokens a final
answer completed. This supports output-budget exhaustion in that reproduced
case; it does not diagnose every historical empty response retroactively.

The default Qwen adapter budget is now 8,192 tokens. Other hosted models retain
1,024 unless a run supplies an explicit cap. Explicit old configs retain their
original settings. Empty responses raise a structured error retaining status,
usage, response ID and item-type labels, never reasoning text. No empty response
is silently retried or converted to a successful defense.

Run `h1-adaption-qwen-budget-repair` repeats all 72 pilot cases, not only the 61
old failures, with a target cap of 8,192. Its two DeepSeek monitor conditions
remain at 1,024. The original run remains immutable and separately reported.

## New hosted-model replication

Run `h1-adaption-gemma-replication` uses gemma-4-26b-a4b-it via the official
Adaption SDK: the same 20 previously inspected tasks, three languages, two sender
roles, three attack repetitions and one benign repetition. Planned total:
360 attacks and 60 benign controls. Target cap 2,048; temperature 0.7. No monitor
calls: this run addresses H1, not monitor context. The model and complete fixed
design were chosen before examining this run's target outcomes. All cells and
failures are reported; there is no stopping on a favorable authority effect.
This is an exploratory model replication, not a fresh held-out task study.

Both runs explicitly disable tools, memory and response storage, preserve role
boundaries and use the same correction template. Calls are paced per process;
429 retries are bounded and logged. Failed collections are not a defense result.

## Manipulation checks and inference limits

Two Adaption-hosted judges audit all six language-by-role messages (12 checks),
rating claimed social rank and checking the marker-in-public_summary objective,
fictional provenance and English backtranslation. This is an automated semantic
and label audit, not independent bilingual human validation, a culture measure,
or proof that the attacked target perceives the claimed role as credible.

Authority and interaction CIs use the existing 2,000 task-cluster bootstrap;
new language contrasts use 10,000. Intervals are descriptive and unadjusted for
multiple comparisons. Complete matched observations are required for contrasts;
coverage and missing cells are separately reported. All-zero outcomes cannot
establish equivalence, no risk, or a precisely absent interaction. Repeated
samples of 20 tasks are not hundreds of independent task clusters.

A future confirmatory study needs fresh tasks, bilingual review, a fixed analysis
family, a sample-size calculation using task-level variance, and an independently
specified meaningful effect size. The current runs cannot guarantee a positive
authority or language effect.

## Relevant primary research

- Maraia et al., *Sounding vs. Being an Expert*: separates authority credentials
  from linguistic register. https://aclanthology.org/2026.findings-acl.1627/
- Zhang, *Does Safety Reasoning Travel?*: paired multilingual agent evaluation;
  translation pipeline defects can create misleading language conclusions.
  https://aclanthology.org/2026.oracle-main.13/
- Adaption Responses API: https://docs.adaptionlabs.ai/api/resources/responses/methods/create
