"""Tests for purchases storage (dedup por event_id)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import storage
from storage import connect, init_db


def test_purchase_record_and_dedup():
    conn = connect()
    init_db(conn)
    key_hash = "k1"
    email = "a@b.c"
    assert storage.record_purchase(conn, "evt_1", email, key_hash, "pro_lifetime") is True
    # mesmo event_id -> dedup (devolve False, não duplica)
    assert storage.record_purchase(conn, "evt_1", email, "DIFFERENT", "pro_lifetime") is False
    rows = storage.purchase_for_event(conn, "evt_1")
    assert rows is not None
    assert rows["email"] == "a@b.c"
    assert rows["key_hash"] == "k1"
    conn.close()


def test_email_keys_returns_issued_keys():
    conn = connect()
    init_db(conn)
    k1 = "MAO-KEY-ONE"
    k2 = "MAO-KEY-TWO"
    storage.record_purchase(conn, "evt_2", "buyer@example.com", k1, "pro")
    storage.record_purchase(conn, "evt_3", "buyer@example.com", k2, "pro")
    keys = storage.email_keys(conn, "buyer@example.com")
    assert set(keys) == {k1, k2}
    conn.close()
