"""Missing or empty data must never produce a successful observability result."""

import asyncio
import importlib.util
import json
from argparse import Namespace
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "observability",
    Path(__file__).parents[1] / "reports/overnight-experiments/check_observability.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_missing_root_rejected(tmp_path):
    with pytest.raises(ValueError, match="missing"):
        asyncio.run(module.main(Namespace(roots=[tmp_path / "missing"])))


@pytest.mark.parametrize("irrelevant_manifest", [False, True])
def test_empty_or_non_original_protocol_root_rejected(tmp_path, irrelevant_manifest):
    if irrelevant_manifest:
        folder = tmp_path / "evidence-game"
        folder.mkdir()
        (folder / "manifest.json").write_text(
            json.dumps({"status": "completed", "section": "4"})
        )
    with pytest.raises(ValueError, match="No eligible"):
        asyncio.run(module.main(Namespace(roots=[tmp_path])))
