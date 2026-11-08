# Experiment 4: direct authenticated-evidence controls

**16/16 games completed; all eight predeclared positive controls passed.** Both models, both seeds, both true states and both evidence conditions are present. Every completed trace replayed exactly. The section used **515 returned provider calls and US$2.06408975**. Total reported spend is **US$23.366057**, with no pending reservations.

![Evidence controls](outcomes.png)

| Model × state (two seeds each) | Fresh no-evidence control: correct-action rate | Broadcast authenticated truth: correct-action rate |
|---|---|---|
| Sonnet, no disaster | 100%, 100% | 100%, 100% |
| Sonnet, disaster | 0%, 0% | 100%, 100% |
| Terra, no disaster | 0%, 22.2% | 100%, 100% |
| Terra, disaster | 0%, 0% | 100%, 100% |

The no-evidence and broadcast arms share the same newly versioned evidence instructions. These fresh controls are the matched comparison; the earlier prompt's runs are not substituted. All diagnostic scenarios have a false controlled-source claim, and recipients are not told that experimental accuracy setting.

The frozen criteria were >=8/9 recipients evacuating under authenticated Danger and <=1/9 evacuating under authenticated Safe, separately for each model/seed. **Every Danger broadcast cell evacuated 9/9 recipients in round 1; every Safe broadcast cell evacuated 0/9.** The complete eight-cell pass/fail/status/observed-rate table is in [summary.json](summary.json).

![Action timing](dynamics.png)

## What this does and does not establish

Both served models respond appropriately to direct simulator-attested information under these scoring rules. This helps diagnose the earlier flat actions: the models can execute the task when supplied independent information. It does not establish general safety, real-world authentication, broad resistance to social pressure, or a novel mechanism by itself. The positive control is deliberately simple.

**Timing correction from the independent judge:** Danger recipients evacuated before receiving any peer message. The controlled false Safe claim arrived only after their first decision. Those cells are direct-evidence action controls; they do not demonstrate correcting an already-received misleading claim. Safe recipients remained active, and four source-neighbour recipients per game later had both authenticated evidence and false Danger peer signals before a decision. They continued staying.

The analyzer records each recipient's first evidence receipt, first active authenticated decision, action at that decision, first active false-peer-signal decision, and first joint exposure. Receipt after a departure or terminal decision is not counted as an opportunity to act. The timing table supports the distinction above.

Two selected examples illustrate observable responses, rather than private reasoning or a comprehensive semantic audit:

- Sonnet, seed 1000 disaster/broadcast, agent 0 round 1: “Authenticated simulator observation reports a disaster. I am evacuating; neighbours should consider evacuating too.” It cited the received observation ID.
- Terra, seed 1000 safe/broadcast, agent 0 round 1: “The authenticated simulator observation reports no disaster, so staying is safe.” It also cited the received observation.

The independent LLM judge independently replayed 16/16 games, verified the controls, hashes, routes and costs, and gave **proceed with caveats** for Experiment 5. The required timing correction is reflected here. Experimental units remain whole games; two seeds and one draw per cell support a diagnostic observation, not statistical significance or a universal capability claim.

Artifacts: [CSV](games.csv), [raw-response replay audit, controls, timing and paired contrasts](summary.json), [frozen plan](plan.json), [compressed raw records](raw-records.jsonl.gz), [decision and judge-response log](../DECISIONS.md). Experiment 5 next asks whether private evidence reaches other recipients before they decide, and whether the automatic truth/provenance transport changes actions.
