from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from shrutilens.api.app import create_app
from shrutilens.core.runner import build_default_runner
from shrutilens.packs.loader import PackRepository


def test_api_session_flow(tmp_path: Path):
    app = create_app(
        pack_repository=PackRepository(),
        runner=build_default_runner(tmp_path / "data", tmp_path / "exports"),
    )
    client = TestClient(app)

    packs = client.get("/packs")
    assert packs.status_code == 200
    assert {pack["id"] for pack in packs.json()} >= {"phq9_demo", "product_discovery_demo"}

    started = client.post("/sessions", json={"pack_id": "product_discovery_demo"})
    assert started.status_code == 200
    session_id = started.json()["session"]["id"]

    response = client.post(
        f"/sessions/{session_id}/utterance",
        json={"text": "I interview customers and synthesize product feedback."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session"]["current_index"] == 1
    assert payload["prompt"]["item_id"] == "pain"
