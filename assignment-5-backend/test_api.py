"""Assignment 5 — endpoint tests (also proves the command->status->WS loop).

Run:  pip install -r requirements.txt && pytest
Uses the default simulated agent, so no LLM key / browser needed.
"""
import time

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture()
def client():
    # Context-manager form runs FastAPI startup (init_db + register event loop).
    with TestClient(app) as c:
        yield c


def test_profile_roundtrip(client):
    payload = {"name": "Anselm", "email": "a@b.com", "phone": "123",
               "address": "742 Evergreen", "resume_text": "Python, Playwright"}
    r = client.post("/user/profile", json=payload)
    assert r.status_code == 200 and r.json()["name"] == "Anselm"
    g = client.get("/user/profile")
    assert g.status_code == 200 and g.json()["email"] == "a@b.com"
    assert g.json()["resume_text"] == "Python, Playwright"


def test_command_returns_task_id_and_completes(client):
    r = client.post("/command", json={"command": "go to google.com and search AI news"})
    assert r.status_code == 200
    task_id = r.json()["task_id"]
    assert r.json()["status"] == "pending"

    status = {}
    for _ in range(60):  # wait for the background task to finish (~3s simulated)
        status = client.get(f"/status/{task_id}").json()
        if status["status"] == "completed":
            break
        time.sleep(0.2)
    assert status["status"] == "completed"
    assert len(status["steps"]) >= 3
    assert status["result"]


def test_status_unknown_task_404(client):
    assert client.get("/status/does-not-exist").status_code == 404


def test_websocket_streams_live_steps(client):
    task_id = client.post("/command", json={"command": "close all tabs"}).json()["task_id"]
    messages = []
    with client.websocket_connect(f"/ws/{task_id}") as ws:
        while True:
            data = ws.receive_json()
            messages.append(data)
            if data.get("status") in ("completed", "failed"):
                break
    assert len(messages) >= 3
    assert messages[-1]["status"] == "completed"
