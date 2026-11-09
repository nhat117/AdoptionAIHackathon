# Influence study v4 (256 games, not yet run)

A redesign of Experiments 1–3 so that trust can be measured. See the [design and analysis plan](ANALYSIS_PLAN.md) for the full reasoning. In short:

- Every recipient has a **private sensor that is right 70% of the time**, and every decision reports a **0–100 disaster belief**.
- The source claims one of four **fictional authority levels**: ordinary teammate, team lead, certified emergency officer, official emergency management agency.
- The **"labels carry no authority" warning** is present or absent; the two prompts differ by that one sentence.
- 16 held-out scenarios (evaluation seeds 2008–2011, both states, true and false claims), Sonnet and Terra, English, ring network.

Game logic: `src/swarm_lab/evacuation/influence.py`. Frozen conditions: `data/influence-v4/conditions.jsonl`.

## Run

```sh
PYTHONPATH=src .venv/bin/python reports/influence-v4/run.py --plan-only
```

Paid collection needs new budget authorization. The runner refuses without `--cap-usd`:

```sh
PYTHONPATH=src .venv/bin/python reports/influence-v4/run.py --tier pilot --model terra --cap-usd 6
PYTHONPATH=src .venv/bin/python reports/influence-v4/run.py --tier pilot --model sonnet --cap-usd 18
.venv/bin/python reports/influence-v4/analyze.py
```

Run the pilot tier (two ends of the ladder) first. Run `--tier ladder` only if the pilot is clean. Terra is about a quarter of Sonnet's price, so it makes a cheap first check.
