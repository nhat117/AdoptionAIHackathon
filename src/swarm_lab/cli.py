"""Run the generic graph offline by default; opt in to live Adaption requests."""

import argparse
import asyncio
import json
import os
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from adaption import AsyncAdaption
from dotenv import load_dotenv

from .backend import AdaptionBackend, OfflineBackend
from .events import EventLog
from .graph import build_graph
from .nodes import Nodes
from .settings import Settings


async def run(task: str, settings: Settings, events: EventLog, live: bool) -> dict:
    events.emit(
        "run_started",
        mode="live" if live else "offline",
        task=task,
        settings=asdict(settings),
    )
    try:
        if live:
            if not os.environ.get("ADAPTION_API_KEY", "").strip():
                raise ValueError("Set ADAPTION_API_KEY before using --live")
            # Avoid invisible retries changing call counts in a testing harness.
            async with AsyncAdaption(timeout=30.0, max_retries=0) as client:
                backend = AdaptionBackend(client, settings)
                graph = build_graph(Nodes(backend, settings, events))
                result = await graph.ainvoke({"task": task})
        else:
            graph = build_graph(Nodes(OfflineBackend(), settings, events))
            result = await graph.ainvoke({"task": task})
        events.emit("run_completed", state=result)
        return result
    except Exception as error:
        # Log the error class, not provider exception bodies or credentials.
        events.emit("run_failed", error_type=type(error).__name__)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task", default="Explore how information moves through this graph."
    )
    parser.add_argument("--config", type=Path, help="Optional JSON settings file")
    parser.add_argument(
        "--live", action="store_true", help="Make real Adaption requests"
    )
    parser.add_argument(
        "--log", type=Path, help="JSONL path; default: runs/<unique ID>.jsonl"
    )
    args = parser.parse_args()
    load_dotenv(override=False)
    try:
        settings = Settings.load(args.config) if args.config else Settings()
        events = EventLog(args.log or Path("runs") / f"{uuid4()}.jsonl")
        state = asyncio.run(run(args.task, settings, events, args.live))
    except Exception as error:
        # Keep API errors concise; full request/response bodies may contain secrets.
        parser.exit(
            1,
            f"Run failed ({type(error).__name__}). Check config, credentials, "
            "and the execution log if one was created.\n",
        )
    print(
        json.dumps(
            {"run_id": events.run_id, "log": str(events.path), "state": state},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0
