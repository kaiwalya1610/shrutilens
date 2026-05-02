from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shrutilens.core.runner import AssessmentRunner, build_default_runner
from shrutilens.packs.loader import PackNotFoundError, PackRepository


class StartSessionRequest(BaseModel):
    pack_id: str
    metadata: dict[str, Any] = {}


class UtteranceRequest(BaseModel):
    text: str


class ConfirmationRequest(BaseModel):
    accepted: bool
    corrected_text: str | None = None


def create_app(
    pack_repository: PackRepository | None = None,
    runner: AssessmentRunner | None = None,
) -> FastAPI:
    app = FastAPI(title="Shrutilens", version="0.1.0")
    packs = pack_repository or PackRepository()
    assessment_runner = runner or build_default_runner(Path("data"), Path("exports"))

    def _load_session_and_pack(session_id: str) -> tuple[Any, Any]:
        try:
            state = assessment_runner.store.get(session_id)
            pack = packs.get(state.pack_id)
        except (KeyError, PackNotFoundError) as exc:
            raise HTTPException(status_code=404, detail="session not found") from exc
        return state, pack

    def _session_prompt_response(state: Any, prompt: Any) -> dict[str, Any]:
        return {"session": state.model_dump(mode="json"), "prompt": prompt.model_dump(mode="json")}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/packs")
    def list_packs() -> list[dict[str, Any]]:
        return [
            {
                "id": pack.id,
                "version": pack.version,
                "title": pack.title,
                "mode": pack.mode.value,
                "language": pack.language,
            }
            for pack in packs.list_packs()
        ]

    @app.post("/sessions")
    def start_session(request: StartSessionRequest) -> dict[str, Any]:
        try:
            pack = packs.get(request.pack_id)
        except PackNotFoundError as exc:
            raise HTTPException(status_code=404, detail="pack not found") from exc
        state, prompt = assessment_runner.start(pack, request.metadata)
        return _session_prompt_response(state, prompt)

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str) -> dict[str, Any]:
        try:
            state = assessment_runner.store.get(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="session not found") from exc
        return {"session": state.model_dump(mode="json")}

    @app.post("/sessions/{session_id}/utterance")
    def submit_utterance(session_id: str, request: UtteranceRequest) -> dict[str, Any]:
        state, pack = _load_session_and_pack(session_id)
        state, prompt = assessment_runner.accept_utterance(pack, state, request.text)
        return _session_prompt_response(state, prompt)

    @app.post("/sessions/{session_id}/confirmation")
    def confirm_answer(session_id: str, request: ConfirmationRequest) -> dict[str, Any]:
        state, pack = _load_session_and_pack(session_id)
        state, prompt = assessment_runner.confirm_pending(pack, state, request.accepted, request.corrected_text)
        return _session_prompt_response(state, prompt)

    return app


app = create_app()
