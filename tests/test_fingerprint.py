"""Tests for machine fingerprint -> stable machine_id."""
import core.fingerprint as fp


def test_machine_id_deterministic():
    a = fp.machine_id()
    b = fp.machine_id()
    assert a == b
    assert len(a) >= 32


def test_machine_id_hex():
    mid = fp.machine_id()
    assert all(c in "0123456789abcdef" for c in mid)


def test_fingerprint_components_nonempty():
    comps = fp.collect_components()
    assert comps
