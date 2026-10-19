import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "couples-coplay-engine"


def test_full_api_room_flow():
    # 1. Create Session
    create_payload = {
        "couple_id": "c-999",
        "partner_a_id": "p-101",
        "partner_a_name": "Dev",
        "partner_b_id": "p-102",
        "partner_b_name": "Tara",
        "interests": ["Board Games", "Standup Comedy"]
    }
    create_res = client.post("/api/sessions/create", json=create_payload)
    assert create_res.status_code == 200
    session_data = create_res.json()
    session_id = session_data["session_id"]
    room_code = session_data["room_code"]
    assert session_data["status"] == "WAITING_FOR_PARTNER"

    # 2. Partner Joins
    join_payload = {
        "room_code": room_code,
        "partner_id": "p-102",
        "partner_name": "Tara"
    }
    join_res = client.post("/api/sessions/join", json=join_payload)
    assert join_res.status_code == 200
    assert join_res.json()["status"] == "ROUND_ACTIVE"

    # 3. Dev Submits
    ans1_res = client.post(
        f"/api/sessions/{session_id}/answer",
        json={"player_id": "p-101", "round_index": 0, "answer": "Option 1"}
    )
    assert ans1_res.status_code == 200
    assert ans1_res.json()["status"] == "WAITING_FOR_PARTNER"

    # 4. Tara Submits -> Reveal
    ans2_res = client.post(
        f"/api/sessions/{session_id}/answer",
        json={"player_id": "p-102", "round_index": 0, "answer": "Option 1"}
    )
    assert ans2_res.status_code == 200
    reveal_data = ans2_res.json()
    assert reveal_data["status"] == "REVEALED"
    assert reveal_data["reveal"]["is_match"] is True

    # 5. Advance
    next_res = client.post(f"/api/sessions/{session_id}/next")
    assert next_res.status_code == 200
    assert next_res.json()["current_round"] == 1


def test_websocket_connection_and_ping():
    with client.websocket_connect("/ws/test-sess/test-user") as ws:
        # Initial connect event broadcast
        msg = ws.receive_json()
        assert msg["event"] == "PLAYER_CONNECTED"

        # Send Ping
        ws.send_json({"action": "PING"})
        resp = ws.receive_json()
        assert resp["event"] == "PONG"
