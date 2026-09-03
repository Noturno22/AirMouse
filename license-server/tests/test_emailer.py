"""Tests for emailer (envio da chave por SMTP)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import emailer


def test_build_message_contains_key():
    msg = emailer.build_key_email("buyer@example.com", "MAO-ABC-123")
    assert "MAO-ABC-123" in msg.as_string()
    assert "buyer@example.com" in msg["To"]


def test_send_disabled_when_no_smtp(monkeypatch):
    monkeypatch.setenv("AIRMOUSE_SMTP_ENABLED", "0")
    res = emailer.send_key_email("a@b.c", "MAO-X")
    assert res.fired is False
    assert res.error == ""


def test_send_uses_smtp(monkeypatch):
    monkeypatch.setenv("AIRMOUSE_SMTP_ENABLED", "1")
    monkeypatch.setenv("AIRMOUSE_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("AIRMOUSE_SMTP_PORT", "587")
    monkeypatch.setenv("AIRMOUSE_SMTP_USER", "u")
    monkeypatch.setenv("AIRMOUSE_SMTP_PASSWORD", "p")
    monkeypatch.setenv("AIRMOUSE_SMTP_FROM", "sales@maouse.app")
    sent = []

    class _S:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self):
            pass

        def login(self, *a):
            sent.append(("login", a))

        def sendmail(self, *a):
            sent.append(("send", a))

    monkeypatch.setattr(emailer.smtplib, "SMTP", lambda *a, **k: _S())
    res = emailer.send_key_email("buyer@example.com", "MAO-KEY")
    assert res.fired is True
    assert res.error == ""
    assert any(x[0] == "login" and x[1] == ("u", "p") for x in sent)
    assert any(x[0] == "send" for x in sent)


def test_send_returns_error_not_raises(monkeypatch):
    monkeypatch.setenv("AIRMOUSE_SMTP_ENABLED", "1")
    monkeypatch.setenv("AIRMOUSE_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("AIRMOUSE_SMTP_PORT", "587")

    class BoomSMTP:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self):
            pass

        def login(self, *a, **k):
            pass

        def sendmail(self, *a, **k):
            raise RuntimeError("boom")

    monkeypatch.setattr(emailer.smtplib, "SMTP", BoomSMTP)
    res = emailer.send_key_email("a@b.c", "MAO-KEY")
    assert res.fired is False
    assert res.error != ""
