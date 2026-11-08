"""Budget, frozen pairing and upstream routing safety checks."""

import asyncio
import importlib.util
import io
import json
from pathlib import Path

import pytest

from swarm_lab.evacuation.openrouter import OpenRouterBackend
from swarm_lab.settings import AgentSettings, Settings

spec = importlib.util.spec_from_file_location(
    "overnight", Path(__file__).parents[1] / "reports/overnight-experiments/run.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_paired_jobs_have_complete_unique_cells():
    jobs = runner.jobs()
    assert len(jobs) == len({j["id"] for j in jobs}) == 72
    assert [sum(j["section"] == s for j in jobs) for s in (1, 2, 3)] == [16, 40, 16]
    baseline = {(j["scenario"]["id"], j["language"]) for j in jobs if j["section"] == 1}
    assert all((j["scenario"]["id"], j["language"]) in baseline for j in jobs)
    sources = {j["scenario"]["informant"] for j in jobs if j["section"] == 3}
    assert len(sources) == 2


def test_budget_reserves_before_call_and_retains_uncertain_billing(tmp_path):
    b = runner.Budget(tmp_path)
    b.reserve("one", {"provider": {}})
    resumed = runner.Budget(tmp_path)
    with pytest.raises(RuntimeError):
        resumed.reserve("two", {"provider": {}})
    b.settle(
        "one",
        {
            "usage": {"cost": 0.1},
            "upstream_provider": "Google",
            "requested_reasoning_effort": "low",
        },
    )
    resumed = runner.Budget(tmp_path)
    assert resumed.spent == 0.1
    assert not resumed.pending
    resumed.spent = 34.9
    with pytest.raises(RuntimeError):
        resumed.reserve("two", {"provider": {}})


def test_missing_cost_or_wrong_provider_halts(tmp_path):
    b = runner.Budget(tmp_path)
    b.reserve("one", {"provider": {}})
    with pytest.raises(RuntimeError):
        b.settle(
            "one",
            {
                "usage": {"cost": 0.01},
                "upstream_provider": "Other",
                "requested_reasoning_effort": "low",
            },
        )
    assert b.halted
    assert b.pending


def test_backend_pins_endpoint_and_reserves_before_network(monkeypatch):
    ordered = []

    def before(payload):
        assert payload["provider"]["only"] == ["google-vertex/global"]
        assert payload["provider"]["allow_fallbacks"] is False
        assert payload["reasoning"] == {"effort": "low"}
        payload["provider"]["max_price"] = {"prompt": 2, "completion": 10}
        ordered.append("reserved")

    def network(request, timeout):
        assert json.loads(request.data)["provider"]["max_price"] == {
            "prompt": 2,
            "completion": 10,
        }
        assert ordered == ["reserved"]
        ordered.append("requested")
        return io.BytesIO(
            json.dumps(
                {"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}
            ).encode()
        )

    monkeypatch.setattr("urllib.request.urlopen", network)
    b = OpenRouterBackend(
        "fake",
        Settings(),
        lambda _: None,
        reasoning_effort="low",
        provider_only="google-vertex/global",
        before_request=before,
    )
    assert asyncio.run(b.generate(AgentSettings(), "view")) == "{}"
    assert ordered == ["reserved", "requested"]
