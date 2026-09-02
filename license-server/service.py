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
