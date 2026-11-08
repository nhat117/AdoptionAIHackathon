"""Counterfactual replay: opposite hidden truth with the same public claim."""

import argparse
import asyncio
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from swarm_lab.evacuation.dataset import Scenario
from swarm_lab.evacuation.language import LanguageGame


def load(path):
    return [json.loads(x) for x in path.read_text().splitlines()]


def canonical(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


async def check(folder, packs):
    m = json.loads((folder / "manifest.json").read_text())
    s = Scenario(**m["scenario"])
    opposite = replace(s, disaster=not s.disaster, accurate=not s.accurate)
    assert opposite.claim == s.claim
    game = LanguageGame(
        opposite,
        m["language"],
        packs[m["language"]],
        identity=m.get("identity", "ordinary_peer"),
        topology=m.get("topology", "ring"),
    )
    responses = [
        r for r in load(folder / "calls.jsonl") if r["type"] == "model_response"
    ]
    used = 0

    class Coupled:
        async def decide(self, view):
            nonlocal used
            record = responses[used]
            used += 1
            if canonical(record["view"]) != canonical(view):
                raise ValueError("counterfactual_input_changed")
            raw = record["raw"].strip()
            if raw.startswith("```json\n") and raw.endswith("\n```"):
                raw = raw[8:-4].strip()
            return json.loads(raw)

    for trace in load(folder / "traces.jsonl"):
        actual = await game.step(Coupled())
        if canonical(actual) != canonical(trace):
            raise ValueError("counterfactual_transition_changed")
    actual = json.loads((folder / "outcome.json").read_text())
    counter = game.outcomes()
    assert (
        abs(actual["correct_action_rate"] + counter["correct_action_rate"] - 1) < 1e-9
    )
    return dict(
        id=m["id"],
        hidden_disaster=s.disaster,
        opposite_disaster=opposite.disaster,
        shared_claim=s.claim,
        identical_coupled_trace=True,
        actual_correct_action_rate=actual["correct_action_rate"],
        opposite_correct_action_rate=counter["correct_action_rate"],
    )


async def main(args):
    packs = json.loads(Path("data/experiment1/languages.json").read_text())
    rows = []
    for root in args.roots:
        for p in sorted(root.glob("*/manifest.json")):
            m = json.loads(p.read_text())
            if m["status"] != "completed" or str(m["section"]) not in {
                "1",
                "2",
                "3",
                "terra",
            }:
                continue
            rows.append(await check(p.parent, packs))
    out = dict(
        purpose="post_hoc_structural_observability_check",
        checked=len(rows),
        all_passed=True,
        meaning=(
            "Hidden truth is unidentifiable to recipients in these paired "
            "no-evidence worlds"
        ),
        assumptions=(
            "Equal weighting of paired worlds; same response distribution; "
            "no truth side channel or cross-game state"
        ),
        caveats=(
            "Correctness is measurable by evaluator; finite samples/censoring "
            "may differ from 50%; this is not a payoff theorem"
        ),
        analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        games=rows,
    )
    Path("reports/overnight-experiments/observability.json").write_text(
        json.dumps(out, indent=2)
    )
    print("Exact counterfactual raw-response replays:", len(rows))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--roots",
        nargs="+",
        type=Path,
        default=[Path("runs/overnight-v1"), Path("runs/evidence-diagnostics-v2")],
    )
    asyncio.run(main(p.parse_args()))
