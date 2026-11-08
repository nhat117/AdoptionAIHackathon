"""A disputed citation counts as traceable exposure, never endorsement."""

import importlib.util
import json
from pathlib import Path

from swarm_lab.evacuation.engine import neighbours

spec = importlib.util.spec_from_file_location(
    "propagation",
    Path(__file__).parents[1] / "reports/overnight-experiments/propagation.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_disputing_reference_extends_exposure_after_delivery(tmp_path, monkeypatch):
    root = tmp_path / "runs"
    game = root / "game"
    game.mkdir(parents=True)
    manifest = dict(
        id="fixture",
        scenario={"informant": 0},
        section=1,
        language="en",
        identity="ordinary_peer",
        topology="ring",
        status="completed",
    )
    (game / "manifest.json").write_text(json.dumps(manifest))
    (game / "outcome.json").write_text(
        json.dumps({"adjacency": {i: neighbours(i) for i in range(10)}})
    )
    views = {i: {} for i in range(10)}
    traces = [
        dict(
            round=1,
            views=views,
            messages={0: dict(id="r1-a0", parents=[], signal="Danger")},
        ),
        dict(
            round=2,
            views=views,
            messages={1: dict(id="r2-a1", parents=["r1-a0"], signal="Unknown")},
        ),
    ]
    (game / "traces.jsonl").write_text("".join(json.dumps(t) + "\n" for t in traces))
    monkeypatch.chdir(tmp_path)
    (tmp_path / "reports/overnight-experiments").mkdir(parents=True)
    monkeypatch.setattr(module, "plot", lambda rows: None)
    module.main(root)
    result = json.loads(
        (tmp_path / "reports/overnight-experiments/propagation.json").read_text()
    )
    rounds = result["games"][0]["rounds"]
    assert [r["direct_recipients"] for r in rounds] == [4, 4]
    assert [r["citation_linked_recipients"] for r in rounds] == [4, 5]
