"""Core business logic: key issuance, machine binding, trial, leases."""
import hashlib
import os
import secrets
import time

from security import decode_jwt, issue_lease
from storage import (
    TRIAL_MAX_SECONDS,
    bind_machine,
    bump_revocation_nonce,
    delete_machine,
    get_last_use_seq,
    get_revocation_nonce,
    get_trial,
    hash_key,
    insert_key,
    key_exists,
    machine_for_key,
    mobile_purchase_for_token,
    record_mobile_purchase,
    set_last_use_seq,
    set_trial_used,
    touch_last_seen,
)

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
    insert_key(conn, hash_key(key), email)
    return key


def authorized(token: str) -> bool:
    return token == _ADMIN_TOKEN


def get_current_nonce_helper(conn) -> int:
    return get_revocation_nonce(conn)


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


def revalidate(conn, machine_id: str, old_lease: str) -> str:
    """Valida o lease antigo (assinatura ES256) e emite um novo (7 dias).
    Não renova leases com nonce obsoleto nem seq repetido. Actualiza last_seen."""
    try:
        claims = decode_jwt(old_lease)
    except Exception:
        raise ValueError("lease_invalido") from None
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


def mobile_entitle(conn, purchase_token: str, product_id: str,
                   package_name: str, device_id: str, expected_product: str,
                   expected_package: str,
                   validate) -> tuple[str, str, bool]:
    """Desbloqueia 'mobile_pro' via uma compra IAP (Google Play). Single purchase.

    - validate(package_name, product_id, purchase_token) levanta
      PlayValidationError se o token nǜo for vǭlido.
    - Dedup anti-replay por purchase_token (o mesmo token s�� gera entitlement
      uma vez; depois Ǹ reaproveitado sem chamar a API do Google).
    - Devolve (lease, session_id, first_time).
    """
    purchase_token = purchase_token.strip()
    if not purchase_token:
        raise ValueError("token_vazio")
    if product_id != expected_product:
        raise ValueError("produto_errado")
    if package_name != expected_package:
        raise ValueError("pacote_errado")

    key_hash = f"MOB:{hash_key(purchase_token)[:16].upper()}"
    existing = mobile_purchase_for_token(conn, purchase_token)
    if existing is not None:
        session_id = secrets.token_hex(16)
        use_seq = int(time.time() * 1000)
        nonce = get_current_nonce_helper(conn)
        lease = issue_lease(device_id, existing["key_hash"], nonce,
                            session_id, use_seq, tier="mobile_pro")
        return lease, session_id, False

    validate(package_name, product_id, purchase_token)
    record_mobile_purchase(conn, purchase_token, package_name,
                           product_id, device_id, key_hash)
    session_id = secrets.token_hex(16)
    use_seq = int(time.time() * 1000)
    nonce = get_current_nonce_helper(conn)
    lease = issue_lease(device_id, key_hash, nonce, session_id, use_seq,
                        tier="mobile_pro")
    return lease, session_id, True
