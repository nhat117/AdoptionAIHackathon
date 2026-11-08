# Filled submission template

[Track4_Submission.docx](Track4_Submission.docx) uses the supplied Apart Research DOCX template and includes the controlled study, results, architecture diagram, limitations, references, ethics appendix and LLM usage statement.

The eight-page rendering and 196-word abstract were checked. Author names and affiliations remain explicit placeholders; confirm contribution dates and review the report before exporting the final PDF. Nothing has been submitted to the hackathon. The original template and prior research evidence are unchanged.

The revised report uses simpler English, logical transitions and linked author–date citations checked against original arXiv records. Figure 2 presents the existing run outcomes; the original methods diagram and results tables remain. See [citation checks](CITATIONS.md) and [chart data](figures/results-chart-data.csv). References start on page six, and the appendix starts on page seven.

Both report figures are now generated with Matplotlib 3.10.7. Citations and references use APA 7 author–date rules, alphabetical references, sentence case titles, italicized work titles, DOI URLs, hanging indents and double spacing within the reference list. The supplied hackathon template still controls the rest of the document.

The appendix includes six [recorded sample cases](recorded-samples.json), selected from the existing first task across English, Vietnamese and Chinese with and without worker grounding. Original peer messages, worker responses, trial IDs and gate decisions remain inspectable. These examples are not additional trials.

Rebuild figures from the repository root in a Python environment with the figure requirements installed:

```sh
python -m pip install -r submission/figures/requirements.txt
python scripts/plot_submission_figures.py --metrics runs/oversight-ablation-v1/metrics.json --outdir submission/figures
```

The script makes no API calls and checks the plotted counts against the saved metrics.
