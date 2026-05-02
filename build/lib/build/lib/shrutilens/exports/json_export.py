from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from shrutilens.core.contracts import AssessmentPack, SessionState


class JsonExporter:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def export(self, pack: AssessmentPack, state: SessionState) -> Path:
        path = self.root / f"{state.id}.json"
        payload = {
            "exported_at": datetime.now(UTC).isoformat(),
            "pack": {
                "id": pack.id,
                "version": pack.version,
                "mode": pack.mode.value,
                "title": pack.title,
            },
            "session": state.model_dump(mode="json"),
            "schema": pack.export_schema,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True))
        return path
