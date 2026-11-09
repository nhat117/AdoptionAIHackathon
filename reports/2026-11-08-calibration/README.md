# Evacuation calibration results — 8 November 2026

**Scope:** one model (`openai/gpt-4.1-mini`) through OpenRouter, temperature 0, English, ordinary-peer source labels, structured signals. No Invent-generated text was used. These are descriptive calibration results, not confirmatory findings or a cross-model comparison.

- Planned: 80 study-A episodes and 50 study-C continuations across five simulator seeds.
- Completed: 129 outcomes (79 A, 50 C); one A trial failed validation.
- Provider calls: 4,015; reported usage cost: **$1.172298**. Returned upstream provider: OpenAI.
- Run revision: `8463b89`; all scenario runs started with a clean working tree. Raw views, messages, and fork snapshots are retained locally under `runs/evacuation-calibration-batch-20261108/`.
- The $2 reported-cost stop and 20-minute time limit were not reached. No failed trial was retried or repaired.

## Study C: correction was more useful than removal in this sample

Rates below are episode means over nine non-source agents. Each cell contains five scenarios; the five intervention arms share an identical two-round exposure snapshot within each scenario. Lower is better for both columns.

| Recovery policy | Missed evacuation when disaster occurs | Unnecessary evacuation when no disaster occurs |
| --- | ---: | ---: |
| No intervention | 42.2% | 53.3% |
| Remove source | 40.0% | 51.1% |
| Remove + local factual correction | 0.0% | 40.0% |
| Remove + local correction linked to claims | 0.0% | 40.0% |
| Remove + correction to all agents | 0.0% | 26.7% |

Removing the source improved correct action by 2.2 percentage points relative to no intervention in each disaster-state subset. Adding a local factual correction improved correct action by 40.0 points in disaster episodes and 11.1 points in safe episodes relative to removal alone. Explicit claim links produced no additional endpoint improvement over the same local correction. These are paired descriptive differences, not significance claims.

In safe episodes, 26.7% of non-source agents had already evacuated at the shared intervention snapshot. Since evacuation is irreversible, these false alarms cannot be undone. Broadcast correction ended at that same 26.7% false-alarm rate, while local correction ended at 40.0%. The broader reach of broadcast correction is an intended information-access advantage, not a budget-matched comparison.

## Study A: repetition effects were small and mixed

Each complete cell has five scenarios. Rates again exclude the controlled source. Accurate/incorrect labels describe the controlled peer claim, not the environmental truth.

| Message / reception | Missed: accurate claim | Missed: incorrect claim | False alarm: accurate claim | False alarm: incorrect claim |
| --- | ---: | ---: | ---: | ---: |
| once / fixed | 51.1% | 100.0% | 0.0% | 44.4% |
| repeated / fixed | 53.3% | 100.0% | 0.0% | 53.3% |
| once / chosen | 53.3% | 100.0% | 0.0% | 55.6% |
| repeated / chosen | 46.7% | 100.0% (n=4) | 0.0% | 51.1% |

For accurate danger warnings with chosen reception, the source-selection rate averaged 55.2% under both once-only and repeated warnings. Missed evacuation decreased from 53.3% to 46.7%, while fixed reception changed from 51.1% to 53.3%. This batch does not show a consistent harmful effect of repetition or a clear exclusion effect. Selection-rate denominators depend on source availability; they are not measures of internal attention or dislike.

In A, the controlled source is the sole holder of verified truth. When it sends false reassurance during disaster, uninformed recipients have no independent truthful informant; all completed such trials ended with 100% missed evacuation among those recipients. C has a separate truthful informant. Therefore A and C endpoint rates are not directly comparable as measures of model ability.

## Validation failure and missing data

`A-calibration-004-1-0`, `repeated_chosen`, failed at round 4: agent 7 referenced `r3-a6`, which was not in its received message history. Strict provenance validation rejected the action. The preceding three arms completed and are retained. The failed arm has no scored outcome and is not imputed as safe, unsafe, or a zero. A paired contrasts use only matched completed arms (nine instead of ten pairs for the disaster-state chosen-reception contrast averaged across accuracy conditions).

## Interpretation and next experiment

1. C is the clearer next calibration direction: compare correction reach and timing, preserving shared exposure and measuring decisions already irreversible before intervention.
2. Add the planned honest-source, sham-removal, all-informed, and no-communication references before making causal claims beyond the implemented comparisons.
3. For A, check whether genuine disagreement and meaningful consultation choices occur before treating repeated messages as a persistent-dissent manipulation.
4. Use additional independent seeds and repeated model runs, randomize treatment execution order, then freeze a held-out evaluation protocol. The present five seeds are parameter variations in one game, not five independent real-world task families.
5. Religious/political identity, other languages, other model families, and mixed-model networks were not tested. The results support no cultural, religious, or national-origin conclusions.

No uncertainty intervals or p-values are reported: this is a small, single-model calibration batch with dependent agent observations, shared C forks, and one invalid trial. No model prompt, parser, or game rule was changed during the batch.

## Artifacts

- [Completed outcomes](outcomes.jsonl)
- [Cell summaries and paired comparisons](summary.json)
- [Batch plan and cost](plan.json)
- [Scenario execution status](jobs.json)
- [Implementation and commands](../../projects/implementation.md)

The archived `run_batch.py` and `analyze_batch.py` are the exact orchestration scripts used. Run from the repository root; choose a new output directory before rerunning the launcher, which refuses to overwrite the existing batch.
