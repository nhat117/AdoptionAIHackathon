"""Replay verifies inputs, proof transport, outcomes and price fields."""

import asyncio
import importlib.util
import json
from dataclasses import asdict
from pathlib import Path

from swarm_lab.evacuation.dataset import generate
from swarm_lab.evacuation.evidence import EvidenceGame
from swarm_lab.evacuation.language import append

spec = importlib.util.spec_from_file_location(
    "extension_analysis",
    Path(__file__).parents[1] / "reports/overnight-experiments/analyze_extensions.py",
)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)
MODELS = {
    "sonnet": ["anthropic/claude-sonnet-5.5", "google-vertex/global", "Google", 2, 10]
}


def test_proof_transport_replays_and_missing_price_filter_is_detected(tmp_path):
    s = next(s for s in generate(1) if s.disaster and not s.accurate)
    pack = {
        "peer_label": "peer",
        "claims": {"Safe": "safe", "Danger": "danger", "Unknown": "unknown"},
    }
    game = EvidenceGame(s, "en", pack, evidence="private", forwarding="proof")
    calls = 0

    class Policy:
        async def decide(self, view):
            nonlocal calls
            calls += 1
            proof = [m for m in view["history"] if m.get("capsules")]
            signal = proof[-1]["capsules"][0]["signal"] if proof else "Unknown"
            d = dict(
                signal=signal,
                action="evacuate" if signal == "Danger" else "stay",
                message=signal,
                parents=[proof[-1]["id"]] if proof else [],
            )
            append(
                tmp_path / "calls.jsonl",
                dict(
                    type="provider_metadata",
                    model=MODELS["sonnet"][0],
                    upstream_provider="Google",
                    requested_reasoning_effort="low",
                    requested_temperature=None,
                    finish_reason="stop",
                    usage={"cost": 0.001},
                    requested_provider=dict(
                        only=["google-vertex/global"],
                        allow_fallbacks=False,
                        max_price={"prompt": 2, "completion": 10},
                    ),
                ),
            )
            append(
                tmp_path / "calls.jsonl",
                dict(type="model_response", view=view, raw=json.dumps(d)),
            )
            return d

    async def run():
        while game.state.round < s.terminal_round:
            append(tmp_path / "traces.jsonl", await game.step(Policy()))

    asyncio.run(run())
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            dict(
                id="fixture",
                section="5",
                scenario=asdict(s),
                model_tag="sonnet",
                language="en",
                arm="private_proof",
                status="completed",
                decision_attempts=calls,
            )
        )
    )
    (tmp_path / "outcome.json").write_text(json.dumps(game.outcomes()))
    row = asyncio.run(analysis.audit(tmp_path, {"en": pack}, MODELS))
    assert row["audit_errors"] == []
    assert row["outcome"]["other_recipients_correct_action_rate"] == 1
    lines = analysis.load(tmp_path / "calls.jsonl")
    next(c for c in lines if c["type"] == "provider_metadata")[
        "requested_provider"
    ].pop("max_price")
    (tmp_path / "calls.jsonl").write_text("".join(json.dumps(c) + "\n" for c in lines))
    row = asyncio.run(analysis.audit(tmp_path, {"en": pack}, MODELS))
    assert "routing_generation_mismatch" in row["audit_errors"]
