"""Studio entry point: load the editable graph and select its model backend.

The server calls this factory for execution and graph/schema inspection. Backend
selection is an explicit server setting, never controlled by model output.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from adaption import AsyncAdaption

from .backend import AdaptionBackend, OfflineBackend
from .events import EventLog
from .graph import build_graph
from .nodes import Nodes
from .settings import Settings


@asynccontextmanager
async def make_graph():
    config_path = os.environ.get("SWARM_LAB_CONFIG")
    settings = Settings.load(Path(config_path)) if config_path else Settings()
    events = EventLog(Path("runs") / f"studio-{uuid4()}.jsonl")
    mode = os.environ.get("SWARM_LAB_MODE", "offline")
    if mode == "offline":
        yield build_graph(Nodes(OfflineBackend(), settings, events))
    elif mode == "live":
        if not os.environ.get("ADAPTION_API_KEY", "").strip():
            raise ValueError("Set ADAPTION_API_KEY for SWARM_LAB_MODE=live")
        async with AsyncAdaption(timeout=30.0, max_retries=0) as client:
            backend = AdaptionBackend(client, settings)
            yield build_graph(Nodes(backend, settings, events))
    else:
        raise ValueError("SWARM_LAB_MODE must be offline or live")
