# Networked evacuation proposals

Two initial proposals adapt the established [Shirado, Crawford and Christakis (2020) evacuation experiment](https://doi.org/10.1098/rspa.2019.0685). They share a simulator foundation but test separate questions. No simulator or experimental results are claimed.

| Study | Question | Draft |
| --- | --- | --- |
| A — Persistent warning | How does repeated disagreement affect who agents listen to and whether they act correctly? | [PDF](persistent-dissenter/main.pdf) · [LaTeX](persistent-dissenter/main.tex) |
| C — Network recovery | How does a network recover after incorrect information spreads, and which interventions improve recovery? | [PDF](network-recovery/main.pdf) · [LaTeX](network-recovery/main.tex) |

The original task supplies local signals, an informed participant, costly evacuation, and a hidden disaster state. Synchronous rounds, chosen reception, controlled false claims, and recovery interventions are proposed adaptations. The papers distinguish original procedures from these changes. The removed rule-breaking-leader project remains removed.

Start implementation with the common game engine, deterministic payoff and delivery checks, then an all-informed/no-communication comprehension pilot. Implement A and C as separate experiment configurations. Freeze sampling and evaluation choices after calibration before collecting held-out results. Do not expand language, authority, topology, and model factors simultaneously.

Compile each directory with `tectonic main.tex` (or `pdflatex main.tex` twice). Before submission, review the methods, supply actual authorship, conduct experiments, and check the current official template and disclosure requirements.

[Source verification](source-verification.md) records evidence scope. The [earlier research investigation](research-directions.md) is retained as background, not the current experimental specification.

## General question and experimental factors

How do a message’s source, repetition, and supporting evidence affect its spread and influence on collective decisions? Both papers now separate fixed settings, primary interventions, balanced controls, optional extensions, and settings awaiting calibration.

The initial pilot holds the network, incentives, evidence access, language (English), and one selected model constant. A varies repetition and reception policy; C varies recovery policy. Both evaluate correct/incorrect information and disaster/no-disaster outcomes. Claimed source (ordinary peer, emergency expert, political or religious authority), English/Chinese/Vietnamese, and models from different developers are staged extension factors. Specific figures are optional conditions, not the research question. Evidence-quality manipulations and mixed-model networks require separate designs. No full factorial sweep is committed.
