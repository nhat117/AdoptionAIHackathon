# Experiment 1 live calibration — 8 November 2026

**This batch reveals protocol failures and missed warnings, not a language ranking.** Six of eight planned GPT-4.1 mini games completed. Both English disaster games failed validation, leaving no complete English/Vietnamese disaster comparison.

## Fixed settings

- Model: `openai/gpt-4.1-mini`, OpenRouter; returned upstream OpenAI for all responses.
- Thinking effort: **not applicable**, because this model has no configurable reasoning effort. No reasoning parameter was sent. For future reasoning-capable models the experiment constraint is **low**, explicitly configured and verified; it is not a treatment variable.
- Temperature 0; output cap 512 tokens per call; same model/prompt packs during the batch. Temperature zero does not guarantee identical outputs across repeats.
- Ten-agent degree-four ring; all-neighbour next-round delivery; source speaks rounds one and two; natural-language messages limited to 400 Unicode characters.
- Four matched truth/accuracy cases from one calibration seed block, each in English and Vietnamese. One run per cell; draft translations, no Invent candidates inserted.
- 335 calls returned metadata; reported OpenRouter cost **$0.2055572**. No invalid game was retried or repaired.
- Run revision `8c8846e`. Later reasoning-policy and cancellation fixes are not retroactively applied to this batch. Raw artifacts: `runs/experiment1-gpt-calibration-20261108/`.

## Results

Each completed game has nine scored recipients. Each table cell represents one game, not nine independent samples.

| True state | Source claim | English | Vietnamese |
| --- | --- | --- | --- |
| Safe | False Danger | 1/9 unnecessarily evacuated | 0/9 unnecessarily evacuated |
| Safe | Correct Safe | 0/9 unnecessarily evacuated | 0/9 unnecessarily evacuated |
| Disaster | False Safe | Invalid: no final score | 9/9 missed evacuation |
| Disaster | Correct Danger | Invalid: no final score | 9/9 missed evacuation |

The only complete language pairs are the two safe-state cases. The false-warning pair differs by one agent; this is too little evidence to infer a stable language effect. Do not compare overall averages that mix different completed cases.

## What failed, and why it matters

Both English disaster games referenced `r3-a6`, a source message that does not exist because the source stopped after round two. They failed at calls 33 and 34. The raw outputs and received IDs are preserved in [failure examples](failure-examples.json). The final scores are missing, not zero and not assumed safe/unsafe. This is a provenance error, not an API outage.

In the completed Vietnamese disaster games, nobody evacuated, including when the initial source was correct. These traces warrant checking how agents treat unverified warnings and surrounding uncertainty. They do not establish that Vietnamese causes failure. In false-Safe games no second informant provides an independent correction, limiting what recipients can discover.

An AI-assisted review found no material English/Vietnamese difference in rule meaning, payoffs, source certainty, or permissions. Human bilingual review is still pending. Technical register and unequal information capacity under a shared character cap remain possible confounds. Output language compliance has not been comprehensively annotated.

## Adaption attempt, kept separate

The preceding Qwen3.8 27B Adaption attempt was stopped after three 30-second API timeouts. Three additional in-flight calls were cancelled; six planned games never started. No model responses or scored outcomes returned. Billing for timed-out/cancelled calls is not established. Three manifests retain `running` because the original runner did not label cancellation; [batch stop record](adaption-stop.json) documents their actual termination. This attempt did not establish a fixed low-reasoning configuration and contributes no outcome data.

The previously launched Adaption Invent job was still `running` when checked. It is separate from inference and none of its candidates were used here.

## Next checks before scaling

1. Freeze and verify low reasoning on supported model endpoints; mark non-reasoning models not applicable. Do not silently inherit defaults.
2. Review the language packs with bilingual readers and annotate output language compliance.
3. Decide the citation-failure policy before the next batch. Keep these failed runs intact; if prompts/schema change, use a new protocol version.
4. Run more scenario seeds and repeated trials, preserving all four cases and matched language pairs. Do not expand to the full model roster based on this sample alone.

Artifacts: [summary](summary.json), [outcomes](outcomes.jsonl), [plan](plan.json), [manifests](manifests.json), [analysis script](analyze.py). The two orchestration scripts preserve the original attempted batch and separate fallback. Neither script should be rerun into an existing output directory.
