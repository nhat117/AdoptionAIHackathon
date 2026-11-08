# Initial research proposals

These are two independent, AI-assisted initial proposals, not completed studies. No experiments, findings, author identities, affiliations, or novelty claims are asserted. The existing repository scaffold is not an implementation of either protocol.

| Project | Research question | Draft |
| --- | --- | --- |
| Heard but Overruled? | Does false peer authority change attention to, uptake of, or exclusion of persistent correct safety dissent? | [LaTeX](persistent-dissenter/main.tex) · [PDF](persistent-dissenter/main.pdf) |
| Following the Rule-Breaker | Does observing unauthorized behavior cause copying without an instruction, and do prestige and actual role authority modify it? | [LaTeX](rule-breaking-leader/main.tex) · [PDF](rule-breaking-leader/main.pdf) |

Each directory is a standalone LaTeX project with an inline bibliography. Compile from the directory using `pdflatex main.tex` twice, or `tectonic main.tex`. No external bibliography processor is needed. PDFs, when generated, are review copies rather than submission-ready reports.

Both drafts connect narrowly to [Swarm Alignment Track 2: The Science of Agent Networks](https://apartresearch.com/sprints/swarm-alignment-2026). The controlled pilots do not establish emergent leadership or large-network behavior. The second proposal reserves propagation claims for a distinct interactive chain experiment.

Before implementation, decide model/provider/version, sampling settings, task bank, calibration split, sample size, stopping rules, annotation rubric, and available budget. The numerical pilot sizes are tentative budget illustrations, not power analyses. Freeze these choices before evaluation. Optional safeguards, second-model replications, and Chinese/Vietnamese extensions should not displace the core contrasts. Translation requires bilingual validation; no cultural conclusions are proposed.

Before submission, the team must substantively review and revise the drafts, supply real author details, conduct/report any experiments, and transfer the approved text into the current official template if required. The current event page states an eight-page cap excluding references and appendices, a 150–250-word abstract, and a required limitations/dual-use appendix. The supplied generic Google template's four-page recommendation is not the event's cap. Check the latest Guidelines tab at submission time.

See [source-verification.md](source-verification.md) for evidence scope and unresolved provenance. No work has been submitted to the event.

Validation: both PDFs compiled with Tectonic 0.17.0 without TeX warnings. Citation keys are complete; abstracts contain 169 and 178 words respectively. Repository lint and all 14 existing tests passed. No research experiments were run.
