"""Phase 0 — infra smoke tests: health, profile round-trip, command->status->WS.

Run from final-project/:  pytest tests/test_phase0.py
Uses the simulated runner, so no LLM key needed.
"""
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/docs").status_code == 200


def test_profile_roundtrip(client):
    r = client.post("/user/profile", json={"name": "Anselm", "email": "a@b.com",
                                           "college": "MIT", "grad_year": "2027"})
    assert r.status_code == 200 and r.json()["name"] == "Anselm"
    g = client.get("/user/profile")
    assert g.json()["college"] == "MIT" and g.json()["grad_year"] == "2027"


def test_command_status_and_ws(client, monkeypatch):
    # Force the deterministic simulated runner so this infra test never depends on
    # a live LLM call / API quota (it exercises the command->status->WS loop).
    monkeypatch.setattr("agents.runner.has_llm", lambda: False)
    task_id = client.post("/command", json={"command": "hello"}).json()["task_id"]

    messages = []
    with client.websocket_connect(f"/ws/{task_id}") as ws:
        while True:
            data = ws.receive_json()
            messages.append(data)
            if data["status"] in ("completed", "failed"):
                break
    assert messages[-1]["status"] == "completed"

    status = client.get(f"/status/{task_id}").json()
    assert status["status"] == "completed"
    assert status["result"]


def test_status_404(client):
    assert client.get("/status/nope").status_code == 404
