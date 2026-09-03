"""Tests for activate: 1 key = 1 machine hard rule + ES256-signed lease."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jwt
from app import create_app
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient
from security import _private_key_path


def _client():
    return TestClient(create_app())


def _issue(client, email="tester@example.com"):
    resp = client.post("/admin/keys", json={
        "email": email, "admin_token": "dev-admin-token"})
    assert resp.status_code == 200
    return resp.json()["key"]


def test_activate_first_machine_ok(tmp_path, monkeypatch):
    client = _client()
    resp = client.post("/api/v1/activate", json={
        "key": _issue(client, "first@x.com"), "machine_id": "MACHINE-A"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["tier"] == "pro"
    assert body["lease"]
    # o lease é um JWT ES256 válido (3 segmentos) com sub correto
    assert body["lease"].count(".") == 2
    # verifica que o lease foi assinado com a privada (não é alg:none)
    priv = serialization.load_pem_private_key(
        open(_private_key_path(), "rb").read(), password=None)
    claims = jwt.decode(body["lease"], priv.public_key(), algorithms=["ES256"])
    assert claims["sub"] == "machine:MACHINE-A"
    assert claims["tier"] == "pro"


def test_activate_same_key_other_machine_rejected(tmp_path, monkeypatch):
    client = _client()
    key = _issue(client, "one@x.com")
    r1 = client.post("/api/v1/activate", json={"key": key, "machine_id": "MACHINE-A"})
    assert r1.status_code == 200
    r2 = client.post("/api/v1/activate", json={"key": key, "machine_id": "MACHINE-B"})
    assert r2.status_code == 403
    assert "maquina" in r2.json()["error"].lower()


def test_activate_same_key_same_machine_reissue_ok(tmp_path, monkeypatch):
    client = _client()
    key = _issue(client, "re@x.com")
    r1 = client.post("/api/v1/activate", json={"key": key, "machine_id": "M"})
    assert r1.status_code == 200
    r2 = client.post("/api/v1/activate", json={"key": key, "machine_id": "M"})
    assert r2.status_code == 200  # mesma máquina → reemite lease (idempotente)


def test_activate_invalid_key_rejected(tmp_path, monkeypatch):
    client = _client()
    resp = client.post("/api/v1/activate", json={
        "key": "MAO-NOTVALID", "machine_id": "M"})
    assert resp.status_code == 403
