"""Tests for mobile IAP entitlement (Play purchaseToken -> mobile_pro lease)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app
from fastapi.testclient import TestClient
from playstore import PlayValidationError, validate_purchase
from security import decode_jwt

VALID_DEV_TOKEN = "test_valid_dev_token_123"
PRODUCT_ID = "maouse_mobile_pro"
PACKAGE = "com.airmouse.mobile"
DEVICE = "device-instance-abc"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("AIRMOUSE_MOBILE_DEV_ALLOW", "1")
    monkeypatch.setenv("AIRMOUSE_MOBILE_PRODUCT_ID", PRODUCT_ID)
    app = create_app()
    return TestClient(app)


def test_dev_validate_accepts_test_token(monkeypatch):
    monkeypatch.setenv("AIRMOUSE_MOBILE_DEV_ALLOW", "1")
    assert validate_purchase(PACKAGE, PRODUCT_ID, "test_foo") == ""


def test_dev_validate_rejects_non_test_token(monkeypatch):
    monkeypatch.setenv("AIRMOUSE_MOBILE_DEV_ALLOW", "1")
    with pytest.raises(PlayValidationError):
        validate_purchase(PACKAGE, PRODUCT_ID, "not_test_token")


def test_entitle_issues_mobile_pro_lease(client):
    resp = client.post("/api/v1/mobile/entitle", json={
        "purchase_token": VALID_DEV_TOKEN,
        "product_id": PRODUCT_ID,
        "package_name": PACKAGE,
        "device_id": DEVICE,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["tier"] == "mobile_pro"
    assert body["first_time"] is True
    claims = decode_jwt(body["lease"])
    assert claims["tier"] == "mobile_pro"


def test_entitle_dedup_returns_first_time_false(client):
    payload = {
        "purchase_token": VALID_DEV_TOKEN,
        "product_id": PRODUCT_ID,
        "package_name": PACKAGE,
        "device_id": DEVICE,
    }
    r1 = client.post("/api/v1/mobile/entitle", json=payload)
    r2 = client.post("/api/v1/mobile/entitle", json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["first_time"] is True
    assert r2.json()["first_time"] is False
    # ambos leases válidos com tier mobile_pro
    assert r1.json()["tier"] == "mobile_pro"
    assert r2.json()["tier"] == "mobile_pro"


def test_entitle_rejects_unknown_token(client):
    resp = client.post("/api/v1/mobile/entitle", json={
        "purchase_token": "garbage-token",
        "product_id": PRODUCT_ID,
        "package_name": PACKAGE,
        "device_id": DEVICE,
    })
    assert resp.status_code == 403
    assert resp.json()["error"] == "token_invalido_dev"


def test_entitle_rejects_wrong_product(client):
    resp = client.post("/api/v1/mobile/entitle", json={
        "purchase_token": "test_wrong_product",
        "product_id": "some_other_product",
        "package_name": PACKAGE,
        "device_id": DEVICE,
    })
    assert resp.status_code == 422
    assert resp.json()["error"] == "produto_errado"


def test_entitle_rejects_wrong_package(client):
    resp = client.post("/api/v1/mobile/entitle", json={
        "purchase_token": "test_wrong_package",
        "product_id": PRODUCT_ID,
        "package_name": "com.evil.app",
        "device_id": DEVICE,
    })
    assert resp.status_code == 422
    assert resp.json()["error"] == "pacote_errado"
