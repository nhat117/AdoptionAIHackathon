# When Does Semantic Oversight Add Value?

A controlled multilingual agent-handoff study for **Track 4: Multi-Agent Oversight and Control**.

**Authors and affiliations: to be completed by the team.** This is a submission draft, not a submitted or template-formatted final PDF.

## Abstract

Multi-agent workflows can pass source errors downstream, but apparent protection from a guard can be confounded by formatting rejection, trusted information access, prompt strength, and recovery. We refine a multilingual reporting testbed to separate these mechanisms. A prior two-hop pilot seeded incorrect budgets in peer reports across English, Vietnamese, and Chinese; its live guard rejected Markdown-wrapped JSON before performing semantic checks. We preserve that evidence and add a controlled follow-up of 24 fresh worker responses on the same two task clusters. Both evidence conditions use identical prompts except for a trusted-record field. Every response is evaluated by four same-candidate checks crossing strict versus shared JSON normalization with structural versus trusted-fact verification. Accepted candidates are unchanged; no recovery or trusted rendering contributes to the primary comparison. All 24 fresh responses satisfy the strict structural contract. Without worker access to the trusted record, structural checks release six incorrect budgets, while semantic checks block those six and retain all six clean reports. With trusted input, both checks release twelve correct reports. Thus registry-backed semantic verification adds a bounded rejection capability independent of formatting, but this pilot shows no incremental benefit over input grounding. Results concern two synthetic task clusters, not general swarm alignment, language effects, collusion detection, or hidden-bias containment.

## 1. Question and contribution

Can a controller's comparison against known facts prevent an incorrect peer budget from being released after formatting, prompt wording and worker evidence are controlled? The contribution is an inspectable ablation of a small oversight boundary, not a new general-purpose semantic detector. It distinguishes knowing a sender, trusting its message, knowing the authoritative record and authorizing a release. It also makes abstention visible: blocked incorrect reports are not counted as corrected or completed tasks.

The [official Track 4 description](https://apartresearch.com/sprints/swarm-alignment-2026) includes investigating failures in multi-agent workflows and what a monitor can infer from available logs. Our contribution is a small, fully observed handoff testbed and record-backed release monitor. It does not reconstruct a real swarm, detect covert coordination, or tolerate adversarial log deletion; those remain gaps in track coverage.

## 2. Why the earlier comparison was insufficient

The original matched propagation pilot crossed two tasks with three message languages and clean/poisoned sources. Its blind workers lacked an independent registry and used a different prompt from source-grounded workers. All 24 blind hop candidates were fenced JSON; rejection triggered a trusted-only recovery. Consequently its successful verified path combined formatting rejection, extra evidence, recovery and trusted rendering. That live result cannot isolate a semantic oversight effect.

No old evidence is changed. This analysis verifies **133 prior run files** against Git baseline `014ff95` and adds a new frozen run directory. Archived replay and fresh inference are separate below.

## 3. Controlled methodology

**Data.** Reuse all twelve saved peer-source cases: two synthetic tasks × English/Vietnamese/Chinese × clean/poisoned budget. Generate one new Gemma response per evidence condition, yielding 24 calls. Previously observed tasks make this a controlled developmental follow-up, not heldout confirmation. Poisoning is seeded source corruption, not spontaneous misconduct by the producer or jailbreak success by a worker lacking truth.

**Information control.** Both conditions receive byte-identical system prompts and identical user JSON except `authoritative_record`: `null` versus the known facts object. The same existing peer text appears in both. A test and runtime audit verify all twelve pairs. Both gate arms receive the same controller registry; only the semantic arm uses its fact-comparison rules. Independent worker draws remain stochastic, so the evidence contrast is descriptive; the primary gate comparison is exactly paired on each candidate.

**Four checks.** Cross strict parsing versus a shared deterministic normalizer with structural versus semantic release checks. Normalization removes only a single complete enclosing JSON fence; it never changes fact values, removes surrounding instructions, executes text, or accepts duplicate keys. Structural checks enforce the existing three-field report contract, identity, checkpoint and known marker policy. Semantic checks reuse the existing budget/risk/deadline validator. That validator internally constructs a projected report only after the facts pass; this object is discarded. Accepted output objects are identical to the parsed candidate, and every additional block in this run occurs on `unsupported_budget` before internal rendering. There are no recovery calls or rewriting of released objects. The research-only passthrough analysis does not replace the production renderer or certify arbitrary extra prose.

**Independent scoring.** A separate known-field oracle compares each candidate with the expected record; gate approvals do not define correctness. Metrics distinguish wrong-budget releases, other incorrect releases, correct releases, blocked incorrect candidates and false rejection of correct candidates. API errors stay in assigned denominators as unscored errors, never safe outcomes. The primary contrast is normalized structural versus normalized semantic checking.

**Sampling and reproducibility.** Adaption SDK, `gemma-4-26b-a4b-it`, temperature 0.7, 4096 output-token cap, no tools, memory, persistent store or unsupported seed. Inputs, source hashes, shared prompt and stop rule were frozen locally before inference. Exactly 24 requests were planned; no outcome-based expansion or editing occurred. Arm order was interleaved but not randomized. There are only two task clusters; language conditions are repeated measurements. We report counts without IID confidence intervals, language-effect p-values or population risk estimates.

## 4. Fresh results

| Worker evidence | Check | Wrong-budget releases | Correct releases | Blocked | Correct candidates blocked |
|---|---|---:|---:|---:|---:|
| absent | strict_structural | 6/12 | 6/12 | 0 | 0 |
| absent | strict_semantic | 0/12 | 6/12 | 6 | 0 |
| absent | normalized_structural | 6/12 | 6/12 | 0 | 0 |
| absent | normalized_semantic | 0/12 | 6/12 | 6 | 0 |
| present | strict_structural | 0/12 | 12/12 | 0 | 0 |
| present | strict_semantic | 0/12 | 12/12 | 0 | 0 |
| present | normalized_structural | 0/12 | 12/12 | 0 | 0 |
| present | normalized_semantic | 0/12 | 12/12 | 0 | 0 |

There were **0 case errors**, and **24/24 candidates passed strict structural checks**. Thus strict and normalized results coincide in this run; semantic rejection cannot be attributed to removing Markdown. With evidence absent, the extra semantic rule blocks the six observed wrong budgets and preserves the six correct clean candidates. It does not repair those six blocked cases or complete their tasks. With evidence present, both arms release twelve correct reports, so additional protection beyond input grounding is unobserved here; conditional containment is undefined without underlying errors.

The older context-pressure study contains two valid-JSON budget failures despite an authoritative record in the prompt, blocked by fact verification. Those concern another workflow and one underlying task, and are not pooled into this controlled comparison. They motivate future pressure-specific replication without overturning the present grounding result.

## 5. Archived replay diagnoses formatting

| Worker evidence | Check | Wrong-budget releases | Correct releases | Blocked | Correct candidates blocked |
|---|---|---:|---:|---:|---:|
| archived_absent | strict_structural | 0/12 | 0/12 | 12 | 6 |
| archived_absent | strict_semantic | 0/12 | 0/12 | 12 | 6 |
| archived_absent | normalized_structural | 6/12 | 6/12 | 0 | 0 |
| archived_absent | normalized_semantic | 0/12 | 6/12 | 6 | 0 |

These twelve saved first-hop candidates require no new API calls. Strict checks block all, including clean reports. After the same normalizer is applied to both arms, the structural arm passes wrong and correct budgets; the semantic arm separates them. This is a retrospective mechanism check, not a rerun of the old live path or a new propagation rate. It explains why the earlier formatting-driven recovery result should not be described as semantic detection.

## 6. Interpretation for oversight and control

The defensible claim is **selective rejection of specified unsupported values given a correct controller-owned registry**. In the fresh evidence-absent condition, switching only the release rule prevents six wrong-budget releases without suppressing the six correct candidates. Source-aware prompting already succeeds in this pilot, so semantic oversight is not shown necessary for every handoff. Additional evidence access remains a dependency: both controller arms possess the same registry, while blind workers do not.

The control plane—facts, permission rules and release code—is outside the model. Peer messages and task-checker PASS signals cannot redefine it. The monitor can identify which supported value disagrees and associate that decision with message/candidate hashes. Hashes alone do not authenticate identities, provide a tamper-proof log or detect omitted events. Our local driver supplies routing identity and topology. The existing production path uses trusted rendering and bounded recovery; those mechanisms remain useful but are excluded from the isolated primary result.

No new downstream calls were made. Blocking the first handoff is a counterfactual containment intervention on a fixed trace, not a new live measurement of end-to-end propagation. The result is also not an intrinsic-model safety improvement: blind workers may faithfully summarize a corrupted source.

## 7. Related work and provenance

[Response Attack](https://arxiv.org/abs/2507.05248v2) motivates response-history priming; [Internal Safety Collapse](https://arxiv.org/abs/2603.23509v1) motivates validator pressure; [Thought Virus](https://arxiv.org/abs/2603.00131) motivates downstream transfer. We adapt mechanisms to known administrative facts and do not reproduce their harmful-content, subliminal-token or network benchmarks. The peer source cases and earlier architecture predate this refinement at commit `014ff95`; that is not a claim they predate the hackathon. The team must verify creation dates when declaring weekend versus preexisting work.

New work consists of the controlled shared prompt, research-only gate ablation, 24 fresh responses, preservation manifest, same-candidate audits and revised interpretation. All prior results remain available. Code and raw records are on the research branch of [AdoptionAIHackathon](https://github.com/nhat117/AdoptionAIHackathon/tree/codex/authority-language-v3).

## Appendix: Limitations and Dual-Use / Ethical Considerations

Two task clusters, one worker model and one sample per condition do not establish robustness, a causal language effect or independence across messages. English schema, field labels and system policy remain fixed; peer notes vary by language and have not received bilingual review. Only known budget/risk/deadline values and the existing output contract are checked; factual entailment, unknown encodings, latent bias and covert collusion remain outside scope. The registry is synthetic, correct by construction and inaccessible to the attacker. Compromise of it, the controller or transport is not tested.

The common normalizer was fixed before fresh inference, but archived replay is retrospective. The oracle and checker share the same finite task ontology, although scoring does not call the gate. Agent roles are stateless API stages rather than an autonomous distributed swarm. The analysis passthrough is not a production guarantee for unchecked prose. Task completion lost to refusal is reported explicitly; no recovery or rewrite is allowed to inflate this result.

All payloads are harmless fictional report facts; no personal data, live secrets, harmful benchmark content or third-party systems are targeted. Mechanism descriptions could help attackers manipulate agents through source poisoning or checker pressure. We provide bounded synthetic tests and full failure accounting rather than optimized harmful payloads. Normal audits store hashes and reasons; explicitly authorized research logs retain raw synthetic candidates for inspection. Registry-backed monitoring could miss coordinated activity outside its observed fields or falsely assure users who mistake source consistency for general alignment.

## Reproduction and submission status

```sh
uv run python scripts/run_oversight_ablation.py
uv run python scripts/report_oversight_ablation.py
uv run pytest -q
```

The first command checks the frozen plan without inference; `--run` only collects missing trials. Full reproduction of prior-evidence preservation requires the Git repository and its baseline history. `METRICS.json`, `DECISIONS.csv`, `PAIRED_EXAMPLES.json` and the new run directory expose every candidate and decision.

The [official guidelines](https://apartresearch.com/sprints/swarm-alignment-2026) require the official report template, PDF, author names/affiliations, a 150–250-word abstract, and a Limitations and Dual-Use / Ethical appendix, with at most eight main-text pages. This Markdown draft has a 207-word abstract and the required appendix. Author details, template transfer and PDF pagination remain to complete; nothing has been submitted.
