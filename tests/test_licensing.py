"""Tests for core/licensing.py — tier model, entitlement gate, offline key
validation and Paddle checkout launch. Pure offline: no network required."""
import json

import core.licensing as lic


# ── Tier & entitlement ────────────────────────────────────────────────
def test_default_tier_is_free():
    lic_ = lic.LicenseManager()
    assert lic_.tier == lic.Tier.FREE
    assert not lic_.is_pro


def test_free_entitlements():
    ent = lic.entitlements(lic.Tier.FREE)
    assert ent["move"] is True
    assert ent["click"] is True
    # Pro-locked features are OFF on Free
    for f in ("snap", "voice", "two_hands", "tts", "ai", "autotune", "low_light"):
        assert ent[f] is False


def test_pro_entitlements_all_on():
    ent = lic.entitlements(lic.Tier.PRO)
    for f in ("move", "click", "snap", "voice", "two_hands", "tts",
              "ai", "autotune", "low_light"):
        assert ent[f] is True


def test_is_pro_locked():
    assert lic.is_pro_locked(lic.Tier.FREE, "snap")
    assert lic.is_pro_locked(lic.Tier.FREE, "voice")
    assert not lic.is_pro_locked(lic.Tier.FREE, "move")
    assert not lic.is_pro_locked(lic.Tier.PRO, "snap")


# ── Key generation / validation (offline, deterministic secret) ───────
def test_issue_and_validate_pro_key():
    lm = lic.LicenseManager(secret="test-secret")
    key = lm.issue_pro_key("tester@example.com")
    assert key.startswith("MAO-")
    assert lm.validate_key(key) is True


def test_validate_rejects_tampered_key():
    lm = lic.LicenseManager(secret="test-secret")
    key = lm.issue_pro_key("a@b.c")
    tampered = key[:-2] + ("AB" if key[-2:] != "AB" else "CD")
    assert lm.validate_key(tampered) is False


def test_validate_rejects_wrong_secret():
    lm1 = lic.LicenseManager(secret="secret-one")
    lm2 = lic.LicenseManager(secret="secret-two")
    key = lm1.issue_pro_key("x@y.z")
    assert lm2.validate_key(key) is False


def test_validate_rejects_garbage():
    lm = lic.LicenseManager(secret="s")
    assert lm.validate_key("not-a-key") is False
    assert lm.validate_key("") is False


def test_validate_normalizes_whitespace():
    lm = lic.LicenseManager(secret="s")
    key = lm.issue_pro_key("a@b.c")
    assert lm.validate_key("  " + key + " \n") is True


# ── Activation / persistence ──────────────────────────────────────────
def test_activate_pro_sets_tier():
    lm = lic.LicenseManager(secret="s")
    key = lm.issue_pro_key("a@b.c")
    assert lm.activate(key) is True
    assert lm.is_pro
    assert lm.tier == lic.Tier.PRO


def test_activate_invalid_keeps_free():
    lm = lic.LicenseManager(secret="s")
    assert lm.activate("garbage") is False
    assert not lm.is_pro


def test_state_roundtrip(tmp_path):
    lm = lic.LicenseManager(secret="s", store_path=str(tmp_path / "lic.json"))
    key = lm.issue_pro_key("a@b.c")
    lm.activate(key)
    lm.save()

    lm2 = lic.LicenseManager(secret="s", store_path=str(tmp_path / "lic.json"))
    lm2.load()
    assert lm2.is_pro


def test_state_rejects_tampered_store(tmp_path):
    p = tmp_path / "lic.json"
    p.write_text(json.dumps({"tier": "PRO", "key": "fake", "sig": "nope"}),
                 encoding="utf-8")
    lm = lic.LicenseManager(secret="s", store_path=str(p))
    lm.load()
    # A tampered store must not grant Pro for free.
    assert not lm.is_pro


# ── Paddle checkout (offline) ─────────────────────────────────────────
def test_checkout_urls_built_from_config(monkeypatch):
    lm = lic.LicenseManager()
    urls = lm.checkout_urls(vendor_id=1234)
    assert "lifetime" in urls and "subscription" in urls
    assert "access" in urls
    assert "https://checkout.paddle.com/" in urls["lifetime"]


def test_open_checkout_calls_browser(monkeypatch):
    opened = {}
    monkeypatch.setattr(lic.webbrowser, "open",
                        lambda url, new=0: opened.update(url=url) or True)
    lm = lic.LicenseManager()
    assert lm.open_checkout("lifetime", vendor_id=1234) is True
    assert "checkout.paddle.com" in opened["url"]


# ── Runtime gate (active_license / active_tier) ────────────────────────
def test_active_license_defaults_to_free():
    # Sem set_active_license, o runtime cai para Free (nunca concede Pro de graça).
    assert lic.active_tier() == lic.Tier.FREE
    lm = lic.active_license()
    assert not lm.is_pro


def test_set_active_license_and_tier():
    lm = lic.LicenseManager(secret="s")
    key = lm.issue_pro_key("a@b.c")
    lm.activate(key)
    lic.set_active_license(lm)
    assert lic.active_tier() == lic.Tier.PRO
    assert lic.active_license().is_pro
    # Reset para não contaminar outros testes.
    lic.set_active_license(lic.LicenseManager())


def test_runtime_is_pro_locked_for_voice_on_free():
    # O gate usa is_pro_locked(active_tier(), feature): no Free, voice é bloqueado.
    lic.set_active_license(lic.LicenseManager())
    assert lic.is_pro_locked(lic.active_tier(), "voice")
    assert lic.is_pro_locked(lic.active_tier(), "snap")
    # Mas move/clique são sempre livres.
    assert not lic.is_pro_locked(lic.active_tier(), "move")
