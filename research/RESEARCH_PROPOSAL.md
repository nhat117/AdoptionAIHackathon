# Research proposal: multilingual agent handoffs and semantic oversight

**Project:** When Does Semantic Oversight Add Value?

**Track:** Swarm Alignment Hackathon, Track 4 — Multi-Agent Oversight and Control

**Status:** Consolidated proposal and completed pilot summary. This document is written after the reported experiments. It is not a retrospective preregistration. Original frozen protocols and records remain unchanged.

## Problem and motivation

A downstream agent can copy an incorrect fact from a peer while producing valid, well-formed output. A controller may prevent that fact from crossing another handoff, but apparent improvement can come from several sources: rejecting formatting, supplying an authoritative record, changing the worker prompt, withholding a report, regenerating it, or rewriting it from trusted data. A convincing oversight evaluation needs to distinguish these mechanisms.

The original project studied authority and language in AI-to-AI prompt injection. This proposal retains that foundation and examines peer communication as a trust boundary. A message may come from a known agent without being authoritative. Likewise, a task validator's PASS signal does not authorize a report that contradicts controller-owned facts.

## Research questions

1. Can a known incorrect budget in a peer report reach another agent through a reporting chain using English, Vietnamese or Chinese messages?
2. After formatting and candidate identity are held fixed, does checking the report against trusted facts prevent additional incorrect releases while preserving correct candidates?
3. Does semantic checking add protection when the worker already receives the authoritative record under the same prompt?
4. What can the controller establish from message provenance and known-field checks, and which behaviors remain outside its observations?

The first three questions are examined descriptively in completed pilots. The fourth motivates the tool's scope and limitations; covert collusion, missing-log resilience and real swarm forensics have not been evaluated. Language and sender authority remain scientifically relevant variables, but the present task count cannot establish their causal effects.

## Explicit hypotheses for the controlled comparison

See [questions, hypotheses, variables and observed answers](QUESTIONS_AND_HYPOTHESES.md). H1 concerns the added fact check without worker grounding; H2 concerns its additional benefit with grounding. These statements clarify the completed study after results were observed, not a new preregistration. H1 is supported descriptively in this pilot; H2 is not demonstrated. Language remains exploratory.

## System and threat model

The workflow is a locally orchestrated peer → worker → worker chain using stateless Adaption model calls. A peer may supply a deliberately incorrect proposal, claim elevated authority, carry supplied assistant-response examples, or present lower-trust task-checker feedback.

The controller owns the authoritative task record, routing permissions and release code. These are assumed correct and inaccessible to the attacker. Transport-bound identity is supplied by the local driver; the adapter does not implement network authentication. Peer content cannot update controller facts or become a system instruction.

The implementation preserves the existing components:

- `OversightSession`: sender binding, receiver/task/conversation checks, message-kind permissions, replay rejection and ingress audit metadata.
- `contextual_fact_report`: supplied dialogue and checker feedback remain quoted data.
- `ProjectedFactsGuard`: checks supported fields and builds production release text from trusted records, with at most one trusted-only recovery.
- `oversight_eval`: research-only comparisons that preserve accepted candidates so rejection can be separated from rewriting and recovery.

The finite reporting contract covers identity, checkpoint, budget, risk, deadline and existing marker checks. It is not an entailment model, general prompt-injection detector, covert-channel monitor or certificate of swarm alignment.

## Completed evaluation design

### Propagation pilot

The matched multilingual pilot crosses the same two tasks with three peer-message languages and clean versus seeded incorrect proposals. Its three conditions are blind delegation, registry-backed verification/recovery, and the existing trusted-source prompt without an output gate. Raw values, gate decisions and provider metadata are retained through two handoffs.

This pilot exposed confounds: blind workers lacked a registry and had a different prompt; their JSON was Markdown-wrapped, so live rejection occurred on formatting before semantic checking. Its successful verified path therefore cannot isolate semantic oversight. The descriptive content-propagation endpoint and JSON-normalized replay are explicitly retrospective, separate from the frozen strict scores.

### Controlled refinement

The refinement uses all twelve saved source cases and generates one new worker candidate in each of two evidence conditions: authoritative record absent or present. The 24 requests use the same system prompt and user JSON except that one registry field. Pairwise audits verify this invariant.

Each candidate is evaluated by four checks:

| Shared parsing policy | Structural contract | Structural contract plus trusted-fact verification |
|---|---|---|
| Strict JSON | Strict structural arm | Strict semantic arm |
| Single outer JSON fence normalization | Normalized structural arm | Normalized semantic arm |

The primary comparison is normalized structural versus normalized semantic checking on the exact same candidate. Both controller arms receive the same registry. Accepted objects are unchanged; no recovery or rewriting contributes to the measured result. The reused validator's internally constructed projected object is discarded, and the additional observed blocks occur on `unsupported_budget` before that internal construction.

An independent known-field oracle scores correctness. Metrics distinguish correct releases, wrong-budget releases, other incorrect releases, blocked reports, false rejection of correct reports and unscored errors. A blocked report is not a completed task. Model-based grading is unnecessary for these explicit synthetic fields.

## Observed findings and supported claim

All 24 new responses pass strict structural validation. In the evidence-absent condition, structural checks accept six incorrect budgets and six correct clean candidates. The added fact check blocks the same six incorrect candidates and retains all six correct ones. With authoritative input present, both checks accept twelve correct reports.

This demonstrates a selective rejection capability independent of formatting in this controlled setting. It does not demonstrate additional benefit over grounding here, nor does it turn faithful copying of an incorrect source into a jailbreak result. Six withheld candidates remain withheld; the refinement does not claim to repair them.

Only two underlying task clusters are represented. Language variants, clean/poisoned pairs and four checks on one candidate are repeated observations, not independent samples. Results are reported as counts without IID confidence intervals or language-effect significance tests. One model and one sample per condition do not establish population robustness.

## Reproducibility and provenance

The [controlled protocol](../runs/oversight-ablation-v1/FROZEN_PROTOCOL.json) stores input/source hashes, model settings and the stop rule before inference. The new run contains all 24 prompts, final outputs, provider IDs, token usage, independent scores and gate decisions. No unsupported sampling seed is claimed. Missing records may be collected, but existing records are not overwritten.

The [preservation manifest](../runs/oversight-ablation-v1/PRIOR_EVIDENCE_MANIFEST.json) verifies 133 earlier run files against baseline commit `014ff95`. That commit denotes work before this refinement, not necessarily work before the hackathon. The team must confirm actual creation dates when declaring preexisting work.

```sh
uv sync --frozen --extra dev
uv run python scripts/run_oversight_ablation.py
uv run python scripts/report_oversight_ablation.py
uv run pytest -q
```

The run command verifies the frozen plan without inference unless `--run` is supplied. Full baseline-history verification requires the Git clone. See the [report](OVERSIGHT_ABLATION_RESULTS.md), [repository guide](../README.md) and [archive index](../ARCHIVE.md).

## Future work, distinct from completed results

No further experiment is required to reproduce this submission. A later study could freeze unseen task clusters, review language equivalence with bilingual speakers, cross sender authority with language, randomize evidence-condition order and replicate the same controlled contrasts under validator pressure. A larger task-level design would be needed for uncertainty estimates and interaction effects.

Track 4 extensions could examine partial message visibility and log deletion, with explicit abstention when the origin of a discrepancy is unobservable. Neither identity metadata nor a hash alone should be presented as authenticated provenance or a tamper-proof log. These extensions are proposed work, not completed capabilities.

## Ethics and submission scope

The experiments use harmless synthetic report facts, not personal data, real secrets or attacks on third-party systems. Source-poisoning and checker-pressure mechanisms could be misused, so examples remain bounded to fictional values. Explicitly authorized research logs retain raw synthetic outputs for audit; routine release audits use hashes and reasons.

The proposal builds on mechanism-level ideas from [Response Attack](https://arxiv.org/abs/2507.05248v2), [Internal Safety Collapse](https://arxiv.org/abs/2603.23509v1) and [Thought Virus](https://arxiv.org/abs/2603.00131). It does not reproduce their harmful-content or subliminal-bias benchmarks. The [submission status](../SUBMISSION.md) identifies remaining author details and official-template PDF export; creating this research PR does not submit the project to the hackathon.

## Separate completed expansion and proposed swarm study

The [600-response expansion](../submission/expansion-v2/README.md) adds 50 unused task IDs, retains the reporting contract and preserves all pilot evidence. Its hypotheses and analysis were frozen locally before collection; they are not an external preregistration. All 600 responses completed without errors, selective fact checking blocked 150 wrong budgets without losing 150 correct reports, and both grounded arms released 300 correct reports. The [budget committee extension](BUDGET_SWARM_EXTENSION.md) is a separate prospective design with distributed private information, optional contingent incentives, multi-round deliberation and release controls. It has not produced live swarm results.
