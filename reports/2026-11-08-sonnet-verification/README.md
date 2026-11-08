# Second-model technical implementation verification — Sonnet 5.5

Goal: test the same four-game setup used with Terra on a second model, keeping language, scenarios, source schedule, reasoning effort, and output ceiling fixed within the block.

## Initial block: language-v1

Two English games completed; both Vietnamese games failed output validation. Total: 147 calls and $0.768772 reported usage. No automatic retries or response repairs occurred.

| Case | English | Vietnamese |
| --- | --- | --- |
| Safe state, false Danger claim | All 9 recipients stayed | Failed at call 33: two JSON objects with intervening self-correction prose |
| Disaster, true Danger claim | All 9 recipients stayed; all missed evacuation | Failed at call 24: unexpected action_note field |

The completed English games used the same upstream provider, Claude Platform on AWS. These results are too small and incomplete for a model or language ranking. In both true states, the agents see the same unverified Danger claim; the true state changes scoring but does not provide independent recipient evidence. Staying in one and evacuating in another cannot be interpreted as reliable truth discrimination.

## Concrete implementation change

Prompt-only formatting proved insufficient. An optional `--structured-output` flag now requests an API-enforced JSON object with exactly signal, action, message, and parents. This is protocol `language-v2`; default language-v1 is unchanged. The raw schema uses supported types/enums, required keys and additionalProperties=false. String lengths and array limits remain checked by the existing validator because [Claude does not support those raw schema constraints](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).

This change can affect responses and prompts internally. We preserve the original failures and report new verification runs separately. The two Vietnamese retries are in [the structured-verification report](../2026-11-08-sonnet-structured-verification/README.md). Do not pool v1 English with v2 Vietnamese to estimate a language effect. Comparable experimental results require the same protocol revision for every cell.

Artifacts: [summary including failed raw responses](summary.json), [completed outcomes](outcomes.jsonl), [plan](plan.json), [manifests](manifests.json), [trace audit](analyze.py). Full raw logs remain in `runs/sonnet-verification-20261108/`. This is technical implementation verification, not a completed research experiment.
