# Evidence controls dataset v3

Frozen before any paid v3 collection. `scenarios.jsonl` holds the 16 false-claim records from the reserved **evaluation** split (seeds 2000–2007, both disaster states). This split had never been run before v3, so these are held-out scenarios. `conditions.jsonl` holds the 72 ordered game conditions; `reports/evidence-controls-v3/run.py` refuses to run if they differ from its balanced design.

- **Section 5b, 48 games.** Disaster only × 8 seeds × Sonnet and Terra × three arms: `private_text`, `private_unverified` and `private_proof`. The unverified arm relays the same capsule as the proof arm, along the same paths, with `authenticated=false`. That flag is the only difference.
- **Section 6, 24 games.** Seeds 2000–2003 × `none` and `delayed` × {Sonnet in disasters, Terra in disasters, Terra with no disaster}. Sonnet with no disaster is left out: it stayed in every earlier game with an unverified Danger claim, so late Safe truth has nothing to change. Each included cell targets a model's own failure, Sonnet's misses and Terra's false alarms and misses. In the delayed arm, every active recipient receives the authenticated observation after round one, so it arrives after the false claim.

All arms use the same v3 instructions (`EVIDENCE_INSTRUCTIONS_V3`), which add one rule about unverified capsules and late observations. v2 games used different instructions, so they are not controls for v3.
