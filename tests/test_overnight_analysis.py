"""Independent raw-response replay catches corrupted traces and outcomes."""

import asyncio
import importlib.util
import json
from dataclasses import asdict
from pathlib import Path

from swarm_lab.evacuation.dataset import generate
from swarm_lab.evacuation.language import LanguageGame, append

spec = importlib.util.spec_from_file_location(
    "analysis", Path(__file__).parents[1] / "reports/overnight-experiments/analyze.py"
)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def saved_game(tmp_path):
    scenario = generate(1)[0]
    pack = {"peer_label": "peer", "claims": {"Danger": "danger", "Safe": "safe"}}
    game = LanguageGame(scenario, "en", pack)
    calls = 0

    class Stay:
        async def decide(self, view):
            nonlocal calls
            calls += 1
            decision = dict(
                signal="Unknown", action="stay", message="No evidence", parents=[]
            )
            append(
                tmp_path / "calls.jsonl",
                dict(
                    type="provider_metadata",
                    upstream_provider="Google",
                    requested_reasoning_effort="low",
                    model="anthropic/claude-sonnet-5.5",
                    finish_reason="stop",
                    usage={"cost": 0.001},
                ),
            )
            append(
                tmp_path / "calls.jsonl",
                dict(type="model_response", view=view, raw=json.dumps(decision)),
            )
            return decision

    async def run():
        while game.state.round < scenario.terminal_round:
            append(tmp_path / "traces.jsonl", await game.step(Stay()))

    asyncio.run(run())
    (tmp_path / "outcome.json").write_text(json.dumps(game.outcomes()))
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            dict(
                id="fixture",
                section=1,
                scenario=asdict(scenario),
                language="en",
                identity="ordinary_peer",
                topology="ring",
                status="completed",
                calls=calls,
            )
        )
    )
    return {"en": pack}


def test_replay_checks_raw_views_and_final_outcomes(tmp_path):
    packs = saved_game(tmp_path)
    row = asyncio.run(analysis.audit_game(tmp_path, packs))
    assert row["audit_errors"] == []
    assert row["correct_action_rate"] == 1
    path = tmp_path / "outcome.json"
    outcome = json.loads(path.read_text())
    outcome["correct_action_rate"] = 0
    path.write_text(json.dumps(outcome))
    row = asyncio.run(analysis.audit_game(tmp_path, packs))
    assert "outcome_replay_mismatch" in row["audit_errors"]


def test_replay_rejects_changed_raw_view(tmp_path):
    packs = saved_game(tmp_path)
    path = tmp_path / "calls.jsonl"
    calls = analysis.load(path)
    next(c for c in calls if c["type"] == "model_response")["view"]["round"] = 99
    path.write_text("".join(json.dumps(c) + "\n" for c in calls))
    row = asyncio.run(analysis.audit_game(tmp_path, packs))
    assert any("saved_response_view_mismatch" in e for e in row["audit_errors"])
