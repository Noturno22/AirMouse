"""Tests for Paddle webhook signature verification and event parsing (pure)."""
import hashlib
import hmac
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paddle

SECRET = "pdl_ntfset_test_secret"


def _signed(event: dict, secret: str = SECRET) -> tuple[str, str]:
    raw = json.dumps(event, separators=(",", ":"))
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode(), f"{ts}:{raw}".encode(), hashlib.sha256).hexdigest()
    return raw, f"ts={ts};h1={sig}"


def test_verify_valid_signature():
    event = {"event_type": "transaction.completed", "event_id": "evt_x"}
    raw, header = _signed(event)
    assert paddle.verify_signature(raw, header, SECRET) is True


def test_verify_rejects_wrong_secret():
    event = {"event_type": "transaction.completed"}
    raw, header = _signed(event, secret="other-secret")
    assert paddle.verify_signature(raw, header, SECRET) is False


def test_verify_rejects_stale_timestamp():
    event = {"event_type": "transaction.completed"}
    raw, _ = _signed(event)
    old_ts = int(time.time()) - 10000
    bad_header = f"ts={old_ts};h1=abc"
    assert paddle.verify_signature(raw, bad_header, SECRET) is False


def test_verify_rejects_malformed_header():
    event = {"event_type": "transaction.completed"}
    raw, _ = _signed(event)
    assert paddle.verify_signature(raw, "garbage", SECRET) is False


def test_parse_transaction_completed_extracts_email():
    event = {
        "event_type": "transaction.completed",
        "event_id": "evt_abc",
        "data": {
            "id": "txn_1",
            "status": "completed",
            "customer": {"email": "buyer@example.com"},
            "items": [{"price": {"product": {"id": "pro_lifetime"}}}],
        },
    }
    info = paddle.event_info(event)
    assert info["email"] == "buyer@example.com"
    assert info["event_id"] == "evt_abc"
    assert info["product_id"] == "pro_lifetime"


def test_parse_non_completed_transaction_returns_none():
    event = {"event_type": "transaction.paid", "event_id": "evt_x", "data": {}}
    assert paddle.event_info(event) is None
