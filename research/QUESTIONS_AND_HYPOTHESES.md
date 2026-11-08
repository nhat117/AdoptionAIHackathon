# Research questions and hypotheses

These statements organise the **completed controlled pilot**. They were written after inspecting the results and are not preregistered predictions. The original frozen protocol and all prior evidence remain unchanged. They correspond to questions 2 and 3 of the consolidated proposal; the earlier propagation question remains part of the foundation.

## Objective

Test whether checking an agent report against controller-owned facts stops wrong budgets, while separating this effect from formatting rejection and worker access to trusted input. The comparator enforces structural rules; it is not an agent without any constraints.

## RQ1 and H1

**RQ1:** When the worker lacks trusted facts, does adding a fact check reduce wrong-budget releases while preserving correct reports?

**H1:** Wrong-budget releases will be lower with the fact check, without additional rejection of correct reports.

**Comparison:** Apply structural and semantic checks to exactly the same twelve evidence-absent responses after identical parsing. Both controller arms have the same record. Accepted candidates remain unchanged; no recovery contributes.

**Observed answer:** Wrong releases are 6 versus 0; correct releases are 6 versus 6. H1 is descriptively supported within this pilot. Six reports are blocked, not repaired.

## RQ2 and H2

**RQ2:** Does the fact check add protection when the worker already receives trusted facts?

**H2:** Adding the fact check will lower wrong-budget releases beyond trusted input alone.

**Comparison:** Apply the same two checks to the twelve evidence-present responses. Worker prompts otherwise match the evidence-absent condition.

**Observed answer:** Both checks release 0 wrong and 12 correct reports. An added benefit is not demonstrated. No observed baseline errors remain to contain; the result does not establish equivalence or prove that grounding always suffices.

## Exploratory RQ3

Does the pattern appear in English, Vietnamese and Chinese peer messages? Each language has four responses per evidence condition: two tasks crossed with clean and poisoned sources. Without grounding, wrong releases are 2/4 for structural checking and 0/4 with fact checking in every language. With grounding both are 0/4. These repeated tasks cannot establish causal language effects or broad multilingual robustness.

## Variables and measurements

- Manipulated variables: worker record absent/present, structural/fact check, strict/shared parsing. Peer language and clean/poisoned source conditions reuse two task groups.
- Fixed controls: model, system prompt, metadata and peer text within evidence pairs; controller record and candidate within each gate comparison.
- Outcomes: wrong releases, correct releases, blocked incorrect reports, false rejection of correct reports and unscored errors.
- Data: 24 recorded responses, one worker model, two task groups. No new inference for this clarification.
- Formatting diagnostic: separately replay 12 archived fenced responses. Strict parsing blocks all 6 correct reports; shared cleaning plus fact checks retains all 6 and blocks all 6 wrong reports.

Counts are descriptive. Gate decisions reuse candidates, and language conditions reuse tasks. We do not report IID confidence intervals, p-values or a general safety guarantee. See the [saved protocol](../runs/oversight-ablation-v1/FROZEN_PROTOCOL.json), [controlled report](OVERSIGHT_ABLATION_RESULTS.md), [filled Word report](../submission/Track4_Submission.docx) and [chart source data](../submission/figures/provenance.json).
