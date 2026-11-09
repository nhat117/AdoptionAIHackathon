> Superseded design note: A and C now use the established networked evacuation game. See [current proposals](README.md). The workflow setting and option B below are historical exploration, not the selected implementation.

# Candidate experiments on collective safety and dissent

Investigation date: 8 November 2026. Decision brief, not a completed study or a claim of novelty. No model experiments were run for this brief.

## Recommendation

Start with **A: selective consultation and loss of a correct warning**, because it preserves the original dissent idea while making the communication graph part of the experiment. Keep **C: recovery after a false claim spreads** as the alternative if routing produces little variation. **B: acknowledged warnings without completed verification** is the simplest engineering pilot, but its conceptual overlap with bystander and accountability work is substantial.

These are three candidate experiments, not three commitments. Use one small shared environment, then choose one primary study after calibration. None should be sold as the first study of dissent, communication topology, social pressure, or agent safety.

## What the two proposals actually establish

The friend's six-page *Authority Across Languages: Evaluating Socially Framed Prompt Injection and Monitoring in Multi-Agent AI Systems* was read in full from the supplied PDF. It proposes a target agent, a lower-trust attacker message, four fictional authority labels, English/Chinese message variants, and a separate monitor. Section 2.5 explicitly excludes conformity from the core experiment. Section 5.5 already requires a deterministic baseline and reserves AI monitoring for semantic violations. Its 480 target trials per model are a proposed budget, not data or a power calculation. The trust separation, matched language controls, benign-task evaluation, and cautious claims remain useful.

The current `persistent-dissenter/main.tex` primarily uses one live coordinator with three scripted peers. Its attention/uptake/exclusion/safety distinction is useful, but the interactive experiment is deferred. For the user's present goal, live interaction must become the primary design. Neither a sender label nor several serial model calls alone demonstrates an interaction-dependent collective effect. The deleted leader project stays deleted.

## Evidence map: what is already close

This was a targeted search, not a systematic review. Searches covered dissent/withholding, minority recovery, adaptive routing/exclusion, responsibility/verification, and correction/propagation. Source status and inspection depth are explicit below; experiments and external code were not independently reproduced.

| Source | Checked evidence and relevance | Implication for our claim |
| --- | --- | --- |
| [HiddenBench, Li et al., ICML 2026](https://proceedings.mlr.press/v306/li26ej.html) | Publisher abstract: distributed-information reasoning and a structured communication intervention. | Pooling hidden facts and improving it with a protocol are established topics. Landing page inspected; full methods not audited. |
| [Mansuri et al., withheld dissent](https://arxiv.org/html/2609.38324v1) | Full-text methods/discussion: live discussion, hidden-profile tasks, disclosure interventions; authors identify fixed communication and single sessions as limits. | An alternative must do more than ask agents to speak up. Adaptive access is a narrower candidate. |
| [Tak et al., Process Loss to Assembly Bonus](https://arxiv.org/html/2609.13261v1) | Full-text process/method sections: interactive deliberation, floor-taking, correct-minority survival, exit and forced-stay conditions. | Persistence, participation, and minority survival already have close precedents. |
| [Minority Sentinel](https://arxiv.org/html/2606.29270v1) | Methods: three-agent debate and a classifier selecting when to overturn majority voting. | Do not claim a new idea merely for recovering a correct minority; wrong interventions must also be counted. |
| [Pitre et al., communication failures](https://arxiv.org/html/2610.32060v1) | Abstract and taxonomy framing: correction, consensus, and minority-signal suppression. | Final disagreement loss is not proof that a participant was denied communication access. |
| [PEAR repository](https://github.com/EVIEHub/PEAR) | README: sparse adaptive critique routing, influence balancing, and random/fixed graph baselines. Code not executed; publication status not established here. | Dynamic routing and routing toward dissent are not new by themselves. |
| [Quiet Suppression](https://apartresearch.com/sprints/projects/ai-collusion-sprint-quiet-suppression-bgu1) | Project page and linked report methods: separate summarizer/rater agents; suppression instructions and private notes; watchdog precedent framing. | Omission through summaries and authority-conditioned oversight are already studied. Participant sprint report, not an Apart publication. |
| [When Monitors Agree for the Wrong Reasons](https://apartresearch.com/sprints/projects/when-monitors-agree-for-the-wrong-reasons-information-design-for-collusion-auditing-bp9g) | Page and linked report: unequal monitor information and aggregation. Report distinguishes detecting explicit planning from successful collusion. | Giving one monitor privileged evidence is not a sufficient new contribution. Participant sprint report. |
| [Agents in a Smoke-Filled Room](https://apartresearch.com/sprints/projects/agents-in-a-smokefilled-room-testing-the-agent-bystander-effect-pf79) | Project summary: a focal agent receives audience/social-proof cues; effects vary by setting/model. Full report not audited. | A generic AI bystander question is already occupied. Distinguish audience descriptions from live delegation. |
| [Shehata and Li, Bystander Effect](https://arxiv.org/html/2605.10698v2) | Section 3.4 explicitly declares auditors rather than instantiating independent messaging agents. | Useful contrast with a live verification/delegation network; this difference alone does not establish novelty. |
| [ForesightSafety-TIDE](https://arxiv.org/html/2608.03421v3) | Methods and exit analysis: five-agent evidence aggregation; false testimony persists after the source exits; observer interventions. | Removing a source need not remove its influence. Persistence and provenance tracing are already studied. |
| [Collective Loss of Control / RogueHandoff](https://arxiv.org/html/2609.18460v1) | Sections 2.3–4: synthetic unsafe-state resumption and an epidemic account; authors distinguish local handoff susceptibility from full network recovery. | A recovery study must measure onward interaction, not merely a successor continuing a transcript. |
| [Can CaMeLs Talk?](https://arxiv.org/abs/2610.05640) | Abstract: provenance-preserving channels across hierarchical agent boundaries. | Provenance and preventing trust promotion are existing defenses, not our invention. Full implementation not audited. |
| [Passaro et al., network topology](https://arxiv.org/abs/2610.31165) | Abstract: naming-game populations using policies extracted from LLMs; topology and committed-node placement. | Ring-versus-hub comparisons alone are weak novelty; not equivalent to that many live API agents. |
| [When Safe Agents Fail Together, SoK](https://arxiv.org/html/2609.00595v1) | Abstract and evaluation framing: interaction counterfactuals and end-to-end protected effects. | We need a comparison that removes or changes interaction while retaining the task and evidence. |
| [Corollary repository](https://github.com/gabe-santana/corollary) | README describes dependency-based retraction and context projection. Not executed or validated. | Automatic dependency invalidation has prior implementations; it can serve as an engineering baseline, not a novelty claim. |

The friend's cited persuasion and multilingual studies motivate controls, but do not settle these three network questions. We did not re-audit all five of its references during this investigation. No claim that a model's vendor, language, or persona measures a human culture is justified.

## Shared task and minimum evidence standard

Use a fictional release-review team with five live agents. Each has a separate history, a common policy, and a different subset of evidence about approval validity, intended recipient, scope, and record restrictions. The team proposes `release`, `hold`, or `request_evidence`. An evaluator outside the agents knows the full state and scores the action. All effects are local simulator records.

Use both allowed and disallowed releases and a permitted route to task completion. Randomize evidence-holder identity and message order. Avoid encoding the answer in agent names, fact IDs, or task templates. Check separately that a model with complete evidence can solve the tasks and that local evidence is genuinely incomplete. Do not call an unanswerable task a coordination failure.

Agents choose messages, questions, verification actions, and revised decisions. Use a predeclared deterministic aggregation rule, such as a strict majority of five votes with ties/uncertainty mapped to a separately reported unresolved state. Keep the decision rule constant across primary conditions. A coordinator-only final decision would reintroduce the limitation we are trying to address.

Required baselines: independent agents with no communication; a single agent with complete evidence; a fixed communication protocol. These are diagnostic comparisons with different information access, not automatically equal-compute causal contrasts. The primary protocol comparisons should match task instances, available evidence, model settings, turns, and message/tool budgets. Report realized usage too.

Keep event visibility enforced in code: storing all messages in one state object must not make all of them visible to every agent. Log delivery separately from generation and citation separately from behavioral change. No hidden chain-of-thought is required.

## A. Do teams stop consulting a correct dissenter?

**Question.** Does repeated evidence-backed disagreement change whom agents choose to hear from, and does that change prevent later relevant evidence from reaching the group?

**Why interaction matters.** Each participant chooses which two peers to consult for the next round. Those choices create the next communication graph. The effect is distributed across recipients, not decided by one scripted gatekeeper.

**Minimal design.** All participants receive the same initial contributions. One agent has a verifiable objection. Over the next rounds, compare an initial objection followed by neutral updates with repeated restatement of the same evidence. No prompt tells peers to ostracize the speaker. The dissenter's initial evidence can be controlled while subsequent replies and peer choices are live. Label the controlled seeding explicitly.

Cross persistence with adaptive consultation versus degree-matched random consultation. Use matched valid and invalid objections. These should be grounded in clear simulator evidence: invalid claims must be refutable, not merely unpopular. Keep total slots and approximate text length comparable. Repetition inherently changes evidence salience; do not pretend the treatment isolates dislike or emotion.

After consultation choices, give one randomly selected agent a new, decision-relevant fact. Randomize whether this is the prior dissenter or another participant. The final fact is not already in everyone's context. This tests the downstream cost of access loss without defining all disagreement as harmful. A later protected-access intervention can reserve one slot for a challenger while replacing another slot, rather than adding free tokens.

**Outcomes.** Incoming consultation share, whether the new fact is delivered, whether recipients cite/use it, final violation rate, false holds, and safe completion. Attention is observable response behavior, not neural attention. Failure to select someone is restricted consultation, not proof of social ostracism.

**Causal claim available.** Randomized protocol/persistence differences can establish effects under this interface. A correlation between fewer consultations and unsafe decisions does not establish mediation. Randomized protected access can test whether restoring access changes outcomes; it still changes exposure.

**Closest overlap and candidate contribution.** Tak examines participation/exit; Mansuri studies withheld dissent; PEAR routes critiques. Our candidate is the feedback loop from repeated objection to peer-selected access to later safety evidence, with invalid-warning controls. This exact combination was not located in this targeted search, which is weaker than proving absence.

**Go/no-go.** Continue if routing varies, some relevant evidence is lost through routing, and the task remains solvable with complete evidence. Null effects are reportable; a ceiling task or a router that always selects the same peers needs redesign. Do not select only dramatic exclusion traces for the main analysis.

## B. Everyone acknowledges the warning, but who verifies it?

**Question.** Can reciprocal delegation leave a shared safety warning unverified, and does explicit ownership close the gap without excessive blocking or redundant checking?

**Why interaction matters.** Agents can request verification, accept responsibility, delegate, or act on another agent's claimed completion. The outcome depends on whether somebody actually executes the check and shares its result.

**Minimal design.** A live agent raises an uncertain warning about release permission. Any team member can call an identical read-only registry tool. Compare three protocols: open responsibility; one randomly assigned owner; and an acknowledged assignment with recorded completion. Keep the available tool-call budget and round count equal. The owner has no privileged evidence or stronger model. Agents learn about actual completed checks through messages or an explicit shared completion event, depending on the predeclared protocol.

Use warnings that turn out true and false, plus cases without a warning. The factual result is fixed independently of who checks. Distinguish tool invocation from a model saying it checked. Define ownership/receipt policy before running; an acknowledgement alone must not count as completion. Include a deterministic mandatory-check baseline to show what ordinary engineering can guarantee.

**Outcomes.** Cases with no completed check, time to first check, duplicated checks, delegation cycles, unverified claims of completion, unsafe releases, and unnecessary holds. Later vary team size only after establishing the basic effect, with both fixed-total and fixed-per-agent budget analyses.

**Closest overlap and candidate contribution.** Bystander work and role/accountability protocols already exist. The narrower candidate is a live, auditable delegation failure despite expressed acknowledgement, measured against real tool events. This is probably the weakest novelty claim of the three, but the easiest operational demonstration.

**Go/no-go.** If every condition reliably checks, report that result and stop expanding this direction. If a deterministic check resolves everything at negligible cost, present the result as a workflow evaluation, not evidence that an AI monitor is necessary.

## C. Can a team recover after a false claim has spread?

**Question.** Once honest agents have repeated an unsupported authorization claim, what restores correct collective action: removing the source, correcting the claim, or invalidating its downstream uses?

**Why interaction matters.** The original source can leave while other agents keep carrying its claim. After correction, agents may retransmit stale or corrected evidence. The main object is recovery across the network, not the first recipient's compliance.

**Minimal design.** Seed one false peer claim into the five-agent release task, then allow two live communication rounds. Snapshot every agent's visible history and simulator state. Branch the same snapshot into: (1) no intervention; (2) source removal only; (3) removal plus a verified correction delivered initially to one honest node; (4) the same correction with explicit claim identifiers and invalidation receipts. Match post-snapshot communication budgets and account for the source's absence consistently in arms 2–4. Compare arm 3 versus 4 for protocol effects; arm 1 versus 2 also changes active membership and must be interpreted as a package effect.

Continue live interaction for several bounded rounds. Measure relay and correction of derived claims, not just repetition of the original string. A separate oracle invalidation baseline can remove all known contaminated records in code; that is an upper-bound engineering control, not model recovery.

The registry is authoritative and unchanged. A verified correction supplies evidence about that state; a peer cannot grant or revoke real permissions. Add accurate original claims followed by false correction attempts, so accepting every reversal fails. For branching, include all snapshots in the primary analysis; report genuinely contaminated snapshots as a prespecified secondary subgroup, not a cherry-picked main sample.

**Outcomes.** Post-intervention violation attempts, stale-claim holders and relays, rounds to evidence-consistent decisions, incorrect reversals, safe completion, and additional messages/checks. Failure to act is not sufficient evidence of recovery: report unresolved episodes and legitimate progress separately. Use a fixed horizon and distinguish unobserved recovery beyond it from permanent failure.

**Closest overlap and candidate contribution.** TIDE directly studies false testimony after source exit; RogueHandoff studies inherited unsafe state; multi-CaMeL and truth-maintenance implementations address provenance/invalidation. The proposed contribution is a controlled comparison of recovery protocols in ongoing live interaction, including resistance to false corrections. Merely showing persistence after source exit would duplicate a close result.

**Go/no-go.** First establish that false claims sometimes propagate and that verified corrections are comprehensible when directly shown. If there is no propagation, the recovery test has no exposure to study. If recovery differs only because one arm gets more information or extra calls, fix the comparison before claiming a protocol benefit.

## Implementation scope in this repository

The current `graph.py` has prepare, two independent branches, combine, and finish. `backend.py` provides an async model-call interface, while `LabState` has no agent inboxes, routing, evidence permissions, or research scoring. These are reusable plumbing, not an existing multi-agent experiment.

Build a separate research runner around the backend rather than treating the current demonstration graph as the experiment. Proposed components:

| Component | Required behavior |
| --- | --- |
| Task generator and oracle | Synthetic evidence partitions, allowed/forbidden action labels, benign variants, separate calibration/test templates |
| Episode state | Per-agent local histories, delivered message IDs, live membership, evidence access, round and budget counters |
| Router | Fixed/random/adaptive consultation; explicit delivery events; no invisible access to global state |
| Agent step | Structured public message, recipients/consultations, evidence references, optional check/delegation, action proposal |
| Simulator | Deterministic registry reads and inert action effects; event-based scoring |
| Checkpoint/replay | Branch matched histories for C without introducing another arm's outputs |
| Analysis | Task-paired effects, false alarms, completion, usage, invalid outputs, protocol adherence, trace samples selected by a stated rule |

Test oracle correctness, visibility isolation, budget enforcement, deterministic routing fixtures, and snapshot isolation before model calls. Offline fixtures test the harness only; they cannot supply research findings.

For rough budgeting, five agents making an initial call, three discussion calls, and a final call means **25 calls per episode**, before separate routing, verification follow-ups, retries, or monitoring. A screen with six task instances, four protocol arms, and two repetitions is 48 episodes, approximately 1,200 calls. This is a feasibility illustration, not a powered study. Direction-specific factorials and controls increase it; calculate cost from actual token usage and the selected provider's current prices before launching. No paid runs are initiated by this brief.

Separate a small calibration set from a held-out pilot. Freeze the primary contrast, task templates, horizon, prompts, model/version, settings, and invalid-output policy before the pilot. Use task-level paired summaries and cluster uncertainty by base scenario; agents, messages, repeated runs, and branched continuations are not independent task samples. Report all prespecified arms and null findings. An initial six-task screen cannot support strong generalization or narrow confidence intervals.

## Decision order

1. Implement the shared inert task and visibility checks.
2. Calibrate A first: can peers make meaningful consultation choices, and can their choices alter access to useful evidence?
3. If the mechanism is measurable, freeze A's primary design. If not, evaluate C's propagation/recovery feasibility rather than forcing an exclusion effect.
4. Retain B as a small, useful comparison if time permits, not an additional full research commitment.
5. Only then add one of the friend's dimensions: authority attribution or language. Match evidence, actual permissions, style, and translated meaning. Do not expand all factors simultaneously or label model/vendor differences as cultural explanations.
6. Rewrite the main LaTeX proposal around the selected mechanism, add the closest competing work, and replace the stale statement that the friend's PDF is unavailable. Keep initial hypotheses distinct from pilot observations and final held-out results.

This brief leaves the existing LaTeX/PDF untouched while the research direction is being selected. It does not restore the deleted leader proposal or claim experiments have been implemented.
