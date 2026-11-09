"""Reject incomplete plans, tampered views, outcomes and missing planned cells."""

import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from swarm_lab.evacuation.dataset import load_dataset
from swarm_lab.evacuation.evidence_v3 import EvidenceGameV3
from swarm_lab.evacuation.language import append

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location(
    "audit3", ROOT / "reports/evidence-controls-v3/audit.py"
)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@pytest.fixture
def collection(tmp_path):
    pack_path = ROOT / "data/experiment1/languages.json"
    pack = json.loads(pack_path.read_text())["en"]
    scenario = load_dataset(ROOT / "data/evidence-controls-v3/scenarios.jsonl")[0]
    jobs = audit.records(ROOT / "data/evidence-controls-v3/conditions.jsonl")
    job = next(
        j
        for j in jobs
        if j["section"] == "6" and j["arm"] == "delayed" and j["model_tag"] == "sonnet"
    )
    scenario = next(
        s
        for s in load_dataset(ROOT / "data/evidence-controls-v3/scenarios.jsonl")
        if s.id == job["scenario"]["id"]
    )
    plan = dict(
        protocol="evidence-controls-v3-corrected",
        jobs=jobs,
        source_sha256={},
        prior_ledger_sha256={},
        packs_sha256=hashlib.sha256(pack_path.read_bytes()).hexdigest(),
        prior_reported_usd={"prior": 25.5456355},
        models={"sonnet": ["test-model", "test-route", "Test", 2, 10]},
    )
    (tmp_path / "plan.json").write_text(json.dumps(plan))
    folder = tmp_path / job["id"]
    folder.mkdir()
    game = EvidenceGameV3(scenario, "en", pack, evidence="delayed")
    count = 0

    class Policy:
        async def decide(self, view):
            nonlocal count
            count += 1
            proofs = game.known_capsules(view["history"])
            signal = scenario.truth if proofs else "Unknown"
            result = dict(signal=signal, action="stay", message=signal, parents=[])
            append(
                folder / "calls.jsonl",
                dict(
                    type="provider_metadata",
                    model="test-model",
                    upstream_provider="Test",
                    requested_reasoning_effort="low",
                    requested_temperature=None,
                    requested_provider=dict(
                        only=["test-route"],
                        allow_fallbacks=False,
                        max_price=dict(prompt=2, completion=10),
                    ),
                    finish_reason="stop",
                    usage=dict(cost=0.001),
                ),
            )
            append(
                folder / "calls.jsonl",
                dict(type="model_response", view=view, raw=json.dumps(result)),
            )
            ticket = f"{job['id']}:{count}"
            append(
                tmp_path / "budget.jsonl", dict(type="reserve", ticket=ticket, usd=0.2)
            )
            append(
                tmp_path / "budget.jsonl",
                dict(type="settle", ticket=ticket, cost=0.001),
            )
            return result

    async def play():
        while game.state.round < scenario.terminal_round:
            append(folder / "traces.jsonl", await game.step(Policy()))

    asyncio.run(play())
    (folder / "outcome.json").write_text(json.dumps(game.outcomes()))
    (folder / "manifest.json").write_text(
        json.dumps(
            dict(
                job,
                status="completed",
                decision_attempts=count,
                protocol=plan["protocol"],
            )
        )
    )
    return tmp_path, folder


def test_full_replay_and_unattempted_enumeration(collection):
    root, _ = collection
    games, missing, audits, budget, _ = audit.collect(root)
    assert len(games) == len(audits) == 1
    assert len(missing) == 71
    assert all(row["status"] == "unattempted" for row in missing)
    assert budget["total_usd"] < 35 and not budget["pending"]
    rows = audits[0]["timing"]
    assert all(r["first_authenticated_decision"] == 3 for r in rows)


@pytest.mark.parametrize("target", ["view", "outcome", "manifest"])
def test_tampered_records_rejected(collection, target):
    root, folder = collection
    if target == "view":
        path = folder / "calls.jsonl"
        rows = audit.records(path)
        next(r for r in rows if r["type"] == "model_response")["view"]["round"] = 99
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    else:
        path = folder / (target + ".json")
        data = json.loads(path.read_text())
        data["correct_action_rate" if target == "outcome" else "arm"] = "tampered"
        path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        audit.collect(root)


def test_missing_or_empty_plan_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        audit.collect(tmp_path)
    (tmp_path / "plan.json").write_text(
        json.dumps(dict(protocol="evidence-controls-v3-corrected", jobs=[]))
    )
    with pytest.raises(ValueError):
        audit.collect(tmp_path)
