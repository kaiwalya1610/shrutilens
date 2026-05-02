from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class JsonlAuditLog:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def append(self, session_id: str, event: str, payload: dict[str, Any]) -> None:
        path = self.root / f"{session_id}.jsonl"
        record = {
            "ts": datetime.now(UTC).isoformat(),
            "event": event,
            "payload": payload,
        }
        with path.open("a") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
