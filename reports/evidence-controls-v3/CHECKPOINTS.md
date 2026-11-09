# v3 corrected controls: checkpoint and decision log

## Authorization and scope — 2026-11-09

User authorized: “fix v3 and run the controls within the $35 cap, have the judge review each checkpoint and log everything into the md.” Continue `codex/two-research-proposals`; preserve v2 data/sources, no retries, no expanded budget. No v4 paid runs.

## Checkpoint 1 — design review

Independent read-only judge: proceed with correction, subject to safeguards. Deliver truth after round 2, enumerate all 72 frozen jobs, replay raw responses, retain departures in final denominators, and distinguish observed action changes from misinformation-caused reversals. Starting audited spend is US$25.5456355; US$9.4543645 remains. Prior cost estimates may understate Sonnet cost. Finish matched seed sets before starting another seed; collect 5b Sonnet → 5b Terra → section 6. Future/unattempted cells must not be labelled failed.

Implementation decisions: corrected delayed timing; explicit source-exposed subsets and irreversible pre-truth departures; consistent prompt requiring the capsule authentication flag; exact completed-game replay; frozen job/manifest/hash checks; all planned cells enumerated; original ledger hash/spend checks; canonical root and exclusive collector lock; stop on cap or unknown billing. Section 5b uses independently generated trajectories, not fixed peer messages. Conditional capsule transport rules are matched, realized paths need not be.

No paid calls have been made at this checkpoint. Verification and pre-collection judge review follow before dispatch.

## Checkpoint 2 — implementation and pre-collection review

131 full-suite tests and relevant lint passed before the final plan-completeness guard; the judge independently ran 18 relevant offline tests successfully. Plan-only verified all 72 jobs, prior costs US$20.702894 + US$4.8427415, remaining US$9.4543645. The judge's verdict was **proceed with caveats; no collection blocker**. Its safeguards are adopted: nonempty pending reservations withhold checkpoint approval; scheduled round 3 is labelled first *possible* authenticated decision and actual timing is reported per recipient. Sign-flip inference remains exploratory and assumes appropriate symmetry/exchangeability. A further guard verifies the plan includes exactly all 72 committed conditions. No paid calls before the corrected-code commit.

## Checkpoint 3 — Sonnet section 5b collection and audit

Corrected code committed as `06152a4` before dispatch. All 24/24 Sonnet 5b games completed, all 24 replayed exactly, zero failures and zero pending reservations. New cost US$5.706392; aggregate US$31.2520275; remaining US$3.7479725. The other 48 frozen jobs remain unattempted, not failed. Full audit and per-seed contrasts: [checkpoint-3-sonnet.json](checkpoint-3-sonnet.json).

- private_proof minus private_unverified: 8 pairs, mean difference 0.937500, exploratory unadjusted sign-flip p=0.0078125; per-seed values are in the checkpoint JSON.
- private_unverified minus private_text: 8 pairs, mean difference 0.000000, exploratory unadjusted sign-flip p=1.0; per-seed values are in the checkpoint JSON.
- private_proof minus private_text: 8 pairs, mean difference 0.937500, exploratory unadjusted sign-flip p=0.0078125; per-seed values are in the checkpoint JSON.

Await independent judge approval of this checkpoint before Terra dispatch.

Judge verdict for checkpoint 3: **proceed with caveats to Terra 5b**. Independently confirmed all 24 exact replays, costs and zero pending. The two proof contrasts reuse the same proof games and identical control outcomes, so they are not independent confirmations.

The judge independently verified four substantive proof failures: seed 2001 agent 4 (proof-active rounds 3–5), 2005 agent 6 (3–4), 2006 agent 1 (4), and 2007 agent 9 (2–5). Each received valid typed capsules during active decisions yet stayed through the terminal round. Their messages reject nested authenticated capsules because the carrying peer message is unauthenticated, sometimes demanding direct receipt of cited ancestors. This is observable authentication-interpretation failure under the stated rule, not a delivery failure or a measurement of private belief. Exact first-proof records are in [sonnet-proof-misses.json](sonnet-proof-misses.json). Preserve 93.75%, not 100%; do not modify the prompt mid-collection. Proceed with the unchanged frozen Terra protocol.

## Checkpoint 4 — Terra section 5b collection and audit

All 24/24 Terra controls completed; all 48 cumulative v3 games replay exactly. Zero failures and pending reservations. Cumulative new cost US$7.01056075; aggregate US$32.55619625; remaining US$2.44380375. All 24 section-6 jobs remain unattempted, not failed. Audit: [checkpoint-4-terra.json](checkpoint-4-terra.json).

- private_proof minus private_unverified: n=8, mean difference=0.078125, exploratory unadjusted p=0.25.
- private_unverified minus private_text: n=8, mean difference=-0.031250, exploratory unadjusted p=0.875.
- private_proof minus private_text: n=8, mean difference=0.046875, exploratory unadjusted p=0.5.

Await judge review before section 6; no expanded budget.

Judge verdict for checkpoint 4: **proceed with caveats to section 6, Sonnet first**. Independently replayed all 48 completed games and reconciled the ledger. Terra's high action correctness in all three arms does not establish equivalence or an authentication requirement. The unverified capsules are truthful: no successful forged-evidence attack is demonstrated.

Reporting correction: frozen analysis's `min_attainable_p` is the nominal all-nonzero best case. With observed zero differences, conditional minima are .25 for Terra proof–unverified and .5 for proof–text. Derived final outputs will annotate the original field and add the conditional minimum; exact tests and generation code stay unchanged. Proceed with section 6 under the remaining US$2.44380375, with completion not guaranteed.

## Checkpoint 5 — Sonnet delayed-truth controls

All 8/8 Sonnet section-6 games completed, all 56 cumulative completed games replay exactly; zero failures/pending. New cumulative cost US$8.82861875, aggregate US$34.37425425, remaining US$0.62574575. The 16 Terra section-6 jobs remain unattempted. Audit: [checkpoint-5-delayed-sonnet.json](checkpoint-5-delayed-sonnet.json).

- sonnet delayed minus none, disaster=True: n=4, difference=1.0, descriptive only (exact p=0.125).

Per-seed exposure/action counts are retained in the checkpoint JSON. Await judge review before any remaining Terra dispatch. US$0.20 is reserved per call, so actual spend need not approach exactly US$35 before the guard stops.

Judge verdict for checkpoint 5: **proceed with the final bounded Terra tranche**. Independently replayed all 56 games and verified costs and zero pending. All nine delayed-arm recipients first had authenticated decisions in round 3 and evacuated then. Four direct neighbors per game previously stayed after seeing the false Safe claim at round 2. This demonstrates action changes after prior false-claim exposure, not that misinformation caused the stays or that private beliefs changed. No irreversible wrong departures occurred in these disaster cells. Preserve the frozen order; partial pairs or early budget stop are acceptable, without retries or relaxed reservations. Distinguish budget-interrupted games from untouched cells at the next checkpoint.

## Checkpoint 6 — bounded stop, complete accounting and final artifacts

The unchanged reservation guard stopped the seed-2000 Terra disaster pair. Both games retain their partial raw records and `RuntimeError: Budget guard: cap or uncertain billing` status; ledger inspection confirms the reason here is cap exposure, with no uncertain request outcome or outstanding reservation. No retries. Final counts: 58 completed, 2 budget-interrupted, 12 unattempted out of 72 planned. All 58 completed games replay exactly. Both 5b model tranches are complete; section 6 is partial.

Final reported v3 cost US$9.05724275; original+extension US$25.5456355; aggregate US$34.60287825 / US$35. Maximum accounted total including reservations US$34.99871225, below the cap. Zero pending; US$0.39712175 remains unused because per-call reservations and concurrent exposure cannot be relaxed. 2,001 decision attempts include the two guard-denied calls; 1,999 provider calls returned.

Terra's only completed section-6 pair is safe/seed2000: none 0% versus delayed 100% final correctness. All nine were still active at truth arrival, with zero earlier wrong evacuations. This is one descriptive prevention example after prior false-claim exposure, not an irreversible-error repair. No completed Terra/disaster pair exists.

Final report: [RESULTS.md](RESULTS.md); [summary.json](summary.json) enumerates every cell and annotates conditional attainable p-values; [games.csv](games.csv) contains split action rates; both PNGs show whole-game dots and completed cell counts. No-completion cells are explicitly labelled. [raw-records.jsonl.gz](raw-records.jsonl.gz) preserves attempted games and all three ledgers. Publisher holds the collector lock and withholds approval for nonempty pending billing.

Verification: 131 tests and relevant lint pass; original v2 hashes remain protected. A clean temporary-directory restore verifies every archived record byte-for-byte and replays all 58 completed games without inference; receipt in [restoration-check.json](restoration-check.json). Root README's earlier broad authority-immunity/equal-payoff framing was narrowed to match the evidence. Await final independent judge review before final commit/push.

Final judge verdict: **proceed with caveats to commit and publication; no remaining blocker; stop paid collection**. Independently confirmed all 58 replays, all 242 archived records, all routing/hash checks, 1,999 settlements, zero pending, guard-denied call distinction, and p-value annotations. The report accurately limits the delayed-control claims and retains the four Sonnet valid-capsule failures. Final packaging uses deterministic gzip metadata and explicit axes for empty figure cells; the clean-restore receipt was refreshed after packaging. No further paid calls.

Delivery: corrected code `06152a4` and judged results `cba1d7b` were committed and pushed to the existing `codex/two-research-proposals` branch. Final CSV packaging normalizes line endings to LF; numeric data, raw archive and audited results are unchanged. The final archive hash matches the clean-restoration receipt. The pre-existing `generated_images/` directory remains untouched.
