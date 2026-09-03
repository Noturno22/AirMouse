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


def _valid_es256_lease(machine_id, private_key):
    """Gera um JWT ES256 genuíno (PyJWT) para verificar o caminho POSITIVO da
    verificação local (raw r||s -> DER) e a idempotência/reload do lease."""
    import jwt
    now = int(time.time())
    payload = {
        "sub": f"machine:{machine_id}",
        "key_hash": "abc",
        "tier": "pro",
        "exp": now + 7 * 24 * 3600,
        "iat": now,
        "revocation_nonce": 0,
        "use_seq": 1,
        "session_id": "s",
        "server_time": now,
    }
    return jwt.encode(payload, private_key, algorithm="ES256")


def test_valid_es256_lease_accepted_and_revalidated():
    from cryptography.hazmat.primitives.asymmetric import ec

    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=60, public_key=pub)
    lm.lease = _valid_es256_lease(lm._machine, priv)
    lm.tier = lic.Tier.PRO
    # lease genuíno → PRO offline válido, NUNCA bloqueado (mesmo com repetição)
    assert lm.is_pro_offline_valid()
    assert not lm.is_blocked()
    assert not lm.is_blocked()  # revalidar o mesmo lease não o torna inválido


def test_valid_es256_lease_survives_save_and_reload(tmp_path):
    from cryptography.hazmat.primitives.asymmetric import ec

    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    store = str(tmp_path / "lic.json")
    lm = lic.LicenseManager(store_path=store, trial_seconds=60, public_key=pub)
    lm.lease = _valid_es256_lease(lm._machine, priv)
    lm.tier = lic.Tier.PRO
    lm.save()

    # recarregar de disco: o mesmo lease (mesmo use_seq) tem de continuar válido
    lm2 = lic.LicenseManager(store_path=store, trial_seconds=60, public_key=pub)
    assert lm2.tier is lic.Tier.PRO
    assert not lm2.is_blocked()


