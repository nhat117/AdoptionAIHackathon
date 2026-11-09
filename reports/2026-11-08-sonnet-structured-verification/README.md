# Structured-output verification retries — Sonnet 5.5

**Goal achieved for the revised route:** both previously failing Vietnamese cases completed all five rounds with valid outputs and no trace-audit errors. These are separate verification attempts, not replacements for the original failed data.

- Protocol: language-v2, `--structured-output`, schema hash recorded in manifests.
- Same model ID, low reasoning, 2,048-token ceiling, source schedule, scenarios, language packs, and output validator as before; temperature provider-controlled.
- Two games, 90 model calls, **$0.772554** reported usage. Combined with the initial four-game block: six attempts, four completed and two failed, 237 calls, **$1.541326** total reported usage.
- All nine responding agents stayed in both completed retries. This was correct in the safe state and missed evacuation in the disaster state. It is not evidence of a stable language effect.
- Every revised call used upstream provider **Google**. The initial completed block used **Claude Platform on AWS**. Both the output format and the serving route changed, so this cannot isolate the causal effect of structured output. Future comparisons must hold both fixed.

The audit verifies received-message membership, local and next-round delivery, source silence after round two, no calls after evacuation, and unchanged low reasoning/temperature settings. It found zero errors. Human review of output language is still incomplete. JSON shape constraints cannot guarantee that a claim is true or a citation is meaningful.

The revised schema contains provider-supported object types, required fields, enums, and additionalProperties=false. Length and citation-count instructions are descriptions plus runtime checks because the raw API does not support those numeric schema limits. Schema descriptions are English machine-interface text; this is held fixed but should be considered when interpreting whole-game language effects. There are no content repairs and no automatic retries.

All **76 software tests pass**. No full experiment or broader matrix was launched. The next bounded step should verify the same structured protocol and pinned provider on both languages before comparing outcomes, then extend to another model with its own fixed route.

Artifacts: [summary](summary.json), [outcomes](outcomes.jsonl), [plan](plan.json), [manifests](manifests.json), [audit](analyze.py), [runner](run.py). Raw traces remain under `runs/sonnet-structured-verification-20261108/`. The previous failures and their raw outputs remain in [the original report](../2026-11-08-sonnet-verification/README.md). Legacy dataset identifiers contain `calibration`; all runs here are explicitly technical implementation verification.
