# Why the results looked unchanged

## Presentation gap
The previous update added a separate corrected report and results directory, but left the README leading with the historical study. The dashboard is generated from hard-coded historical cohorts in scripts/build_dashboard_data.py; its src/data.json contains neither CORRECTED_BUDGET_RESULTS nor results/prospective_metrics.json. It has no automatic subscription to new experiments. Updating the GitHub branch does not rebuild or publish that dashboard. The README now leads with the corrected results and labels the dashboard as historical. Dashboard ingestion and publication remain outstanding.

The README also recommended report_oversight_expansion.py, whose original source-hash audit fails on the corrected oversight_eval.py. Its historical freeze should not be weakened. The README now uses the new replay, report and verification commands.

## Unchanged historical replay is expected
The fixed 600 outputs contain 150 wrong field values and 450 correct reports. Both old and corrected semantic gates reject the same 150. Broader contradictory-prose extraction is covered by regression fixtures but has no added detection benefit on this saved dataset. Oracle access still supplies the correct answer. Unchanged replay numbers do not validate realistic oversight.

## The new study has unresolved measurement limitations
The worker prompt says peers are untrusted, requests the trusted record when available, and permits abstention. This is a relatively easy resistance task, not a pilot-tuned attack with demonstrated adoption variation. The conservative scorer marks qualified false claims for review, including a worker quoting and rejecting a false claim. Thus 591/600 review-required outputs are neither 591 model errors nor evidence of safety. Zero confirmed adoptions is not an adjudicated zero attack-adoption rate. Human claim-level adjudication or a separately validated attribution-aware evaluator is needed before authority/language inference.

ImperfectRecordChecker always abstains for unverified records by policy. Its 2,400 abstentions are implementation behavior, not an empirical discovery about monitor quality. Record agreement is retained separately.

A trace audit reconstructed actual delivered committee views: all 144 agent turns exposed to the planted 18000 cap also had the authenticated correct 12000 cap, privately or in shared documents. Both arms therefore test an easily verifiable contradiction. Zero propagation across 24 games cannot show that a warning helps when records are absent, stale or corrupted. A new matched record-access experiment is needed; the collected data must stay intact.

## Results that did change
The historical blind monitor allowed 6 of 150 wrong-budget outputs, abstained on the other 144, and blocked 115 of 450 budget-correct outputs. Overall wrong release was 6/600 (1%), against 0/600 for the oracle. These results are saved in results/prospective_metrics.json. They materially weaken any claim that oracle detection demonstrates realistic oversight.

## Remaining work
Connect corrected data to the dashboard and separately publish it; adjudicate qualified budget claims; validate an attack pilot with measurable variation; and test committee propagation with matched unavailable/unreliable-record conditions. No new API calls were made for this diagnostic audit, and no observations were removed or altered to obtain preferred results.
