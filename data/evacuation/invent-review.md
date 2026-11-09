# Invent v1 candidate review

Adaption Invent generated 12 pairs for 2 estimated credits. The downloaded export
uses `enhanced_prompt` / `enhanced_completion`; the importer explicitly supports
this and the ordinary `completion` schema. Raw generated content is retained.
All 12 pairs pass structural checks (fields, lengths, distinct messages). None is
approved for confirmatory evaluation. Review status remains `pending`.

Preliminary assistant inspection found semantic mismatches requiring human review
or regeneration:

- Rows 0, 1, 3, 5, 7, 8, 9, 10, 11 add urgency, timing, calmness, or stronger action
  language asymmetrically between Safe and Danger. Row 9 also introduces “today”.
- Rows 2 and 6 describe present conditions rather than the future disaster state;
  a currently safe situation does not imply a disaster will not happen later.
- Row 4 changes the requested certainty to an expectation and describes conditions.

These are candidate stimuli, not ground truth, verified quotations, model decisions,
or evidence about cultural or religious effects. Do not train the evaluated agents
on these pairs and then evaluate them on paraphrases from the same family.

One row (index 4) was used only for an offline integration smoke test with explicit
`--allow-unreviewed-stimuli`. It confirmed message attachment and delivery, not
semantic validity or a behavioral result. Use reviewed, matched wording or a new
constrained generation batch before studying natural-language effects. The baseline
structured-signal simulator does not depend on accepting any generated pair.
