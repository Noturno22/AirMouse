"""Tests for core/licensing.py — tier model, trial gate, lease persistence, compat API."""
import json

import core.licensing as lic


def test_default_tier_is_free():
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=60)
    assert lm.tier is lic.Tier.FREE
    assert not lm.is_pro


def test_free_entitlements():
    ent = lic.entitlements(lic.Tier.FREE)
    assert ent["move"] is True
    assert ent["click"] is True
    for f in ("snap", "voice", "two_hands", "tts", "ai", "autotune", "low_light"):
        assert ent[f] is False


def test_pro_entitlements_all_on():
    ent = lic.entitlements(lic.Tier.PRO)
    for f in ("move", "click", "snap", "voice", "two_hands", "tts",
              "ai", "autotune", "low_light"):
        assert ent[f] is True


def test_is_pro_locked():
    assert lic.is_pro_locked(lic.Tier.FREE, "snap")
    assert not lic.is_pro_locked(lic.Tier.FREE, "move")
    assert not lic.is_pro_locked(lic.Tier.PRO, "snap")


def test_trial_blocks_when_exhausted(tmp_path):
    store = tmp_path / "lic.json"
    lm = lic.LicenseManager(store_path=str(store), trial_seconds=30 * 60)
    lm.report_usage(30 * 60)
    assert lm.is_blocked()
    assert lm.trial_remaining_seconds() == 0
    assert lm.block_reason() == "trial_esgotado"


def test_store_from_other_machine_not_honored(tmp_path):
    p = tmp_path / "lic.json"
    p.write_text(json.dumps({"machine_id": "OTHER", "trial_used": 0,
                             "lease": "", "last_nonce": 0, "last_use_seq": 0}),
                 encoding="utf-8")
    lm = lic.LicenseManager(store_path=str(p), trial_seconds=60)
    lm.load()
    assert lm.tier is lic.Tier.FREE


def test_checkout_urls_built_from_config(monkeypatch):
    lm = lic.LicenseManager(store_path=":memory:")
    urls = lm.checkout_urls(vendor_id=12345)
    assert "checkout.paddle.com" in urls["lifetime"]


def test_open_checkout_calls_browser(monkeypatch):
    lm = lic.LicenseManager(store_path=":memory:")
    monkeypatch.setattr(lic.webbrowser, "open", lambda url, new=0: True)
    assert lm.open_checkout("lifetime", 12345) is True


def test_active_license_defaults_to_free():
    assert lic.active_tier() is lic.Tier.FREE
    lic.set_active_license(lic.LicenseManager(store_path=":memory:"))
    assert lic.active_tier() is lic.Tier.FREE
