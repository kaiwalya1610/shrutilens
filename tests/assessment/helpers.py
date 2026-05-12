from __future__ import annotations

import json
from pathlib import Path


def compact_export(record: dict) -> dict:
    session = record["session"]
    return {
        "pack": record["pack"],
        "status": session["status"],
        "current_item_id": session["current_item_id"],
        "visited_item_ids": session["visited_item_ids"],
        "responses": {
            item_id: {
                "anchor_id": response.get("anchor_id"),
                "anchor_ids": response.get("anchor_ids", []),
                "value": response.get("value"),
                "skipped": response.get("skipped", False),
            }
            for item_id, response in session["responses"].items()
        },
        "score": session["score"],
        "safety_events": [
            {
                "hook_id": event["hook_id"],
                "severity": event["severity"],
                "interrupt": event["interrupt"],
                "item_id": event["item_id"],
                "evidence": event["evidence"],
            }
            for event in session["safety_events"]
        ],
    }


def assert_matches_golden(record: dict, golden_path: Path) -> None:
    expected = json.loads(golden_path.read_text())
    assert compact_export(record) == expected
