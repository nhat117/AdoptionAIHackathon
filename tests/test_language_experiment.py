"""Protocol checks for the new language experiment, not model findings."""

import asyncio
import copy
import json
from argparse import Namespace

import pytest

from swarm_lab.evacuation.dataset import generate
from swarm_lab.evacuation.engine import InvalidDecision, neighbours
from swarm_lab.evacuation.language import LanguageGame, run, validate

PACK = {
    "review_status": "pending",
    "instructions": "Fixture instructions",
    "peer_label": "ordinary teammate",
    "claims": {
        "Safe": "It is safe.",
        "Danger": "There is danger.",
        "Unknown": "Unknown.",
    },
}


def scenario():
    return next(s for s in generate(1) if s.disaster and s.accurate)


class StayPolicy:
    def __init__(self, evacuate=None):
        self.views = []
        self.evacuate = evacuate

    async def decide(self, view):
        self.views.append(copy.deepcopy(view))
        return {
            "signal": "Unknown",
            "action": "evacuate" if view["agent"] == self.evacuate else "stay",
            "message": "I do not yet have verified information.",
            "parents": [],
        }


def test_no_global_state_or_remote_history_in_local_view():
    game = LanguageGame(scenario(), "en", PACK)
    recipient = (game.source + 1) % 10
    game.state.histories[game.source].append({"secret": "hidden source information"})
    view = game.view(recipient)
    serialized = json.dumps(view)
    assert view.get("private_observation") is None
    assert "terminal_round" not in serialized
    assert "hidden source information" not in serialized
    assert "disaster" not in view
    view["history"].append({"tamper": True})
    assert game.state.histories[recipient] == []


def test_all_four_neighbours_receive_on_next_round_and_source_stops():
    async def check():
        game = LanguageGame(scenario(), "en", PACK)
        policy = StayPolicy()
        await game.step(policy)
        assert len(policy.views) == 9
        assert all(v["history"] == [] for v in policy.views)
        for recipient in range(10):
            if recipient == game.source:
                continue
            received = {
                e["sender"] for e in game.state.histories[recipient] if "id" in e
            }
            assert received == set(neighbours(recipient))
        await game.step(policy)
        assert all(v["agent"] != game.source for v in policy.views)
        await game.step(policy)
        for recipient in range(10):
            assert not any(
                e.get("id") == f"r3-a{game.source}"
                for e in game.state.histories[recipient]
            )
        assert all(v["agent"] != game.source for v in policy.views)

    asyncio.run(check())


def test_evacuation_is_final_but_last_message_is_sent():
    async def check():
        game = LanguageGame(scenario(), "en", PACK)
        departing = (game.source + 1) % 10
        policy = StayPolicy(evacuate=departing)
        await game.step(policy)
        assert game.state.evacuated[departing] == 1
        for recipient in neighbours(departing):
            if recipient == game.source:
                continue
            assert any(
                e.get("id") == f"r1-a{departing}"
                for e in game.state.histories[recipient]
            )
        await game.step(policy)
        assert sum(v["agent"] == departing for v in policy.views) == 1
        assert not any(
            e.get("id") == f"r2-a{departing}"
            for history in game.state.histories.values()
            for e in history
        )

    asyncio.run(check())


def test_language_pairs_keep_scenario_and_outcome_denominator():
    async def check():
        outcomes = []
        for language in ("en", "vi"):
            pack = copy.deepcopy(PACK)
            if language == "vi":
                pack["claims"]["Danger"] = "Có nguy hiểm."
                pack["peer_label"] = "đồng đội"
            game = LanguageGame(scenario(), language, pack)
            policy = StayPolicy()
            for _ in range(scenario().terminal_round):
                await game.step(policy)
            outcomes.append(game.outcomes())
            assert outcomes[-1]["missed_evacuation_rate"] == 1.0
            assert outcomes[-1]["correct_action_rate"] == 0.0
        for key in ("missed_evacuation_rate", "correct_action_rate", "total_payoff"):
            assert outcomes[0][key] == outcomes[1][key]

    asyncio.run(check())


@pytest.mark.parametrize(
    "changes",
    [
        {"message": "字" * 401},
        {"message": " " * 400 + "字"},
        {"message": ""},
        {"parents": ["unreceived-id"]},
        {"parents": ["r1-a1", "r1-a1"]},
        {"listen_to": [1, 2]},
    ],
)
def test_invalid_message_or_provenance_rejected(changes):
    view = {"history": [{"id": "r1-a1"}]}
    data = {"signal": "Unknown", "action": "stay", "message": "等待。", "parents": []}
    data.update(changes)
    with pytest.raises((InvalidDecision, ValueError)):
        validate(data, view)


def test_character_limit_counts_unicode_characters_not_utf8_bytes():
    data = {"signal": "Unknown", "action": "stay", "message": "字" * 400, "parents": []}
    validate(data, {"history": []})


def test_controlled_source_is_excluded_from_primary_rates():
    game = LanguageGame(scenario(), "en", PACK)
    game.state.evacuated = {i: 1 for i in range(10) if i != game.source}
    assert game.outcomes()["missed_evacuation_rate"] == 0.0
    assert game.outcomes()["correct_action_rate"] == 1.0


@pytest.mark.parametrize(
    "split, allow_unreviewed",
    [("evaluation", False), ("evaluation", True), ("calibration", False)],
)
def test_draft_live_packs_rejected_before_network_or_output(
    tmp_path, monkeypatch, split, allow_unreviewed
):
    packs = tmp_path / "packs.json"
    packs.write_text(json.dumps({"en": PACK}))
    output = tmp_path / "not-created"
    args = Namespace(
        packs=packs,
        languages=["en"],
        limit=1,
        max_calls=100,
        mode="live",
        split=split,
        allow_unreviewed=allow_unreviewed,
        dataset=tmp_path / "not-read.jsonl",
        output=output,
        provider="adaption",
        model="qwen3.8-27b",
    )

    def forbidden_network(*args, **kwargs):
        pytest.fail("Unreviewed packs must be rejected before creating an API client")

    monkeypatch.setattr(
        "swarm_lab.evacuation.language.AsyncAdaption", forbidden_network
    )
    with pytest.raises(ValueError, match="Draft packs require calibration"):
        asyncio.run(run(args))
    assert not output.exists()
