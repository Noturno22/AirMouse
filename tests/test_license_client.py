"""Tests for LicenseClient HTTP transport (urllib) + failover."""
import json
from urllib.parse import urlparse

import pytest

import core.license_client as lc


class _FakeHandler:
    def __init__(self, responses):
        self._responses = responses
        self.calls = []

    def __call__(self, req, timeout=5):
        self.calls.append(req.full_url)
        url = req.full_url
        req_path = urlparse(url).path
        for base, payload in self._responses.items():
            parsed = urlparse(base)
            if parsed.scheme:
                # base é um URL completo -> combinar pelo full_url (host importa)
                if url.startswith(base):
                    status, body = payload
                    return _FakeResp(status, json.dumps(body).encode())
            else:
                # base é apenas um path -> combinar pelo path
                if req_path.startswith(parsed.path):
                    status, body = payload
                    return _FakeResp(status, json.dumps(body).encode())
        return _FakeResp(404, b'{"error":"not found"}')

    def _method(self):
        return "POST"


class _FakeResp:
    def __init__(self, status, body):
        self.status = status
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_activate_post(monkeypatch):
    handler = _FakeHandler({"/api/v1/activate": (200, {"tier": "pro",
                                                       "lease": "L1",
                                                       "session_id": "s1",
                                                       "use_seq": 1})})
    monkeypatch.setattr(lc.urllib.request, "urlopen", handler)
    client = lc.LicenseClient(["http://srv"])
    result = client.activate("MAO-KEY", "mid123")
    assert result["tier"] == "pro"
    assert result["lease"] == "L1"


def test_failover_to_next_endpoint(monkeypatch):
    handler = _FakeHandler({
        "http://srv1/api/v1/activate": (500, {"error": "boom"}),
        "http://srv2/api/v1/activate": (200, {"tier": "pro", "lease": "L2"}),
    })
    monkeypatch.setattr(lc.urllib.request, "urlopen", handler)
    client = lc.LicenseClient(["http://srv1", "http://srv2"])
    result = client.activate("K", "m")
    assert result["lease"] == "L2"
    assert handler.calls[0].startswith("http://srv1")
    assert handler.calls[1].startswith("http://srv2")


def test_http_error_raises_license_error(monkeypatch):
    handler = _FakeHandler({"/api/v1/activate": (403, {"error": "chave_invalida"})})
    monkeypatch.setattr(lc.urllib.request, "urlopen", handler)
    client = lc.LicenseClient(["http://srv"])
    with pytest.raises(lc.LicenseError) as exc_info:
        client.activate("BAD", "m")
    assert "chave" in str(exc_info.value)


def test_trial_report(monkeypatch):
    handler = _FakeHandler({"/api/v1/trial/report": (200, {"remaining_seconds": 30})})
    monkeypatch.setattr(lc.urllib.request, "urlopen", handler)
    client = lc.LicenseClient(["http://srv"])
    result = client.trial_report("mid", 120)
    assert result["remaining_seconds"] == 30
