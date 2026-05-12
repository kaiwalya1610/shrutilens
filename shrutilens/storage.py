from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shrutilens.models import SessionState


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute(
        """
        create table if not exists sessions (
            id text primary key,
            pack_id text not null,
            status text not null,
            state_json text not null,
            created_at text not null default (datetime('now')),
            updated_at text not null default (datetime('now'))
        )
        """
    )
    return conn


def save_session(conn: sqlite3.Connection, state: SessionState) -> None:
    with conn:
        conn.execute(
            """
            insert into sessions (id, pack_id, status, state_json, updated_at)
            values (?, ?, ?, ?, datetime('now'))
            on conflict(id) do update set
                status=excluded.status,
                state_json=excluded.state_json,
                updated_at=datetime('now')
            """,
            (state.id, state.pack_id, state.status.value, state.model_dump_json()),
        )


def load_session(conn: sqlite3.Connection, session_id: str) -> SessionState:
    row = conn.execute("select state_json from sessions where id = ?", (session_id,)).fetchone()
    if row is None:
        raise KeyError(session_id)
    return SessionState.model_validate(json.loads(row[0]))


def append_audit(audit_dir: Path, session_id: str, event: str, payload: dict[str, Any]) -> None:
    audit_dir.mkdir(parents=True, exist_ok=True)
    record = {"ts": datetime.now(UTC).isoformat(), "event": event, "payload": payload}
    with (audit_dir / f"{session_id}.jsonl").open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def write_export(export_dir: Path, session_id: str, payload: dict[str, Any]) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    path = export_dir / f"{session_id}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path
