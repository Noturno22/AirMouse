import os
import pytest


@pytest.fixture(autouse=True)
def _test_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRMOUSE_LS_DB", str(tmp_path / "ls.db"))
    monkeypatch.setenv("AIRMOUSE_LS_SECRET", "test-jwt-secret")
    monkeypatch.setenv("AIRMOUSE_LS_ADMIN_TOKEN", "dev-admin-token")
    from keys import ensure_test_keypair
    ensure_test_keypair(tmp_path)
