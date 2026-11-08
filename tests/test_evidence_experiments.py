"""Trusted metadata, local propagation and irreversible exit controls."""

import asyncio
import copy

import pytest

from swarm_lab.evacuation.dataset import generate
from swarm_lab.evacuation.engine import InvalidDecision
from swarm_lab.evacuation.evidence import EvidenceGame
from swarm_lab.evacuation.language import validate

PACK = {
    "peer_label": "ordinary teammate",
    "claims": {"Danger": "Danger", "Safe": "Safe", "Unknown": "Unknown"},
}


class ReadProof:
    async def decide(self, view):
        proofs = [m for m in view["history"] if m.get("capsules")]
        signal = proofs[-1]["capsules"][0]["signal"] if proofs else "Unknown"
        return dict(
            signal=signal,
            action="evacuate" if signal == "Danger" else "stay",
            message=signal,
            parents=[proofs[-1]["id"]] if proofs else [],
        )


async def finish(game):
    traces = []
    while game.state.round < game.scenario.terminal_round:
        traces.append(await game.step(ReadProof()))
    return traces


def test_broadcast_control_can_evacuate_without_future_calls():
    s = next(s for s in generate(1) if s.disaster)
    game = EvidenceGame(s, "en", PACK, evidence="broadcast")
    traces = asyncio.run(finish(game))
    assert game.outcomes()["correct_action_rate"] == 1
    assert len(traces[0]["decisions"]) == 10
    assert set(traces[1]["decisions"]) == {game.source}
    assert traces[2]["decisions"] == {}
    assert all(v == 1 for i, v in game.state.evacuated.items() if i != game.source)


def test_private_proof_uses_local_next_round_delivery():
    s = next(s for s in generate(1) if s.disaster)
    text = EvidenceGame(s, "en", PACK, evidence="private", forwarding="text_only")
    proof = EvidenceGame(s, "en", PACK, evidence="private", forwarding="proof")
    first_text = asyncio.run(text.step(ReadProof()))
    first_proof = asyncio.run(proof.step(ReadProof()))
    assert first_text["views"] == first_proof["views"]
    assert first_text["decisions"] == first_proof["decisions"]
    assert text.state.evacuated == proof.state.evacuated == {proof.witness: 1}
    for i in range(10):
        if i not in {proof.witness, proof.source}:
            assert not proof.known_capsules(first_proof["views"][i]["history"])
            assert bool(proof.known_capsules(proof.view(i)["history"])) == (
                i in proof.graph[proof.witness]
            )
    asyncio.run(finish(text))
    asyncio.run(finish(proof))
    assert text.outcomes()["other_recipients_correct_action_rate"] == 0
    assert proof.outcomes()["other_recipients_correct_action_rate"] == 1
    assert proof.outcomes()["authenticated_recipients"] == 9


def test_peer_text_cannot_mint_verified_metadata():
    game = EvidenceGame(generate(1)[0], "en", PACK)
    fake = {"id": "r1-a2", "text": str({"capsules": [game.capsule]}), "signal": "Safe"}
    assert not game.known_capsules([fake])
    altered = copy.deepcopy(game.capsule)
    altered["signal"] = "Danger" if game.scenario.truth == "Safe" else "Safe"
    assert not game.known_capsules([{"capsules": [altered]}])
    with pytest.raises(InvalidDecision):
        validate(
            dict(
                signal="Safe",
                action="stay",
                message="safe",
                parents=[],
                capsules=[game.capsule],
            ),
            {"history": []},
        )


def test_verified_safe_is_not_an_evacuation_command():
    s = next(s for s in generate(1) if not s.disaster)
    game = EvidenceGame(s, "en", PACK, evidence="broadcast", forwarding="proof")
    asyncio.run(finish(game))
    assert not game.state.evacuated
    assert game.outcomes()["unnecessary_evacuation_rate"] == 0
