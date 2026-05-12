from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shrutilens import runner
from shrutilens.packs import PackNotFoundError, load_pack_dir
from shrutilens.storage import append_audit, load_session, open_db, save_session, write_export


class StartSessionRequest(BaseModel):
    pack_id: str
    metadata: dict[str, Any] = {}


class UtteranceRequest(BaseModel):
    text: str


class ConfirmationRequest(BaseModel):
    accepted: bool
    corrected_text: str | None = None


def create_app(
    packs: dict | None = None,
    data_dir: Path = Path("data"),
    export_dir: Path = Path("exports"),
) -> FastAPI:
    app = FastAPI(title="Shrutilens", version="0.1.0")
    pack_index = packs if packs is not None else load_pack_dir()
    db = open_db(data_dir / "shrutilens.sqlite3")
    audit_dir = data_dir / "audit"

    def _get_pack(pack_id: str):
        if pack_id not in pack_index:
            raise HTTPException(status_code=404, detail="pack not found")
        return pack_index[pack_id]

    def _load(session_id: str):
        try:
            state = load_session(db, session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="session not found") from exc
        return state, _get_pack(state.pack_id)

    def _response(state, prompt) -> dict[str, Any]:
        return {"session": state.model_dump(mode="json"), "prompt": prompt.model_dump(mode="json")}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/packs")
    def list_packs() -> list[dict[str, Any]]:
        return [
            {"id": p.id, "version": p.version, "title": p.title, "mode": p.mode.value, "language": p.language}
            for p in pack_index.values()
        ]

    @app.post("/sessions")
    def start(request: StartSessionRequest) -> dict[str, Any]:
        pack = _get_pack(request.pack_id)
        state = runner.start_session(pack, request.metadata)
        save_session(db, state)
        append_audit(audit_dir, state.id, "session_started", {"pack_id": pack.id, "mode": pack.mode.value})
        return _response(state, runner.next_prompt(pack, state))

    @app.get("/sessions/{session_id}")
    def get(session_id: str) -> dict[str, Any]:
        state, _ = _load(session_id)
        return {"session": state.model_dump(mode="json")}

    @app.post("/sessions/{session_id}/utterance")
    def utterance(session_id: str, request: UtteranceRequest) -> dict[str, Any]:
        state, pack = _load(session_id)
        append_audit(audit_dir, state.id, "user_utterance", {"text": request.text})
        state, prompt = runner.accept_utterance(pack, state, request.text)
        save_session(db, state)
        if state.status.value == "completed":
            payload = runner.export_record(pack, state)
            write_export(export_dir, state.id, payload)
        return _response(state, prompt)

    @app.post("/sessions/{session_id}/confirmation")
    def confirm(session_id: str, request: ConfirmationRequest) -> dict[str, Any]:
        state, pack = _load(session_id)
        state, prompt = runner.confirm_pending(pack, state, request.accepted, request.corrected_text)
        save_session(db, state)
        if state.status.value == "completed":
            payload = runner.export_record(pack, state)
            write_export(export_dir, state.id, payload)
        return _response(state, prompt)

    return app


app = create_app()
