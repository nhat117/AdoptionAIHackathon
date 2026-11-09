# Preserved pilot submission report

The current 600-response expansion has a [separate report and Word file](expansion-v2/README.md). This page describes the preserved 24-response pilot.

[Track4_Submission.docx](Track4_Submission.docx) uses the supplied Apart Research template. It contains the objective, explicit research questions and hypotheses, methods, actual results, hypothesis outcomes, limitations, APA 7 references and recorded examples.

The final rendering is eleven pages, including references and appendices; references start on page seven. The abstract is 196 words. All pages were checked visually. Author names and affiliations remain explicit placeholders. Confirm contribution dates, review the report and export the final PDF before upload. Nothing has been submitted to the hackathon.

## Questions and evidence

[Questions, hypotheses and observed answers](../research/QUESTIONS_AND_HYPOTHESES.md) define the comparisons, variables and measures. H1 is supported descriptively in this pilot: adding fact checks blocks six wrong budgets without losing the six correct reports. H2 is not demonstrated: trusted input already produces twelve correct reports. Language is exploratory. These hypotheses organise completed results and are not preregistered predictions.

## Readable Matplotlib figures

Five figures comprise a methods diagram, outcome bars, a language heatmap, worker-error bars and an archived-formatting bar comparison. All chart axes show counts and denominators. Formatting and worker-error views use grouped bars rather than scatter or paired-point charts. The charts reuse saved trials and do not add independent observations.

## Dataset locations

[Dataset index](../data/README.md) lists the exact current input and output files and the separate earlier 600-case dataset. The controlled study uses 24 responses, not 600.

## Actual sample outputs

The report includes the six-language/grounding examples for the first task and clean, poisoned and grounded outputs from the second task. The [24 recorded outputs in JSON](figures/all-recorded-outputs.json) contain expected facts, peer reports, exact parsed model objects, trial IDs and gate decisions. The [flat CSV](figures/all-recorded-outputs.csv) supports quick inspection. These are existing synthetic-task records, not newly generated demonstration outputs.

## Reproduction

```sh
python -m pip install -r submission/figures/requirements.txt
python scripts/plot_submission_figures.py --metrics runs/oversight-ablation-v1/metrics.json --outdir submission/figures
```

Matplotlib 3.10.7 generates all figures. The script checks plotted counts, exports sample outputs, records source hashes and makes no API calls. The original run evidence is unchanged. See [citation checks](CITATIONS.md), [figure provenance](figures/provenance.json) and the [consolidated proposal](../research/RESEARCH_PROPOSAL.md).
