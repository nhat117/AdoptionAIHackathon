# Networked evacuation proposals

Two initial proposals adapt the established [Shirado, Crawford and Christakis (2020) evacuation experiment](https://doi.org/10.1098/rspa.2019.0685). They share a simulator foundation but test separate questions. No simulator or experimental results are claimed.

| Study | Question | Draft |
| --- | --- | --- |
| A — Persistent warning | Does repeated warning reduce chosen communication access, with consequences for evacuation? | [PDF](persistent-dissenter/main.pdf) · [LaTeX](persistent-dissenter/main.tex) |
| C — Network recovery | After false reassurance spreads, which correction policy restores appropriate action? | [PDF](network-recovery/main.pdf) · [LaTeX](network-recovery/main.tex) |

The original task supplies local signals, an informed participant, costly evacuation, and a hidden disaster state. Synchronous rounds, chosen reception, controlled false claims, and recovery interventions are proposed adaptations. The papers distinguish original procedures from these changes. The removed rule-breaking-leader project remains removed.

Start implementation with the common game engine, deterministic payoff and delivery checks, then an all-informed/no-communication comprehension pilot. Implement A and C as separate experiment configurations. Freeze sampling and evaluation choices after calibration before collecting held-out results. Do not expand language, authority, topology, and model factors simultaneously.

Compile each directory with `tectonic main.tex` (or `pdflatex main.tex` twice). Before submission, review the methods, supply actual authorship, conduct experiments, and check the current official template and disclosure requirements.

[Source verification](source-verification.md) records evidence scope. The [earlier research investigation](research-directions.md) is retained as background, not the current experimental specification.
