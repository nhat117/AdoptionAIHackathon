import asyncio
import json
from dataclasses import replace

import httpx
import pytest
from adaption import AsyncAdaption

from swarm_lab.backend import AdaptionBackend, OfflineBackend
from swarm_lab.events import EventLog
from swarm_lab.graph import build_graph
from swarm_lab.nodes import Nodes
from swarm_lab.settings import AgentSettings, Settings


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_offline_run_join_logs_and_fresh_state(tmp_path, monkeypatch):
    monkeypatch.delenv("ADAPTION_API_KEY", raising=False)
    settings = replace(
        Settings(),
        branch_a=AgentSettings(offline_output="A"),
        branch_b=AgentSettings(offline_output="B"),
    )
    path = tmp_path / "events.jsonl"
    for task in ("first", "second"):
        events = EventLog(path)
        graph = build_graph(Nodes(OfflineBackend(), settings, events))
        state = asyncio.run(graph.ainvoke({"task": task}))
        assert state["prepared_input"] == task
        assert state["final_output"] == "Branch A:\nA\n\nBranch B:\nB"
    log = records(path)
    assert len({entry["run_id"] for entry in log}) == 2
    for run_id in {entry["run_id"] for entry in log}:
        subset = [entry for entry in log if entry["run_id"] == run_id]
        completed = [
            entry["node"] for entry in subset if entry["event"] == "node_completed"
        ]
        assert completed.index("combine") > completed.index("branch_a")
        assert completed.index("combine") > completed.index("branch_b")
        assert completed[-1] == "finish"


def test_parallel_branches_receive_only_prepared_input(tmp_path):
    class RecordingBackend:
        def __init__(self):
            self.calls = []
            self.both_started = asyncio.Event()

        async def generate(self, agent, input_text):
            self.calls.append(input_text)
            if len(self.calls) == 2:
                self.both_started.set()
            # Would time out if the graph accidentally serialized the branches.
            await asyncio.wait_for(self.both_started.wait(), timeout=3)
            return "result"

    async def scenario():
        backend = RecordingBackend()
        nodes = Nodes(backend, Settings(), EventLog(tmp_path / "log.jsonl"))
        graph = build_graph(nodes)
        await graph.ainvoke({"task": "only this", "final_output": "not model input"})
        assert backend.calls == ["only this", "only this"]

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "status, text",
    [("completed", "raw answer"), ("incomplete", "partial"), ("completed", "")],
)
def test_adaption_request_boundary_with_real_sdk(status, text):
    async def scenario():
        def handler(request):
            body = json.loads(request.content)
            assert body["instructions"] == "custom instruction"
            assert body["input"] == "selected input"
            assert body["agentic_memory"] is False
            assert body["store"] is False
            assert "previous_response_id" not in body
            assert body["model"] == Settings().model
            return httpx.Response(
                200,
                json={
                    "id": "test",
                    "object": "response",
                    "status": status,
                    "output_text": text,
                    "model": "test-model",
                    "output": [
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": "raw answer"}],
                        }
                    ],
                },
            )

        async with AsyncAdaption(
            api_key="test-key",
            max_retries=0,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        ) as client:
            backend = AdaptionBackend(client, Settings())
            if status == "completed" and text:
                output = await backend.generate(
                    AgentSettings(instructions="custom instruction"), "selected input"
                )
                assert output == text
            else:
                with pytest.raises(RuntimeError):
                    await backend.generate(
                        AgentSettings(instructions="custom instruction"),
                        "selected input",
                    )

    asyncio.run(scenario())


def test_failed_response_is_not_a_completed_node(tmp_path):
    class BrokenBackend:
        async def generate(self, agent, input_text):
            raise RuntimeError("private provider detail")

    path = tmp_path / "log.jsonl"
    graph = build_graph(Nodes(BrokenBackend(), Settings(), EventLog(path)))
    with pytest.raises(RuntimeError):
        asyncio.run(graph.ainvoke({"task": "test"}))
    completed = [
        entry["node"] for entry in records(path) if entry["event"] == "node_completed"
    ]
    assert completed == ["prepare"]
    assert "private provider detail" not in path.read_text()


@pytest.mark.parametrize(
    "payload",
    [
        {"typo": True},
        {"max_output_tokens": 0},
        {"temperature": 3},
        {"model": ""},
        {"branch_a": {"instructions": 42}},
    ],
)
def test_invalid_settings(tmp_path, payload):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload))
    with pytest.raises((ValueError, TypeError)):
        Settings.load(path)
