"""Tests for key issuance and storage on the license server."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from fastapi.testclient import TestClient


def _client():
    return TestClient(create_app())


def test_admin_issue_key():
    client = _client()
    resp = client.post("/admin/keys", json={
        "email": "tester@example.com", "admin_token": "dev-admin-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["key"].startswith("MAO-")
    assert data["email"] == "tester@example.com"


def test_admin_issue_rejects_bad_token():
    client = _client()
    resp = client.post("/admin/keys", json={
        "email": "a@b.c", "admin_token": "wrong"})
    assert resp.status_code == 403
