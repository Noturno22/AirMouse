"""Tests for local ES256 lease verification (rejeita alg:none / assinatura invalida)."""
import base64
import json as _json
import time

import core.licensing as lic


def _unsigned_jwt(machine_id, **over):
    """Monta um JWT SEM assinatura válida (cabeçalho alg:none) — deve ser REJEITADO."""
    now = int(time.time())
    payload = {
        "sub": f"machine:{machine_id}",
        "key_hash": "abc",
        "tier": "pro",
        "exp": over.get("exp", now + 7 * 24 * 3600),
        "iat": over.get("iat", now),
        "revocation_nonce": 0,
        "use_seq": 1,
        "session_id": "s",
        "server_time": now,
    }
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(
        _json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}.sig"


def test_alg_none_lease_rejected(tmp_path):
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=60)
    lm.lease = _unsigned_jwt(lm._machine)
    lm.tier = lic.Tier.PRO
    # assinatura inválida / alg:none -> NÃO conceder PRO
    assert lm.is_blocked()
    assert not lm.is_pro_offline_valid()


def test_lease_from_other_machine_invalid(tmp_path):
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=60)
    lm.lease = _unsigned_jwt("OTHER-MACHINE")
    lm.tier = lic.Tier.PRO
    assert lm.is_blocked()
