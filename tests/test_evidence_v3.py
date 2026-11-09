"""Unverified-capsule and delayed-truth controls, plus the frozen v3 design."""

import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path

from swarm_lab.evacuation.dataset import load_dataset
from swarm_lab.evacuation.evidence_v3 import EvidenceGameV3

ROOT = Path(__file__).parents[1]
PACK = {
    "peer_label": "ordinary teammate",
    "claims": {"Danger": "Danger", "Safe": "Safe", "Unknown": "Unknown"},
}
spec = importlib.util.spec_from_file_location(
    "v3run", ROOT / "reports/evidence-controls-v3/run.py"
)
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class ReadCapsule:
    """Acts on the newest capsule; optionally only when it is authenticated."""

    def __init__(self, require_authenticated):
        self.require_authenticated = require_authenticated

    async def decide(self, view):
        proofs = [
            m
            for m in view["history"]
            if any(
                c["authenticated"] or not self.require_authenticated
                for c in m.get("capsules", [])
            )
        ]
        signal = proofs[-1]["capsules"][0]["signal"] if proofs else "Unknown"
        return dict(
            signal=signal,
            action="evacuate" if signal == "Danger" else "stay",
            message=signal,
            parents=[proofs[-1]["id"]] if proofs else [],
        )


def scenario(disaster):
    rows = load_dataset(ROOT / "data/evidence-controls-v3/scenarios.jsonl")
    return next(s for s in rows if s.disaster == disaster)


def play(game, policy):
    traces = []
    while game.state.round < game.scenario.terminal_round:
        traces.append(asyncio.run(game.step(policy)))
    return traces


def test_unverified_capsules_match_proof_except_the_flag():
    s = scenario(True)
    proof = EvidenceGameV3(s, "en", PACK, evidence="private", forwarding="proof")
    fake = EvidenceGameV3(s, "en", PACK, evidence="private", forwarding="unverified")
    credulous = ReadCapsule(require_authenticated=False)
    a, b = play(proof, credulous), play(fake, credulous)
    for ta, tb in zip(a, b):
        assert ta["decisions"] == tb["decisions"]
        for ma, mb in zip(ta["messages"].values(), tb["messages"].values()):
            caps_a, caps_b = ma.pop("capsules", []), mb.pop("capsules", [])
            assert ma == mb
            assert [dict(c, authenticated=False) for c in caps_a] == caps_b
    # Relayed beyond the witness's neighbours, as in the proof arm.
    assert fake.outcomes()["unverified_recipients"] == 8
    assert proof.outcomes()["authenticated_recipients"] == 9
    assert fake.outcomes()["authenticated_recipients"] == 1  # Witness only.


def test_flag_checking_policy_treats_unverified_like_text_only():
    s = scenario(True)
    strict = ReadCapsule(require_authenticated=True)
    text = EvidenceGameV3(s, "en", PACK, evidence="private", forwarding="text_only")
    fake = EvidenceGameV3(s, "en", PACK, evidence="private", forwarding="unverified")
    proof = EvidenceGameV3(s, "en", PACK, evidence="private", forwarding="proof")
    for game in (text, fake, proof):
        play(game, strict)
    rate = "other_recipients_correct_action_rate"
    assert text.outcomes()[rate] == fake.outcomes()[rate] == 0
    assert proof.outcomes()[rate] == 1


def test_delayed_truth_arrives_after_round_two_and_counts_reversals():
    s = scenario(True)
    game = EvidenceGameV3(s, "en", PACK, evidence="delayed")
    traces = play(game, ReadCapsule(require_authenticated=True))
    first = traces[0]["views"]
    assert not any(
        m.get("sender") == "simulator" for v in first.values() for m in v["history"]
    )
    second = traces[1]["views"]
    assert not any(
        m.get("sender") == "simulator" for v in second.values() for m in v["history"]
    )
    assert any(
        m.get("sender") == game.source for v in second.values() for m in v["history"]
    )
    third = traces[2]["views"]
    assert all(
        any(m.get("sender") == "simulator" for m in third[i]["history"])
        for i in third
        if i != game.source
    )
    out = game.outcomes()
    assert len(out["exposed_wrong_before_truth"]) == 4
    assert out["exposed_wrong_stays_then_evacuated"] == 4
    assert out["correct_action_rate"] == 1


def test_delayed_truth_under_safe_reports_irreversible_errors_separately():
    s = scenario(False)
    game = EvidenceGameV3(s, "en", PACK, evidence="delayed")
    play(game, ReadCapsule(require_authenticated=True))
    out = game.outcomes()
    assert out["exposed_wrong_stays_then_evacuated"] == 0
    assert out["irreversible_before_truth_errors"] == 0
    assert out["unnecessary_evacuation_rate"] == 0


def test_v3_design_is_balanced_and_held_out():
    jobs = run.jobs()
    assert len(jobs) == len({j["id"] for j in jobs}) == 72
    assert {s: sum(j["section"] == s for j in jobs) for s in run.ARMS} == {
        "5b": 48,
        "6": 24,
    }
    for section, arms in run.ARMS.items():
        groups = {}
        for j in jobs:
            if j["section"] == section:
                key = j["model_tag"], j["scenario"]["id"]
                groups.setdefault(key, set()).add(j["arm"])
                assert j["scenario"]["split"] == "evaluation"
                assert not j["scenario"]["accurate"]
        assert all(g == set(arms) for g in groups.values())
    assert (
        len(
            {
                (j["model_tag"], j["scenario"]["seed"])
                for j in jobs
                if j["section"] == "5b"
            }
        )
        == 16
    )


def test_frozen_v2_sources_are_untouched():
    plan = json.loads(
        (ROOT / "reports/overnight-experiments/extension-plan.json").read_text()
    )
    for path, expected in plan["source_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected


def test_false_claim_decision_can_precede_truth_and_exit_is_irreversible():
    s = scenario(False)
    game = EvidenceGameV3(s, "en", PACK, evidence="delayed")

    class FollowSource:
        async def decide(self, view):
            known = game.known_capsules(view["history"])
            source = [m for m in view["history"] if m.get("sender") == game.source]
            signal = s.truth if known else s.claim if source else "Unknown"
            return dict(
                signal=signal,
                action="evacuate" if signal == "Danger" else "stay",
                message=signal,
                parents=[],
            )

    traces = play(game, FollowSource())
    out = game.outcomes()
    exposed = out["false_source_exposed_before_truth"]
    assert len(exposed) == 4 and out["irreversible_before_truth_errors"] == 4
    assert out["exposed_wrong_before_truth"] == exposed
    assert all(i not in traces[2]["views"] for i in exposed)
    assert out["correct_action_rate"] == 5 / 9


def test_capsule_prompt_is_not_unconditionally_authenticated():
    instructions = run.EVIDENCE_INSTRUCTIONS_V3
    assert "is checked by the simulator and reports" not in instructions
    assert "authenticated field is true" in instructions
