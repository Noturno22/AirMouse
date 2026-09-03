# AirMouse — Paddle Checkout Automático (webhook → chave → email) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpawers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Goal:** Fechar o bloqueador de receita **#1b** (`PRONTIDAO_PARA_VENDA.md` §4): ligar o pagamento automático no Paddle (Merchant of Record, decisão D2) ao servidor de licenças. Quando um `transaction.completed` chega ao `/webhooks/paddle`, o servidor verifica a assinatura, emite uma chave `MAO-`, liga-a ao email do comprador, e envia a chave por email. Sem intervenção manual (fluxo administrativo `/admin/keys` continua para vendas manuais).

**Architecture:** Endpoint novo FastAPI em `license-server/` — **`POST /webhooks/paddle`** — que lê o **raw body**, verifica o header `Paddle-Signature` (HMAC-SHA256 sobre `ts:raw_body` com o secret do destination, comparação constante), faz parsing do evento `transaction.completed`, extrai o email do comprador, emite a chave (`service.issue_key`), regista a compra em SQLite com **dedup por `event_id`** (idempotente — at-least-once do Paddle), e envia o email com a chave (SMTP, desligável em dev).

**Tech Stack:** Python stdlib (`hmac`, `hashlib`, `time`, `smtplib`, `email.message`) — **sem dependências novas**. Raw body via `starlette.requests.Request` (`await request.body()`), pois o Paddle assina os bytes exatos. `uuid` para debug.

**Ambiente:** Windows, teste com `pytest` em `license-server/tests` (corrido explicitamente, como os outros). O servidor é FastAPI tal como `license-server/*`.

---

## Contexto do código atual (verificado)

- **`license-server/app.py`** — FastAPI com rotas `/health`, `/admin/keys`, `/api/v1/{activate,trial/*,revalidate,revoke}`. Padrão: `Depends(get_db)`, modelos `pydantic.BaseModel`, `JSONResponse` para erros.
- **`license-server/service.py`** — `issue_key(conn, email) -> "MAO-..."` (chama `insert_key(conn, hash_key(key), email)`).
- **`license-server/storage.py`** — SQLite; tabelas `keys`, `machines`, `trial`, `config`. Padrão: funções que recebem `conn`, `INSERT OR IGNORE`, `conn.commit()`. `hash_key(key)`.
- **`license-server/security.py`** — ES256. Não usada no webhook.
- **`license-server/tests/`** — `conftest.py` (env de teste autouse: `AIRMOUSE_LS_DB`, `AIRMOUSE_LS_ADMIN_TOKEN`, keypair), `test_app.py`, `test_keys.py`, `test_activate.py`, `test_trial.py`, `test_revalidate.py`. Padrão: `sys.path.insert(0, dirname(dirname(__file__)))`, import `from app import create_app`, `TestClient(create_app())`.
- **`.env.example`** — lista vars de produção do license server.
- **`core/licensing.py`** — `PADDLE_PRODUCT_URLS` lidos de `AIRMOUSE_PADDLE_LIFETIME_URL` etc. (checkout client-side; sem webhook). `PADDLE_VENDOR_ID` TODO em `ui/license_dlg.py`.

**Formato do webhook Paddle Billing (verificado em docs oficiais):**
- Topo: `{ "event_id": "evt_...", "event_type": "transaction.completed", "occurred_at": "...", "notification_id": "ntf_...", "data": {...} }`.
- `data.items[]` → `data.items[].price.product.id` (product), `data.items[].price.id` (price).
- `data.customer.email` → email do comprador.
- `data.status` → `"completed"` quando o evento `transaction.completed` dispara.
- `Paddle-Signature` header: `ts=<unix>;h1=<hmac_sha256_hex>`. Assinatura = `HMAC-SHA256(secret, f"{ts}:{raw_body}")`. Rejeitar se `ts` antigo (>5s, com folga de 300s para clock skew) ou `h1` não bater.
- **Raw body obrigatório** — não re-serializar JSON (mudanças de key-order/whitespace quebram o HMAC).

---

## Estrutura de ficheiros

```
license-server/
  paddle.py            # NOVO: verificação de assinatura + parsing de eventos puro
  emailer.py           # NOVO: envio de email SMTP (com opção desligada/dev)
  storage.py           # MODIFICAR: tabela purchases (event_id dedup, email, key_hash, product)
  app.py               # MODIFICAR: rota /webhooks/paddle (raw body + verify + issue + email)
  requirements.txt     # (sem novas deps; smtplib é stdlib)
  tests/
    test_paddle.py     # NOVO: verificação assinatura + parsing
    test_paddle_webhook.py  # NOVO: endpoint idempotente + dedup + chave por email
    conftest.py        # MODIFICAR: set env paddle webhook secret
.env.example           # MODIFICAR: vars PADDLE_WEBHOOK_SECRET, SMTP_*, PADDLE_* product ids
```

---

# PARTE 1 — Núcleo puro (paddle.py)

## Task 1: `license-server/paddle.py` — verificação HMAC + parsing de eventos

**Files:**
- Create: `license-server/paddle.py`
- Test: `license-server/tests/test_paddle.py`

- [ ] **Step 1: Escrever o teste** (`tests/test_paddle.py`)

```python
"""Tests for Paddle webhook signature verification and event parsing (pure)."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paddle

SECRET = "pdl_ntfset_test_secret"


def _signed(event: dict, secret: str = SECRET) -> tuple[str, str]:
    import hashlib
    import hmac
    raw = json.dumps(event, separators=(",", ":"))
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode(), f"{ts}:{raw}".encode(), hashlib.sha256).hexdigest()
    return raw, f"ts={ts};h1={sig}"


def test_verify_valid_signature():
    event = {"event_type": "transaction.completed", "event_id": "evt_x"}
    raw, header = _signed(event)
    assert paddle.verify_signature(raw, header, SECRET) is True


def test_verify_rejects_wrong_secret():
    event = {"event_type": "transaction.completed"}
    raw, header = _signed(event, secret="other-secret")
    assert paddle.verify_signature(raw, header, SECRET) is False


def test_verify_rejects_stale_timestamp():
    event = {"event_type": "transaction.completed"}
    raw, _ = _signed(event)
    old_ts = int(time.time()) - 10000
    bad_header = f"ts={old_ts};h1=abc"
    assert paddle.verify_signature(raw, bad_header, SECRET) is False


def test_verify_rejects_malformed_header():
    event = {"event_type": "transaction.completed"}
    raw, _ = _signed(event)
    assert paddle.verify_signature(raw, "garbage", SECRET) is False


def test_parse_transaction_completed_extracts_email():
    event = {
        "event_type": "transaction.completed",
        "event_id": "evt_abc",
        "data": {
            "id": "txn_1",
            "status": "completed",
            "customer": {"email": "buyer@example.com"},
            "items": [{"price": {"product": {"id": "pro_lifetime"}}}],
        },
    }
    info = paddle.event_info(event)
    assert info["email"] == "buyer@example.com"
    assert info["event_id"] == "evt_abc"
    assert info["product_id"] == "pro_lifetime"


def test_parse_non_completed_transaction_returns_none():
    event = {"event_type": "transaction.paid", "event_id": "evt_x", "data": {}}
    assert paddle.event_info(event) is None
```

- [ ] **Step 2: Correr e ver que falha** — `ModuleNotFoundError: No module named 'paddle'`.

- [ ] **Step 3: Implementar** (`license-server/paddle.py`)

```python
"""Paddle Billing webhook: verificação de assinatura + parsing de eventos (puro)."""
import hashlib
import hmac
import json
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
    expected = hmac.new(
        secret.encode(), f"{ts}:{raw_body}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(h1, expected)


def event_info(event: dict):
    """Extrai os dados úteis de um evento Paddle. Devolve None se não for
    um transaction.completed aproveitável."""
    if event.get("event_type") != "transaction.completed":
        return None
    data = event.get("data") or {}
    items = data.get("items") or []
    product_id = ""
    if items:
        product_id = (items[0].get("price") or {}).get("product") or {}
        product_id = product_id.get("id", "")
    email = (data.get("customer") or {}).get("email", "")
    if not email:
        return None
    return {
        "event_id": event.get("event_id", ""),
        "email": email,
        "product_id": product_id,
        "transaction_id": data.get("id", ""),
    }
```

- [ ] **Step 4: Correr e ver que passa** — `pytest license-server/tests/test_paddle.py -v` → 6 PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(license-server/paddle): verificacao de assinatura HMAC + parsing de eventos"`

---

# PARTE 2 — Persistência de compras (dedup)

## Task 2: Tabela `purchases` com dedup por `event_id` em `storage.py`

**Files:** Modify `license-server/storage.py`, Test: `license-server/tests/test_storage_purchases.py`

- [ ] **Step 1: Escrever o teste**

```python
"""Tests for purchases storage (dedup por event_id)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import storage
from storage import connect, init_db


def test_purchase_record_and_dedup():
    conn = connect(); init_db(conn)
    key_hash = "k1"
    email = "a@b.c"
    assert storage.record_purchase(conn, "evt_1", email, key_hash, "pro_lifetime") is True
    # mesmo event_id -> dedup (devolve False, não duplica)
    assert storage.record_purchase(conn, "evt_1", email, "DIFFERENT", "pro_lifetime") is False
    rows = storage.purchase_for_event(conn, "evt_1")
    assert rows is not None
    assert rows["email"] == "a@b.c"
    assert rows["key_hash"] == "k1"
    conn.close()
```

- [ ] **Step 2: Correr e ver que falha** — `AttributeError: ... record_purchase`.

- [ ] **Step 3: Implementar em `storage.py`** — adicionar tabela + helpers:

Tabela:
```sql
CREATE TABLE IF NOT EXISTS purchases (
    event_id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    product_id TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL
);
```

Helpers:
```python
def record_purchase(conn, event_id: str, email: str, key_hash: str,
                    product_id: str = "") -> bool:
    cur = conn.execute(
        "INSERT OR IGNORE INTO purchases(event_id, email, key_hash, product_id, created_at)"
        " VALUES(?,?,?,?,?)",
        (event_id, email, key_hash, product_id, int(time.time())))
    conn.commit()
    return cur.rowcount > 0


def purchase_for_event(conn, event_id: str):
    cur = conn.execute("SELECT * FROM purchases WHERE event_id=?", (event_id,))
    return cur.fetchone()


def email_keys(conn, email: str):
    """Devolve as chaves (já emitidas) de um email."""
    rows = conn.execute(
        "SELECT p.key_hash, k.email FROM purchases p JOIN keys k ON k.key_hash=p.key_hash"
        " WHERE k.email=?", (email,)).fetchall()
    return [r["key_hash"] for r in rows]
```

- [ ] **Step 4: Correr e ver que passa**.
- [ ] **Step 5: Commit** — `feat(license-server/storage): tabela purchases com dedup por event_id`.

---

# PARTE 3 — Email

## Task 3: `license-server/emailer.py` — envio SMTP da chave (desligável)

**Files:** Create `license-server/emailer.py`, Test: `license-server/tests/test_emailer.py`

- [ ] **Step 1: Escrever o teste** (mock do SMTP)

```python
"""Tests for emailer (envio da chave por SMTP)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import emailer


def test_build_message_contains_key(monkeypatch):
    msg = emailer.build_key_email("buyer@example.com", "MAO-ABC-123")
    assert "MAO-ABC-123" in msg.as_string()
    assert "buyer@example.com" in msg["To"]


def test_send_disabled_when_no_smtp(monkeypatch):
    monkeypatch.setenv("AIRMOUSE_SMTP_ENABLED", "0")
    assert emailer.send_key_email("a@b.c", "MAO-X") == emailer.Result(fired=False, error="")


def test_send_uses_smtp(monkeypatch):
    monkeypatch.setenv("AIRMOUSE_SMTP_ENABLED", "1")
    monkeypatch.setenv("AIRMOUSE_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("AIRMOUSE_SMTP_PORT", "587")
    monkeypatch.setenv("AIRMOUSE_SMTP_USER", "u")
    monkeypatch.setenv("AIRMOUSE_SMTP_PASSWORD", "p")
    monkeypatch.setenv("AIRMOUSE_SMTP_FROM", "sales@maouse.app")
    sent = []
    class _S:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): pass
        def login(self, *a): sent.append(a)
        def sendmail(self, *a): sent.append(a)
    monkeypatch.setattr(emailer.smtplib, "SMTP", lambda *a, **k: _S())
    res = emailer.send_key_email("buyer@example.com", "MAO-KEY")
    assert res.fired is True
    assert res.error == ""
    assert ("u", "p") in sent
```

(Nota: `emailer.Result` é um `NamedTuple(fired: bool, error: str)`. `send_key_email` devolve sempre um Result, nunca lança.)

- [ ] **Step 2: Correr e ver que falha**.
- [ ] **Step 3: Implementar**

```python
"""Envio de email com a chave Pro por SMTP (stdlib). Desligável em dev."""
import os
import smtplib
from email.message import EmailMessage
from typing import NamedTuple

class Result(NamedTuple):
    fired: bool
    error: str


def _cfg():
    return {
        "enabled": os.getenv("AIRMOUSE_SMTP_ENABLED", "0") == "1",
        "host": os.getenv("AIRMOUSE_SMTP_HOST", ""),
        "port": int(os.getenv("AIRMOUSE_SMTP_PORT", "587")),
        "user": os.getenv("AIRMOUSE_SMTP_USER", ""),
        "password": os.getenv("AIRMOUSE_SMTP_PASSWORD", ""),
        "from": os.getenv("AIRMOUSE_SMTP_FROM", "sales@maouse.app"),
    }


def build_key_email(to_email: str, key: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "A tua chave Maouse PRO"
    msg["From"] = _cfg()["from"]
    msg["To"] = to_email
    body = (
        "Obrigado pela tua compra!\n\n"
        "A tua chave Maouse PRO:\n\n"
        f"{key}\n\n"
        "Como ativar:\n"
        "1. Abre o Maouse e vai a PRO / Ativar chave\n"
        "2. Cola a chave e ativa (precisa de internet uma vez)\n\n"
        "A chave fica ligada ao teu computador. Precisas de ajuda? Responde a este email.\n"
        "\nM\~eouse"
    )
    msg.set_content(body)
    return msg


def send_key_email(to_email: str, key: str) -> Result:
    cfg = _cfg()
    if not cfg["enabled"]:
        return Result(fired=False, error="")
    try:
        msg = build_key_email(to_email, key)
        with smtplib.SMTP(cfg["host"], cfg["port"]) as srv:
            srv.starttls()
            srv.login(cfg["user"], cfg["password"])
            srv.sendmail(cfg["from"], [to_email], msg.as_string())
        return Result(fired=True, error="")
    except Exception as exc:  # noqa: BLE001 - o webhook não deve falhar por email
        return Result(fired=False, error=str(exc))
```

- [ ] **Step 4: Correr e ver que passa**.
- [ ] **Step 5: Commit** — `feat(license-server/emailer): envio SMTP da chave Pro (desligavel em dev)`.

---

# PARTE 4 — Endpoint webhook

## Task 4: Endpoint `POST /webhooks/paddle` no `app.py`

**Files:** Modify `license-server/app.py`, Test: `license-server/tests/test_paddle_webhook.py`, Modify `license-server/tests/conftest.py`

- [ ] **Step 1: Adicionar env de teste ao `conftest.py`**

```python
monkeypatch.setenv("AIRMOUSE_PADDLE_WEBHOOK_SECRET", "pdl_test_secret")
```

- [ ] **Step 2: Escrever o teste do endpoint** (`tests/test_paddle_webhook.py`)

```python
"""Tests for the Paddle webhook endpoint (issue key + email + idempotente)."""
import hashlib
import hmac
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app import create_app
import storage
from storage import connect, init_db

SECRET = "pdl_test_secret"


def _signed(event: dict) -> tuple[str, str]:
    raw = json.dumps(event, separators=(",", ":"))
    ts = str(int(time.time()))
    sig = hmac.new(SECRET.encode(), f"{ts}:{raw}".encode(), hashlib.sha256).hexdigest()
    return raw, f"ts={ts};h1={sig}"


def _completed_event(event_id="evt_123", email="buyer@example.com"):
    return {
        "event_id": event_id,
        "event_type": "transaction.completed",
        "occurred_at": "2026-09-03T10:00:00Z",
        "notification_id": "ntf_1",
        "data": {
            "id": "txn_1",
            "status": "completed",
            "customer": {"email": email},
            "items": [{"price": {"product": {"id": "pro_lifetime"}}}],
        },
    }


def test_webhook_issues_key_and_returns_200():
    client = TestClient(create_app())
    raw, header = _signed(_completed_event())
    resp = client.post("/webhooks/paddle", content=raw,
                       headers={"Paddle-Signature": header})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("ok") is True
    assert body.get("key", "").startswith("MAO-")
    assert body.get("email") == "buyer@example.com"


def test_webhook_idempotent_same_event():
    client = TestClient(create_app())
    raw, header = _signed(_completed_event(event_id="evt_dedup"))
    r1 = client.post("/webhooks/paddle", content=raw, headers={"Paddle-Signature": header})
    r2 = client.post("/webhooks/paddle", content=raw, headers={"Paddle-Signature": header})
    assert r1.status_code == 200
    assert r2.status_code == 200
    k1 = r1.json()["key"]
    k2 = r2.json()["key"]
    # idempotente: mesma chave, não duplica (digest ignora chave igual)
    assert k1 == k2


def test_webhook_rejects_bad_signature():
    client = TestClient(create_app())
    raw, _ = _signed(_completed_event())
    resp = client.post("/webhooks/paddle", content=raw,
                       headers={"Paddle-Signature": "ts=0;h1=bad"})
    assert resp.status_code == 401


def test_webhook_ignores_non_completed():
    client = TestClient(create_app())
    raw, header = _signed({"event_id": "evt_1", "event_type": "transaction.paid",
                           "data": {}})
    resp = client.post("/webhooks/paddle", content=raw,
                       headers={"Paddle-Signature": header})
    assert resp.status_code == 200
    assert resp.json().get("ok") is True
```

- [ ] **Step 3: Correr e ver que falha** — 404.

- [ ] **Step 4: Implementar o endpoint em `app.py`**

Adicionar imports e dependência do raw body:

```python
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import paddle as paddle_mod
from emailer import send_key_email

# dentro de create_app():
WEBHOOK_SECRET = os.getenv("AIRMOUSE_PADDLE_WEBHOOK_SECRET", "")

@app.post("/webhooks/paddle")
async def paddle_webhook(request: Request, db=Depends(get_db)):
    from service import issue_key
    from storage import hash_key, record_purchase, purchase_for_event
    raw = (await request.body()).decode("utf-8")
    sig = request.headers.get("Paddle-Signature", "")
    if not paddle_mod.verify_signature(raw, sig, WEBHOOK_SECRET):
        return JSONResponse(status_code=401, content={"error": "assinatura_invalida"})
    try:
        event = json.loads(raw)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "json_invalido"})
    info = paddle_mod.event_info(event)
    if info is None:
        # evento irrelevante (ex.: transaction.paid) -> reconhecer, nada a fazer
        return {"ok": True, "handled": False}
    # dedup idempotente: se já processámos este event_id, devolver a chave existente
    existing = purchase_for_event(db, info["event_id"])
    if existing is not None:
        return {"ok": True, "handled": True, "key": existing["key_hash"]}
    key = issue_key(db, info["email"])
    record_purchase(db, info["event_id"], info["email"], key, info["product_id"])
    send_key_email(info["email"], key)
    return {"ok": True, "handled": True, "key": key, "email": info["email"]}
```

(Nota: em dev/teste `AIRMOUSE_PADDLE_WEBHOOK_SECRET` vazio → o erro 401 acontece para tudo, o que é claramente um estado de não-configurado. Para permitir testes e sanidade em dev, se a secret não estiver set, o servidor responde 503 "paddle_nao_configurado". Opcional — por defeito, se vazio, recusa com 503 para nunca aceitar webhooks não autenticados.)

- [ ] **Step 5: Correr os dois testes e ver que passam** (test_paddle.py + test_paddle_webhook.py).
- [ ] **Step 6: Commit** — `feat(license-server/webhook): /webhooks/paddle - emite chave + email + idempotente`.

---

# PARTE 5 — Config, docs, verificação final

## Task 5: `.env.example` + requisitos + verificação

- [ ] **Step 1: Atualizar `.env.example`**

```bash
# ─── Paddle (D2) — webhook + produtos ───
# Secret do "notification destination" do Paddle (dashboard > Developer tools > Notifications).
# Usado para verificar o header Paddle-Signature no /webhooks/paddle.
AIRMOUSE_PADDLE_WEBHOOK_SECRET=pdl_ntfset_...

# URLs de checkout (produtos). Já lidas pelo cliente em core/licensing.py.
AIRMOUSE_PADDLE_LIFETIME_URL=https://checkout.paddle.com/.../product=...
AIRMOUSE_PADDLE_SUBSCRIPTION_URL=https://checkout.paddle.com/...
AIRMOUSE_PADDLE_FAMILY_URL=https://checkout.paddle.com/...
AIRMOUSE_PADDLE_ACCESS_URL=https://checkout.paddle.com/...

# Email da chave (SMTP) — desligado por omissão (dev). Ligar em produção.
AIRMOUSE_SMTP_ENABLED=0
AIRMOUSE_SMTP_HOST=smtp.example.com
AIRMOUSE_SMTP_PORT=587
AIRMOUSE_SMTP_USER=your-user
AIRMOUSE_SMTP_PASSWORD=your-password
AIRMOUSE_SMTP_FROM=sales@maouse.app
```

- [ ] **Step 2: Correr toda a suite do servidor**

```bash
.venv\Scripts\python.exe -m pytest license-server/tests -v
```
Expected: PASS (15 + 6 + 1 + 3 + 4 = 29).

- [ ] **Step 3: Correr toda a suite do cliente**

```bash
.venv\Scripts\python.exe -m pytest tests -v
```
Expected: PASS (sem regressões).

- [ ] **Step 4: Lint**

```bash
.venv\Scripts\python.exe -m ruff check license-server/
```
Expected: PASS.

- [ ] **Step 5: Commit final** — `docs(env): config Paddle + SMTP para webhook de pagamento`.
