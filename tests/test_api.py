from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from shrutilens.api import create_app


def test_api_session_flow(tmp_path: Path):
    app = create_app(data_dir=tmp_path / "data", export_dir=tmp_path / "exports")
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
    assert payload["session"]["current_item_id"] == "pain"
    assert payload["prompt"]["item_id"] == "pain"
