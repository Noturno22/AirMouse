"""Tests for the Paddle webhook endpoint (issue key + email + idempotente)."""
import hashlib
import hmac
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from fastapi.testclient import TestClient

SECRET = "pdl_test_secret"


def _signed(event: dict) -> tuple[str, str]:
    raw = json.dumps(event, separators=(",", ":"))
    ts = str(int(time.time()))
    sig = hmac.new(SECRET.encode(), f"{ts}:{raw}".encode(), hashlib.sha256).hexdigest()
    return raw, f"ts={ts};h1={sig}"


def _completed_event(event_id="evt_123", email="buyer@example.com"):
    return {
        "event_id": event_id,
        "event_type": "transaction.completed",
        "occurred_at": "2026-09-03T10:00:00Z",
        "notification_id": "ntf_1",
        "data": {
            "id": "txn_1",
            "status": "completed",
            "customer": {"email": email},
            "items": [{"price": {"product": {"id": "pro_lifetime"}}}],
        },
    }


def test_webhook_issues_key_and_returns_200():
    client = TestClient(create_app())
    raw, header = _signed(_completed_event())
    resp = client.post("/webhooks/paddle", content=raw,
                       headers={"Paddle-Signature": header})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("ok") is True
    assert body.get("key", "").startswith("MAO-")
    assert body.get("email") == "buyer@example.com"


def test_webhook_idempotent_same_event():
    client = TestClient(create_app())
    raw, header = _signed(_completed_event(event_id="evt_dedup"))
    r1 = client.post("/webhooks/paddle", content=raw, headers={"Paddle-Signature": header})
    r2 = client.post("/webhooks/paddle", content=raw, headers={"Paddle-Signature": header})
    assert r1.status_code == 200
    assert r2.status_code == 200
    # idempotente: mesma chave, não duplica nem emite chave nova
    assert r1.json()["key"] == r2.json()["key"]


def test_webhook_rejects_bad_signature():
    client = TestClient(create_app())
    raw, _ = _signed(_completed_event())
    resp = client.post("/webhooks/paddle", content=raw,
                       headers={"Paddle-Signature": "ts=0;h1=bad"})
    assert resp.status_code == 401


def test_webhook_ignores_non_completed():
    client = TestClient(create_app())
    raw, header = _signed({"event_id": "evt_1", "event_type": "transaction.paid",
                           "data": {}})
    resp = client.post("/webhooks/paddle", content=raw,
                       headers={"Paddle-Signature": header})
    assert resp.status_code == 200
    assert resp.json().get("ok") is True
    assert resp.json().get("handled") is False


def test_webhook_returns_503_when_secret_unset(monkeypatch):
    monkeypatch.delenv("AIRMOUSE_PADDLE_WEBHOOK_SECRET", raising=False)
    client = TestClient(create_app())
    raw, _ = _signed(_completed_event())
    resp = client.post("/webhooks/paddle", content=raw,
                       headers={"Paddle-Signature": "ts=0;h1=x"})
    assert resp.status_code == 503
