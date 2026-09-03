"""Tests for server-side 30-min trial. Idempotente + nunca diminui + report persiste."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from fastapi.testclient import TestClient
from storage import connect, init_db


def _client():
    return TestClient(create_app())


def test_trial_start_ok():
    client = _client()
    resp = client.post("/api/v1/trial/start", json={"machine_id": "M1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["remaining_seconds"] == 30 * 60


def test_trial_start_does_not_reset():
    client = _client()
    client.post("/api/v1/trial/start", json={"machine_id": "M2"})
    conn = connect()
    init_db(conn)
    conn.execute("UPDATE trial SET used_seconds=1800 WHERE machine_id='M2'")
    conn.commit()
    conn.close()
    body = client.post("/api/v1/trial/start", json={"machine_id": "M2"}).json()
    assert body["remaining_seconds"] == 0


def test_trial_report_persists_usage():
    client = _client()
    client.post("/api/v1/trial/start", json={"machine_id": "M3"})
    r = client.post("/api/v1/trial/report",
                    json={"machine_id": "M3", "used_seconds": 120})
    assert r.status_code == 200
    status = client.get("/api/v1/trial/status?machine_id=M3").json()
    assert status["remaining_seconds"] == 30 * 60 - 120


def test_trial_report_never_decreases():
    client = _client()
    client.post("/api/v1/trial/start", json={"machine_id": "M4"})
    client.post("/api/v1/trial/report", json={"machine_id": "M4", "used_seconds": 300})
    # report menor não reduz
    client.post("/api/v1/trial/report", json={"machine_id": "M4", "used_seconds": 60})
    status = client.get("/api/v1/trial/status?machine_id=M4").json()
    assert status["remaining_seconds"] == 30 * 60 - 300


def test_trial_status():
    client = _client()
    client.post("/api/v1/trial/start", json={"machine_id": "M5"})
    status = client.get("/api/v1/trial/status?machine_id=M5").json()
    assert "remaining_seconds" in status
