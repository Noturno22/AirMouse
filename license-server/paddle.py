"""Paddle Billing webhook: verificação de assinatura + parsing de eventos (puro)."""
import hashlib
import hmac
import time

_MAX_TS_AGE = 300  # 5 min de folga p/ clock skew (Paddle usa 5 s; folga para ambientes)


def verify_signature(raw_body: str, signature_header: str, secret: str) -> bool:
    """Verifica o header Paddle-Signature (ts=..;h1=..) sobre o RAW body.

    Assinatura = HMAC-SHA256(secret, f"{ts}:{raw_body}"). Compara em tempo
    constante. Rejeita timestamps antigos (anti-replay).
    """
    parts = {}
    for kv in signature_header.split(";"):
        if "=" in kv:
            k, _, v = kv.partition("=")
            parts[k.strip()] = v.strip()
    ts = parts.get("ts")
    h1 = parts.get("h1")
    if not ts or not h1:
        return False
    try:
        delta = abs(int(time.time()) - int(ts))
    except ValueError:
        return False
    if delta > _MAX_TS_AGE:
        return False
    if not secret:
        return False
    expected = hmac.new(
        secret.encode(), f"{ts}:{raw_body}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(h1, expected)


def event_info(event: dict):
    """Extrai os dados úteis de um evento Paddle. Devolve None se não for
    um transaction.completed aproveitável (email obrigatório)."""
    if event.get("event_type") != "transaction.completed":
        return None
    data = event.get("data") or {}
    items = data.get("items") or []
    product_id = ""
    if items:
        price = items[0].get("price") or {}
        product = price.get("product") or {}
        product_id = product.get("id", "")
    email = (data.get("customer") or {}).get("email", "")
    if not email:
        return None
    return {
        "event_id": event.get("event_id", ""),
        "email": email,
        "product_id": product_id,
        "transaction_id": data.get("id", ""),
    }
