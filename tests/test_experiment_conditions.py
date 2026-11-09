"""Treatments alter only their intended input and preserve local delivery."""

import asyncio
import copy

import pytest

from swarm_lab.evacuation.conditions import (
    IDENTITIES,
    communication_graph,
    source_label,
)
from swarm_lab.evacuation.dataset import generate
from swarm_lab.evacuation.language import LanguageGame

PACK = {
    "peer_label": "ordinary teammate",
    "claims": {"Safe": "Safe claim", "Danger": "Danger claim", "Unknown": "Unknown"},
}


class Stay:
    async def decide(self, view):
        return {
            "signal": "Unknown",
            "action": "stay",
            "message": "Unknown",
            "parents": [],
        }


def test_regular_graph_connected_symmetric_reproducible():
    for seed in range(30):
        graph = communication_graph("random_regular", seed)
        assert graph == communication_graph("random_regular", seed)
        assert sum(map(len, graph.values())) == 40
        assert all(len(ns) == 4 and i not in ns for i, ns in graph.items())
        assert all(i in graph[j] for i, ns in graph.items() for j in ns)
        reached = {0}
        for _ in range(10):
            reached |= {j for i in reached for j in graph[i]}
        assert reached == set(range(10))
    assert communication_graph("random_regular", 1) != communication_graph(
        "random_regular", 2
    )


def test_identity_only_changes_controlled_source_label():
    scenario = generate(1)[0]
    baseline = LanguageGame(scenario, "en", PACK)
    original = asyncio.run(baseline.step(Stay()))
    for identity in IDENTITIES:
        game = LanguageGame(scenario, "en", PACK, identity=identity)
        trace = asyncio.run(game.step(Stay()))
        normalized = copy.deepcopy(trace)
        normalized["messages"][game.source]["source_label"] = PACK["peer_label"]
        # State hash includes delivered label; compare the visible transition fields.
        normalized.pop("state_hash")
        expected = {k: v for k, v in original.items() if k != "state_hash"}
        assert normalized == expected
        assert game.graph == baseline.graph
        assert (
            trace["messages"][game.source]["text"]
            == original["messages"][game.source]["text"]
        )
        assert trace["messages"][game.source]["authenticated"] is False


def test_random_graph_drives_both_view_and_delivery():
    game = LanguageGame(generate(1)[0], "en", PACK, topology="random_regular")
    trace = asyncio.run(game.step(Stay()))
    for agent, view in trace["views"].items():
        assert view["neighbours"] == game.graph[agent]
        received = game.view(agent)["history"]
        assert sorted(m["sender"] for m in received if "id" in m) == game.graph[agent]
    outcome = game.outcomes()
    assert outcome["adjacency"] == game.graph
    assert outcome["network_seed"] == game.scenario.seed


def test_bad_conditions_fail_before_game_calls():
    with pytest.raises(ValueError):
        LanguageGame(generate(1)[0], "en", PACK, identity="God")
    with pytest.raises(ValueError):
        communication_graph("complete", 1)
    with pytest.raises(ValueError):
        source_label("buddhist_monk", "unsupported", "peer")
