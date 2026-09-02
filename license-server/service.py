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
