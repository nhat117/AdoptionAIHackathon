import asyncio
import copy
import json

import pytest

from swarm_lab.evacuation.dataset import generate, load_dataset, write_dataset
from swarm_lab.evacuation.engine import (
    Game,
    InvalidDecision,
    neighbours,
    state_hash,
    validate_decision,
)
from swarm_lab.evacuation.policies import FixturePolicy, LivePolicy


def scenario(disaster=True, accurate=True):
    return next(
        s for s in generate(1) if s.disaster == disaster and s.accurate == accurate
    )


class StayPolicy:
    def __init__(self):
        self.views = []

    async def decide(self, view):
        self.views.append(copy.deepcopy(view))
        return {
            "signal": "Unknown",
            "action": "stay",
            "listen_to": view["neighbours"][-2:],
            "parents": [],
        }


def test_dataset_reproducible_balanced_and_roundtrip(tmp_path):
    rows = generate()
    assert rows == generate()
    for split in ("calibration", "evaluation"):
        subset = [s for s in rows if s.split == split]
        for truth in (False, True):
            for accuracy in (False, True):
                assert (
                    sum(s.disaster == truth and s.accurate == accuracy for s in subset)
                    == 5
                )
    assert not (
        {s.seed for s in rows if s.split == "calibration"}
        & {s.seed for s in rows if s.split == "evaluation"}
    )
    path = tmp_path / "rows.jsonl"
    write_dataset(path, rows)
    assert load_dataset(path) == rows


def test_views_do_not_leak_truth_horizon_or_remote_history():
    game = Game(scenario(), "A", "once_fixed")
    other = (game.source + 1) % 10
    game.state.histories[game.source].append({"secret": "private detail"})
    view = game.view(other)
    assert view["private_observation"] is None
    assert "terminal_round" not in json.dumps(view)
    assert "private detail" not in json.dumps(view)
    view["history"].append({"tamper": True})
    assert not game.state.histories[other]


def test_synchronous_local_delivery_and_irreversible_exit():
    async def check():
        game = Game(scenario(), "A", "repeated_fixed")
        policy = StayPolicy()
        await game.step(policy)
        assert all(v["history"] == [] for v in policy.views)
        for i in range(10):
            delivered = {e["sender"] for e in game.state.histories[i] if "id" in e}
            assert delivered == set(neighbours(i))
        departed = (game.source + 1) % 10
        game.state.evacuated[departed] = 1
        trace = await game.step(policy)
        assert departed not in trace["decisions"]
        assert game.state.evacuated[departed] == 1

    asyncio.run(check())


def test_chosen_reception_uses_previous_round_selection():
    async def check():
        game = Game(scenario(), "A", "repeated_chosen")
        policy = StayPolicy()
        await game.step(policy)
        await game.step(policy)
        for event in game.state.events:
            if event["round"] == 2 and event["recipient"] != game.source:
                assert event["selected"] == neighbours(event["recipient"])[-2:]

    asyncio.run(check())


def test_c_forks_share_exposure_without_mutating_snapshot():
    async def check():
        base = Game(scenario(accurate=False), "C", "none")
        for _ in range(2):
            await base.step(StayPolicy())
        original = state_hash(base.state)
        removed, corrected = base.fork("remove"), base.fork("correction")
        assert state_hash(base.state) == original
        assert base.source not in base.state.disabled
        assert base.source in removed.state.disabled
        for i in range(10):
            corrections = [
                e
                for e in corrected.state.histories[i]
                if e.get("id") == "verified-correction"
            ]
            assert bool(corrections) == (i in neighbours(base.source))
            # Source removal must not erase already delivered claims.
            assert removed.state.histories[i][:-1] == base.state.histories[i]
        trace = await removed.step(StayPolicy())
        assert base.source not in trace["messages"]
        assert base.state.round == 2

    asyncio.run(check())


@pytest.mark.parametrize("disaster", [False, True])
def test_payoffs_include_other_correct_agents_only(disaster):
    game = Game(scenario(disaster), "A", "once_fixed")
    game.state.evacuated = {0: 1}
    outcomes = game.outcomes()
    if disaster:
        assert outcomes["payoffs"][0] == 1
        assert outcomes["payoffs"][1] == 0
    else:
        assert outcomes["payoffs"][0] == pytest.approx(1.9)
        assert outcomes["payoffs"][1] == pytest.approx(2.8)


@pytest.mark.parametrize(
    "change",
    [
        {"listen_to": [True, 2]},
        {"listen_to": [1, 1]},
        {"parents": ["unseen"]},
        {"action": "wait"},
        {"extra": 1},
    ],
)
def test_invalid_actions_rejected(change):
    game = Game(scenario(), "A", "once_fixed")
    view = game.view(0)
    decision = {
        "signal": "Safe",
        "action": "stay",
        "listen_to": view["neighbours"][:2],
        "parents": [],
    }
    decision.update(change)
    with pytest.raises(InvalidDecision):
        validate_decision(decision, view)


def test_live_budget_stops_before_extra_request():
    class Backend:
        calls = 0

        async def generate(self, agent, input_text):
            self.calls += 1
            return json.dumps(await FixturePolicy().decide(json.loads(input_text)))

    async def check():
        backend = Backend()
        policy = LivePolicy(backend, 1, lambda _: None)
        view = Game(scenario(), "A", "once_fixed").view(0)
        await policy.decide(view)
        with pytest.raises(RuntimeError, match="limit"):
            await policy.decide(view)
        assert backend.calls == 1

    asyncio.run(check())


def test_unreviewed_invented_stimuli_cannot_enter_evaluation(tmp_path):
    from swarm_lab.evacuation.stimuli import load_stimulus

    path = tmp_path / "stimuli.jsonl"
    pair = {
        "safe_message": "No disaster will occur here; I recommend that we stay.",
        "danger_message": "A disaster will occur; I recommend we evacuate now.",
        "review_status": "pending",
    }
    path.write_text(json.dumps(pair) + "\n")
    with pytest.raises(ValueError, match="calibration-only"):
        load_stimulus(path, 0, "evaluation", allow_unreviewed=True)
    assert load_stimulus(path, 0, "calibration", True)["safe_message"]


def test_fenced_json_accepted_without_accepting_surrounding_prose():
    class Backend:
        raw = '```json\n{"signal":"Safe"}\n```'

        async def generate(self, *_):
            return self.raw

    async def check():
        backend = Backend()
        policy = LivePolicy(backend, 2, lambda _: None)
        assert await policy.decide({}) == {"signal": "Safe"}
        backend.raw = 'Here is my response: {"signal":"Safe"}'
        with pytest.raises(InvalidDecision):
            await policy.decide({})

    asyncio.run(check())


def test_generated_text_reaches_only_local_recipients():
    async def check():
        pair = {
            "safe_message": "No disaster will occur here; I recommend that we stay.",
            "danger_message": "A disaster will occur; I recommend we evacuate now.",
        }
        game = Game(scenario(), "A", "once_fixed", pair)
        await game.step(StayPolicy())
        for agent in range(10):
            texts = [e["text"] for e in game.state.histories[agent] if "text" in e]
            assert texts == (
                [pair["danger_message"]] if agent in neighbours(game.source) else []
            )

    asyncio.run(check())


def test_invent_conversion_preserves_pending_and_rejections(tmp_path):
    from swarm_lab.evacuation.stimuli import convert

    pair = {
        "safe_message": "No disaster will occur here; I recommend that we stay.",
        "danger_message": "A disaster will occur; I recommend we evacuate now.",
    }
    row = json.dumps({"completion": json.dumps(pair)})
    source, target = tmp_path / "raw.jsonl", tmp_path / "pairs.jsonl"
    source.write_text(row + "\n" + row + '\n{"completion":"bad"}\n')
    assert convert(source, target) == (1, 2)
    assert json.loads(target.read_text())["review_status"] == "pending"
    assert len(json.loads(target.with_suffix(".rejected.json").read_text())) == 2


def test_openrouter_request_boundary_and_usage(monkeypatch):
    import io
    import urllib.request

    from swarm_lab.evacuation.openrouter import OpenRouterBackend
    from swarm_lab.settings import AgentSettings, Settings

    records = []

    def fake_open(request, timeout):
        body = json.loads(request.data)
        assert request.full_url == "https://openrouter.ai/api/v1/chat/completions"
        assert body["model"] == "openai/gpt-4.1-mini"
        assert body["messages"][0]["content"] == "instruction"
        assert body["messages"][1]["content"] == "local view"
        assert body["provider"]["allow_fallbacks"] is False
        assert "tools" not in body
        return io.BytesIO(
            json.dumps(
                {
                    "id": "test",
                    "model": body["model"],
                    "provider": "test-provider",
                    "usage": {"cost": 0.0001},
                    "choices": [
                        {"finish_reason": "stop", "message": {"content": "{}"}}
                    ],
                }
            ).encode()
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_open)
    backend = OpenRouterBackend(
        "test-secret", Settings(model="openai/gpt-4.1-mini"), records.append
    )
    assert (
        asyncio.run(
            backend.generate(AgentSettings(instructions="instruction"), "local view")
        )
        == "{}"
    )
    assert records[0]["usage"]["cost"] == 0.0001
    assert "test-secret" not in json.dumps(records)
