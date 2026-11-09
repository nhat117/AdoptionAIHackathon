# Evacuation pilot data

`scenarios.jsonl` contains 40 deterministic simulator configurations: five seeds
per split × two disaster states × two claim-accuracy conditions. Calibration and
evaluation use disjoint seeds. These are parameterized episodes, **not 40 distinct
real-world tasks**, human data, model responses, or evidence of generalization.
The environment is an adaptation of [Shirado et al. (2020)](https://doi.org/10.1098/rspa.2019.0685).

Ground truth, source locations, and terminal round belong to the evaluator.
The runner constructs private local views; it never sends a whole scenario row
to a participant. Source identity claims confer no permissions. The evaluation
split is reserved for later use; only calibration has been exercised.

## Adaption

The raw dataset upload stores scenario configurations and evaluator oracle answers
in Adaption's required prompt/completion format. These are **simulator records,
not participant training examples**. No fine-tuning or AutoScientist job is started.
The executable source of truth remains the versioned local scenario file.

`invent-prompt.txt` instead asks Adaption Invent for paired Safe/Danger message
phrasings. Its generated completions are **candidate stimuli**, never the actions
we expect an evaluated agent to take. Claims can be true or false depending on the
simulator state. Source labels are attached separately so wording stays identical
in attribution comparisons. Review pairs for meaning, tone, length, new evidence,
and extra authority claims before approval. Syntactic checks do not establish
semantic equivalence. Keep paraphrases of one family in the same split.

Invent candidates start with `review_status: pending`. The runner rejects them
for evaluation and requires an explicit flag even for calibration. English is
currently supported. Chinese/Vietnamese require bilingual review and a translated
instruction set; they are not silently treated as equivalent.

Invent v1 completed with 12 rows. See [invent-review.md](invent-review.md) for semantic issues found in preliminary inspection. `stimuli.jsonl` retains all candidates as pending; `invent-raw.jsonl` is the unchanged service export. Structural acceptance does not approve a pair for evaluation.
