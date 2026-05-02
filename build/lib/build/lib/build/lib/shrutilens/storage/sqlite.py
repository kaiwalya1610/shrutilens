from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from shrutilens.core.contracts import SessionState


class SQLiteSessionStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def save(self, state: SessionState) -> None:
        with self._connect() as conn:
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

    def get(self, session_id: str) -> SessionState:
        with self._connect() as conn:
            row = conn.execute("select state_json from sessions where id = ?", (session_id,)).fetchone()
        if row is None:
            raise KeyError(session_id)
        return SessionState.model_validate(json.loads(row[0]))

    def _init(self) -> None:
        with self._connect() as conn:
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

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)
