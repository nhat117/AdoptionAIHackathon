"""Append-only execution records; independent of model conversation memory."""

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class EventLog:
    def __init__(self, path: Path):
        self.path = path
        self.run_id = str(uuid4())
        path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: str, **data: object) -> None:
        record = {
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **data,
        }
        # A short synchronous append has no await, so asyncio branches cannot
        # interleave writes here. Use separate files for separate processes.
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
