"""v4 influence game, stance rule, and the frozen v4 design and analysis."""

import asyncio
import importlib.util
import json
from pathlib import Path

import pytest

from swarm_lab.evacuation.dataset import load_dataset
from swarm_lab.evacuation.engine import InvalidDecision
from swarm_lab.evacuation.influence import (
    WARNING,
    InfluenceGame,
    instructions,
    pack,
    split_belief,
)
from swarm_lab.evacuation.stance import cohen_kappa, stance

ROOT = Path(__file__).parents[1]
CLAIMS = {"Danger": "Danger", "Safe": "Safe", "Unknown": "Unknown"}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


run = module("reports/influence-v4/run.py", "v4run")
analyze = module("reports/influence-v4/analyze.py", "v4analyze")
SCENARIOS = load_dataset(ROOT / "data/influence-v4/scenarios.jsonl")


class TrustsAgency:
    """Fixture: sensor-based belief, moved to the claim only by the agency."""

    def __init__(self, label):
        self.label = label

    async def decide(self, view):
        history = view["history"]
        sensor = next(m for m in history if m.get("sender") == "own_sensor")
        belief = 70 if sensor["signal"] == "Danger" else 30
        source = [m for m in history if m.get("source_label") == self.label]
        if source and self.label == "official emergency management agency":
            belief = 90 if source[-1]["signal"] == "Danger" else 10
        signal = "Danger" if belief > 50 else "Safe"
        return dict(
            signal=signal,
            action="stay",  # Keep everyone in play so every round has a belief.
            message=signal,
            parents=[],
            belief=belief,
        )


def play(scenario, authority, warning):
    game = InfluenceGame(
        scenario, "en", pack(warning, CLAIMS), authority=authority, warning=warning
    )
    policy = TrustsAgency(game.claimed_source_label)
    while game.state.round < scenario.terminal_round:
        asyncio.run(game.step(policy))
    return game


def test_warning_arms_differ_by_exactly_one_sentence():
    assert instructions(True).replace(" " + WARNING, "") == instructions(False)
    assert WARNING not in instructions(False)


def test_clues_are_private_matched_across_arms_and_hide_truth():
    s = SCENARIOS[0]
    a = InfluenceGame(s, "en", pack(True, CLAIMS), authority="teammate")
    b = InfluenceGame(
        s, "en", pack(False, CLAIMS), authority="emergency_agency", warning=False
    )
    assert a.clues == b.clues and a.source not in a.clues
    for i, clue in a.clues.items():
        own = [m for m in a.view(i)["history"] if m.get("sender") == "own_sensor"]
        assert [m["signal"] for m in own] == [clue] and own[0]["accuracy"] == 0.7
    assert "disaster" not in json.dumps(a.view(a.source)["history"]).lower()


@pytest.mark.parametrize("bad", [101, -1, "50", 50.5, True])
def test_belief_must_be_an_integer_percentage(bad):
    with pytest.raises(InvalidDecision):
        split_belief(
            dict(signal="Safe", action="stay", message="x", parents=[], belief=bad)
        )


def test_belief_shift_and_tipping_follow_the_trusted_source():
    s = next(x for x in SCENARIOS if not x.accurate)
    trusted = play(s, "emergency_agency", True).outcomes()
    ignored = play(s, "teammate", True).outcomes()
    assert trusted["exposed_with_baseline"] == 4
    assert trusted["mean_belief_shift_toward_claim"] > 0
    assert ignored["mean_belief_shift_toward_claim"] == 0
    assert set(trusted["beliefs"]) >= {f"1-{i}" for i in trusted["clues"]}


def test_analysis_finds_the_planted_authority_effect():
    games = {}
    for s in SCENARIOS:
        for authority in ("teammate", "emergency_agency"):
            for warning in (True, False):
                out = play(s, authority, warning).outcomes()
                games["sonnet", s.id, authority, warning] = dict(
                    out, seed=s.seed, claim_true=s.accurate
                )
    res = analyze.analyse(games, [])["sonnet"][analyze.PRIMARY]
    effect = res["authority_with_warning"]
    assert effect["complete_units"] == 16 and effect["mean"] > 0
    assert effect["exact_sign_flip_p"] < 0.001
    assert res["interaction"]["mean"] == 0  # Fixture ignores the warning.


def test_v4_design_is_balanced_held_out_and_needs_a_cap(tmp_path):
    jobs = run.jobs()
    assert len(jobs) == len({j["id"] for j in jobs}) == 256
    for tier, levels in run.TIERS.items():
        cells = {}
        for j in jobs:
            if j["section"] == tier:
                key = j["model_tag"], j["scenario"]["id"]
                cells.setdefault(key, set()).add((j["authority"], j["warning"]))
        assert len(cells) == 32
        assert all(
            c == {(lv, w) for lv in levels for w in (True, False)}
            for c in cells.values()
        )
    v3 = load_dataset(ROOT / "data/evidence-controls-v3/scenarios.jsonl")
    assert not {s.seed for s in SCENARIOS} & {s.seed for s in v3}
    args = type(
        "A",
        (),
        dict(
            cap_usd=None, tier="pilot", model=None, plan_only=False, root=tmp_path / "r"
        ),
    )
    with pytest.raises(ValueError, match="cap-usd"):
        asyncio.run(run.main(args))
    assert not (tmp_path / "r").exists()


def test_stance_rule_separates_requests_from_absence():
    unknown = lambda t: stance(dict(signal="Unknown", text=t), "Danger")  # noqa: E731
    assert stance(dict(signal="Danger", text=""), "Danger") == "agrees"
    assert stance(dict(signal="Safe", text=""), "Danger") == "disagrees"
    assert (
        unknown("Please share any independent confirmation with IDs.") == "asks_proof"
    )
    assert unknown("Round 1: no messages and no evidence of a disaster.") == "neutral"
    assert unknown("Agent 6's claim is unverified, with no cited source.") == "neutral"
    assert unknown("Bạn có bằng chứng không?") == "asks_proof"
    assert unknown("Chưa có bằng chứng về thảm họa.") == "neutral"


def test_kappa_matches_hand_computation():
    assert cohen_kappa(["agrees"] * 4, ["agrees"] * 4) == 1.0
    a = ["agrees", "agrees", "neutral", "neutral"]
    b = ["agrees", "neutral", "neutral", "neutral"]
    assert cohen_kappa(a, b) == pytest.approx(0.5)


def test_few_pairs_are_inconclusive():
    games = {}
    for s in SCENARIOS[:3]:
        for authority in ("teammate", "emergency_agency"):
            out = play(s, authority, True).outcomes()
            games["terra", s.id, authority, True] = dict(
                out, seed=s.seed, claim_true=s.accurate
            )
    res = analyze.analyse(games, [])["terra"][analyze.PRIMARY]
    assert res["authority_with_warning"]["status"] == "inconclusive"
