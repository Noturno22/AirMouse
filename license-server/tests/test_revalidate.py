"""Tests for revalidate: renew lease, revoke via nonce, anti-replay."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app import create_app


def _client():
    return TestClient(create_app())


def _activate(client, machine="M1"):
    resp = client.post("/admin/keys", json={
        "email": "r@x.com", "admin_token": "dev-admin-token"})
    key = resp.json()["key"]
    r = client.post("/api/v1/activate", json={"key": key, "machine_id": machine})
    return r


def test_revalidate_returns_new_lease():
    client = _client()
    act = _activate(client).json()
    resp = client.post("/api/v1/revalidate", json={
        "machine_id": "M1", "old_lease": act["lease"]})
    assert resp.status_code == 200
    assert resp.json()["tier"] == "pro"
    assert resp.json()["lease"]


def test_revalidate_rejects_stale_nonce_after_revoke():
    client = _client()
    act = _activate(client).json()
    r = client.post("/api/v1/revoke", json={
        "machine_id": "M1", "admin_token": "dev-admin-token"})
    assert r.status_code == 200
    resp = client.post("/api/v1/revalidate", json={
        "machine_id": "M1", "old_lease": act["lease"]})
    assert resp.status_code == 403


def test_revalidate_rejects_unknown_machine():
    client = _client()
    resp = client.post("/api/v1/revalidate", json={
        "machine_id": "NOBODY", "old_lease": "garbage"})
    assert resp.status_code == 403
