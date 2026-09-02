"""Core business logic: key issuance, machine binding, trial, leases."""
import hashlib
import os
import secrets
import time

from storage import insert_key

_ADMIN_TOKEN = os.getenv("AIRMOUSE_LS_ADMIN_TOKEN", "dev-admin-token")
_PREFIX = "MAO-"
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def _format_key(body: str) -> str:
    groups = [body[i:i + 5] for i in range(0, len(body), 5)]
    return _PREFIX + "-".join(groups)


def issue_key_email_hash(email: str) -> str:
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()[:10].upper()


def issue_key(conn, email: str) -> str:
    email_hash = issue_key_email_hash(email)
    nonce = secrets.token_hex(4).upper()
    body = f"PRO{email_hash}{nonce}"
    key = _format_key(body)
    from storage import hash_key
    insert_key(conn, hash_key(key), email)
    return key


def authorized(token: str) -> bool:
    return token == _ADMIN_TOKEN


import secrets

from security import issue_lease
from storage import (bind_machine, hash_key, key_exists, machine_for_key)


def get_current_nonce_helper(conn) -> int:
    from storage import get_revocation_nonce
    return get_revocation_nonce(conn)


from storage import get_trial, set_trial_used, TRIAL_MAX_SECONDS


def trial_remaining(conn, machine_id: str) -> int:
    row = get_trial(conn, machine_id)
    used = row["used_seconds"] if row else 0
    return max(0, TRIAL_MAX_SECONDS - used)


def trial_report(conn, machine_id: str, used_seconds: int) -> int:
    """Persiste o uso reportado (nunca diminui — ver storage.set_trial_used) e
    devolve o restante."""
    used_seconds = max(0, int(used_seconds))
    set_trial_used(conn, machine_id, used_seconds)
    return trial_remaining(conn, machine_id)


from security import decode_jwt, issue_lease
from storage import (set_last_use_seq, get_last_use_seq, touch_last_seen,
                     delete_machine, bump_revocation_nonce)


def revalidate(conn, machine_id: str, old_lease: str) -> str:
    """Valida o lease antigo (assinatura ES256) e emite um novo (7 dias).
    Não renova leases com nonce obsoleto nem seq repetido. Actualiza last_seen."""
    try:
        claims = decode_jwt(old_lease)
    except Exception:
        raise ValueError("lease_invalido")
    if claims["sub"] != f"machine:{machine_id}":
        raise ValueError("maquina_diferente")
    if claims["revocation_nonce"] < get_current_nonce_helper(conn):
        raise ValueError("nonce_obsoleto")
    last_seq = get_last_use_seq(conn, machine_id)
    new_seq = int(claims["use_seq"]) + 1
    if last_seq is not None and new_seq <= last_seq:
        raise ValueError("seq_repetido")
    set_last_use_seq(conn, machine_id, new_seq)
    touch_last_seen(conn, machine_id)
    key_hash = claims["key_hash"]
    return issue_lease(machine_id, key_hash, get_current_nonce_helper(conn),
                       claims["session_id"], new_seq)


def revoke_machine(conn, machine_id: str) -> int:
    delete_machine(conn, machine_id)
    return bump_revocation_nonce(conn)


def activate(conn, key: str, machine_id: str) -> tuple[str, str, int]:
    """Liga uma chave a uma máquina e emite um lease ES256.

    Regra dura: 1 chave = 1 máquina. Se a chave já está ligada a OUTRA máquina,
    levanta ValueError.
    """
    key_hash = hash_key(key)
    if not key_exists(conn, key_hash):
        raise ValueError("chave_invalida")
    locked = machine_for_key(conn, key_hash)
    if locked is not None and locked["machine_id"] != machine_id:
        raise ValueError("chave_ja_em_uso_noutra_maquina")
    if locked is None:
        bind_machine(conn, key_hash, machine_id)
    session_id = secrets.token_hex(16)
    use_seq = int(time.time() * 1000)
    nonce = get_current_nonce_helper(conn)
    lease = issue_lease(machine_id, key_hash, nonce, session_id, use_seq)
    return lease, session_id, use_seq
