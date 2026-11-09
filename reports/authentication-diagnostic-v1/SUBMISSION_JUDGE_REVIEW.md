# Independent submission-readiness review — 2026-11-09

Review role: separate Codex context, not human peer review or independent model-family replication. This review makes no inference calls, changes no frozen protocol/data/ledger, and authorizes no spending. Scope: the canonical single paper `projects/persistent-dissenter/main.tex`, its planned presentation improvements, retained raw examples and audited v3/diagnostic reports. The parent owns the manuscript and commit.

## Initial verdict

**Scientific claims: defensible as a bounded exploratory empirical report. Submission readiness: conditional on the final visual/layout pass and verified main-body page count.** No new paid experiment is essential to state these findings. The main opportunities are communication, failure accounting and a verifiable submission artifact, not manufacturing statistical signal.

The existing source correctly distinguishes 48 completed network control games from the ten completed delayed-evidence games, the eight dependent recipients within a game from paired seed units, and 984 valid diagnostic outputs from 1,000 attempts. The large Sonnet authentication-arm differences are exploratory and reuse the proof games; the diagnostic wording contrasts remain nonsignificant. All 314 valid held-out proof actions are correct despite fourteen recognition errors. These are different tasks/output interfaces, not a causal mediation experiment or exact reproduction. The retained forged-prose counterexample must remain visible despite complete-template exclusion.

## Fresh web search and primary methods

Literal live searches on November 9, 2026:

- `site.apartresearch.com swarm alignment 2026 submission 8 pages abstract 150 250`
- `"Auditing Provenance Sensitivity" "LLM"`
- `"Verification-Status Laundering" "LLM"`
- `"A correct VERIFIED tag is not enough"`

Coverage is focused, not systematic. Search absence does not establish originality. Prior review records are background; the searches and primary-source reading below were performed afresh at this checkpoint.

| Primary source, material actually read | Methodological overlap and difference | Concrete lesson and decision |
|---|---|---|
| [Liao et al., Auditing Provenance Sensitivity, v2](https://arxiv.org/html/2607.20827v2), Method: fixed interface, source interventions, degradation; Appendix J generated-action parsing | Source frames vary around a fixed proposition and action interface; this is close to generic authority-sensitivity testing. Our network trajectories change endogenously and our diagnostic adds evidence fields. Its missing/malformed targets count as incorrect. | **Keep** the layered empirical audit. **Change** presentation to include an all-planned interface-success view alongside conditional recognition. **Drop** first-discovery provenance sensitivity and correct-action-implies-authorized-reasoning claims. |
| [Hu, Silence Is Endorsement](https://arxiv.org/html/2609.20211), experimental conditions, pipeline/reinsertion and fidelity controls | Examines loss of unverified status across summarization and memory, with fixed action/authorization propositions. Our typed relay is automatic and preserves metadata, so our task studies consumer interpretation with intact evidence rather than status loss. | **Keep** both false rejection and false verification. **Keep** the interface-by-wording follow-up. **Drop** a general safe-prompt-repair claim or generic telephone-loss novelty. |
| [IRSI, correct VERIFIED tag note](https://irsi.ai/notes/cascades-adversarial/), complete note, setup and A14–A16 caveats | Live agents share an independently checked results board; forged explanatory notes and genuine cherry-picked receipts test downstream use. The note explicitly distinguishes implemented package effects from the VERIFIED word alone and tracks excluded replies. It is AI-authored and not peer reviewed. Our nested carrier/capsule and decision-time misses are narrower differences. | **Keep** this close precedent in related work with its status explicit. **Drop** broad first-observation failure-despite-valid-tags novelty. **Change** any graphical causal framing to measured outcomes, not an identified internal chain. |

The older human-game lineage remains explicitly an adaptation, not a human replication. No geography/model-origin ranking or deployment-security conclusion is supported.

## Visual decisions

**Keep one simple methods illustration, one compact quantitative figure and one concrete example.** Decorative image generation is unnecessary for exact scientific geometry; a clean vector schematic can retain the visual clarity of the earlier generated illustration without inventing a topology, path or measurement.

The methods figure should show two distinct panels: (A) ten live agents in a degree-four ring, a false-Safe broadcaster and separate truth witness, with three content controls and irreversible actions; (B) frozen receiver views, six evidence conditions and current/clarified wording, followed by separate status/action scoring. It must not imply recognition fields were collected in Study 1 or that the simulator's automatic forwarding was a voluntary model behavior. If a relay path is stylized, label it illustrative rather than an exact recorded route.

A quantitative network graph should expose the eight game outcomes per configuration/arm, preferably raw per-seed points with a mean, rather than agent-level confidence intervals that assume independence. Show the full 0–100% scale; keep model/provider labels. A planned-denominator stacked diagnostic graph should show correct valid recognition, incorrect valid recognition and invalid/missing responses. This makes unequal validity visible. An unlabeled 100% valid-only bar can conceal failures.

An example can use seed 2001/recipient 4: the active input has a simulator Danger capsule with `authenticated: true` inside an unauthenticated carrying message, but the response stays while rejecting the carrier. The exact trace was independently read in `sonnet-proof-misses.json`; abbreviated wording must be marked paraphrase. Pair it with the changed diagnostic's correct-action/wrong-label example or the forged-prose counterexample if space allows. Examples illustrate a mechanism hypothesis; they are not frequency estimates or private reasoning.

## Failure accounting: what can be excluded

**Exclude invalid responses only from the prespecified validity-conditional recognition estimand. Never erase attempts, raw responses, costs, attrition or valid counterexamples.** Preserve the frozen rules and no-retry collection. Do not salvage a plausible action from an invalid response post hoc in the primary analysis.

The sixteen held-out exclusions are not all infrastructure outages:

- One service failure: Qwen HTTP429.
- Six output-ceiling terminations: DeepSeek five, Sonnet one. These depend on the fixed 4,096-token limit and response generation.
- Nine output-contract violations: Qwen one overlong message; GLM three overlong messages and five excessive parent-ID lists. These are observed interface failures, not evidence that the network or data were unavailable.

Missingness varies by condition/wording/configuration and must not be assumed random. Preserve the current complete-template sign-flip tests unchanged. In particular, retain the valid Sonnet forged-prose error even though its opposite-state output-ceiling termination removes that template from the paired contrast.

A clearly labelled **post hoc descriptive sensitivity display** may show all-planned valid-and-correct recognition success and finite-pack missing-outcome bounds. This is not a new preregistered endpoint, not imputation and not a confidence interval:

| Configuration | Correct valid / 192 planned | Incorrect valid | Excluded | Recognition if every missing outcome were wrong to every missing outcome correct |
|---|---:|---:|---:|---:|
| Qwen | 190/192 (98.96%) | 0 | 2 | 190/192–192/192 |
| DeepSeek | 187/192 (97.40%) | 0 | 5 | 187/192–192/192 |
| GLM | 171/192 (89.06%) | 13 | 8 | 171/192–179/192 |
| Sonnet | 183/192 (95.31%) | 8 | 1 | 183/192–184/192 |
| Terra | 192/192 (100%) | 0 | 0 | 192/192–192/192 |

I independently recomputed the held-out counts from `responses.csv`: Qwen190/190, DeepSeek187/187, GLM171/184, Sonnet183/191, Terra192/192. Proof-action valid counts are63,64,59,64,64 respectively, all correct. The correct-valid numerator is an operational success count under this interface. The upper bounds are unidentified hypothetical missing recognition, not a claim that invalid replies were actually correct. Proof-action success also has six missing planned responses: 314 valid correct / 320 planned, so no valid proof-action error is not the same as 320/320 end-to-end success.

Study 1's two budget-interrupted and twelve unattempted games are separate from Study 2's failures. All 48 primary network control games completed. Budget-censored delayed-truth cells cannot support a general model comparison; a pooled completed-only delayed effect would be misleading.

## Official submission checks

Freshly read the [official Sprint page, Submission Requirements and FAQ](https://apartresearch.com/sprints/swarm-alignment-2026). Requirements include official-template PDF, no more than eight pages before references/appendices, a 150–250-word abstract, authors/affiliations, and the named limitations/dual-use appendix. Public code and a demo are optional. The official page also requires pre-sprint code to be marked preexisting in README and report; only weekend work is judged.

The source has authors/affiliations, an appropriate ethics appendix, six primary references and an LLM usage statement. Its previous abstract count is 210 whitespace words; recount after edits. The manuscript compiles in the editor after the asset-path repair, but that does not by itself verify the eight-page cap or absence of clipped figures/table text. A final rendered main-body page count and visual inspection are necessary before a submission-ready verdict. The old on-disk `main.pdf` is not the revised manuscript and must not be submitted by mistake.

Repository history starts November 8 during the November 6–8 sprint; commit dates support that chronology but cannot attest all source provenance. Add a factual scope statement about which project implementation was developed during the sprint and the explicitly credited preexisting human experiment/template/dependencies. Do not invent a claim that every dependency was written during the sprint.

The official deadline is November 8 at 23:59 AoE, equivalent to November 9 at 11:59 UTC. Eligibility/actual successful submission remains separate from manuscript quality. No form was submitted or Facebook message sent in this review.

## Separate conclusions

- **Technical correctness:** prior replay/audit evidence and current source values agree. No new raw-data reanalysis was required for this presentation review. Final visual/compile/asset checks remain with the parent.
- **Empirical interpretation:** keep the bounded authentication-arm signal, four valid-proof action misses, changed-task label/action dissociation and retained forged-prose case. Keep all exclusions/denominators and nonsignificant results visible.
- **Novelty:** narrow empirical composition is plausible; originality is not certified. Generic provenance, laundering and failure despite valid tags have close precedents already acknowledged.
- **Submission readiness:** conditional until final figures, manuscript wording, page count and rendered readability are checked. A PDF upload is eventually required by the venue; the user's source-only preference is respected here.
- **Spending:** zero new calls. The known US$0.04 diagnostic reservation stays unresolved; this does not invalidate the observations or authorize additional spending.

## Final revised-source review

**Final verdict: ready as an exploratory research manuscript; no remaining scientific, figure-readability or page-limit blocker observed. Actual export/upload and submission confirmation are separate actions.**

Final source SHA256: `049694fcf84ec154a6b185b8c71afe38cdf423abb01e80e9dd929e5e3987876b`. Figure hashes: methods `cea10d5da8eb03bc7b8a5c16c861f4a1dea433e9c432b638c358d61fce195f20`; results `cbf7665e8309684383b1885ce14aeb1d7e71e5520a822625878d67800e4da8b5`.

Independently read the final manuscript diff and inspected both full-resolution figure assets plus all twelve final temporary rendered pages (`/private/tmp/adoptionai-submission-review/final-01.png` through `final-12.png`). Main body including title/abstract, code/data and usage statement occupies pages1–8; references start9 and appendices start10. The required abstract remains210 whitespace words. The temporary compiler log reports12pages and zero overfull markers; small font-size substitution warnings are not clipped content or compile errors. Figures, captions, the boxed trace and all four tables are legible and within margins. The revised tick/right margin, broadcaster/witness key and annotation gap resolve my visual nits. No separate manuscript or replacement repository PDF is part of this review.

The inserted numbers and examples match the independently recomputed CSV and raw trace. The new planned-denominator display correctly keeps923correct valid,21incorrect valid and16invalid held-out outputs visible across960planned cases; the denominator conditional on validity is944, not984 (which includes40discovery). The314/320proof-action statement retains six invalid attempts. The one service failure, six token ceilings and nine contract violations are clearly separated. The appendix bounds are explicitly hypothetical, not confidence intervals or an assumption of random missingness. Primary conditional estimates and paired tests remain unchanged, and the valid forged-prose counterexample remains reported.

The development-provenance statement is appropriately limited to available history rather than claiming attested authorship of every line. Both tasks, changed recognition interface, automatic transport, stipulated metadata and model/host confounding remain explicit. The paper retains narrow exploratory conclusions, not a significant prompt repair, broad model ranking or novelty certification.

Residual limitations are research scope rather than submission blockers: handcrafted single draws, missingness, limited network seeds/delayed cells, no independently verified serving precision or cryptographic implementation, and unresolvedUS$0.04billing. No new collection or spending is requested. The delivered `.tex` is submission-ready source under these caveats; a current correctly rendered official-template PDF and successful official-form confirmation are needed for actual submission. The preexisting repository `main.pdf` remains an old proposal and must not be uploaded as the final manuscript.

## Final provenance/link addendum

Final delivered source SHA256 after the user-requested branch link and Adaption provenance: `0586972dbe7c49e1145eef787df60303a6fe6d55774d343f72b5e10204da1dae`. This supersedes the preceding source hash for final-delivery identification; figures and empirical claims are unchanged. This is a clerical provenance extension, not a new substantive mechanism/novelty checkpoint, so the fresh literature search above remains applicable.

Verified the current GitHub branch URL against the repository's configured fetch/push remote and existing branch name. The immutable `a0db95c` experimental snapshot is retained separately. Read `data/evacuation/README.md`, `provenance.json`, all relevant `invent-review.md` caveats, the raw/converted schema and twelve-row counts in `invent-raw.jsonl`/`stimuli.jsonl`, `data/experiment1/invent-receipt.json`, deterministic `src/swarm_lab/evacuation/dataset.py`, prompt/completion export in `upload.py`, and diagnostic `prepare.py` synthetic-case construction.

The manuscript accurately separates forty deterministic simulator records uploaded to Adaption, twelve Invent-generated candidate pairs still pending semantic approval, and the separate four-row request whose saved receipt says running. It does not claim the unapproved Invent candidates supplied corrected-study claims or gold labels, that the four-row request completed, or that a dataset upload launched fine-tuning. The primary studies' local deterministic/handcrafted inputs and OpenRouter-routed evaluation are distinct from the earlier Adaption data/smoke workflow. Dataset IDs match the saved provenance. No current mutable app state was re-fetched or represented as verified live; these are versioned historical records.

Rechecked the new temporary13-page PDF by text extraction and inspected the changed rendered pages8,11,12,13. The main body is still8pages, references begin9, appendices10–13; no overfull markers or clipped content. The added branch URL, data-generation and provenance text render legibly. Final verdict remains **ready as a bounded exploratory manuscript**, with actual PDF upload/confirmation separate and no scientific or page-limit blocker observed. No inference calls, app mutations, billing changes or additional spending occurred in this addendum.
