# Message stance check (method fix 8)

`src/swarm_lab/evacuation/stance.py` labels each delivered message as **agrees**, **disagrees**, **asks_proof** or **neutral** relative to the source's claim. The machine signal decides when it is Safe or Danger. Unknown-signal messages count as `asks_proof` only for explicit requests ("Please share any evidence", "Is this verified?"). Absence of evidence ("no evidence yet") is neutral.

The rule is used in analysis only after a hand check:

1. `sample.csv` holds 48 messages from the saved games, 12 per rule label, drawn with a fixed seed. Regenerate it with `.venv/bin/python reports/stance/label_messages.py sample --roots runs/restored-review/original runs/restored-review/extensions`.
2. A team member fills in `human_label` with one of the four labels, without looking at `rule_label` first. A Vietnamese speaker should take the Vietnamese rows.
3. Run `.venv/bin/python reports/stance/label_messages.py agreement`. If Cohen's κ ≥ 0.7, the rule may be used. If not, report stance as not validated, or revise the rule and label a fresh sample.

The labels describe stated stance, not private belief. Many messages both dispute a claim and ask for proof; the label records the machine signal first.
