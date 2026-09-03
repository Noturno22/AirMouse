# AirMouse License Server + Prova-de-Fogo Implementation Plan (rev. 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpawers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Rev 2 changes (após review):** fecha 2 falhas de segurança críticas + 1 quebra de API:
> 1. **Trial server-authoritative** — o servidor é a fonte da verdade; apagar `license.json` NÃO reinicia os 30 min (aplica o requisito do spec §4.1/§6).
> 2. **Verificação de assinatura do lease no cliente (ES256)** — o cliente valida a assinatura assimétrica localmente; um `license.json` forjado (ex. `alg:none`) NÃO concede PRO offline (spec §4.4/V3).
> 3. **Superfície de API preservada** — `open_checkout`, `deactivate`, `checkout_urls`, `issue_pro_key`, `validate_key`, `LicenseAgency` mantêm-se para não quebrar `ui/license_dlg.py`, `main.py` e `tools/issue_pro_key.py`.

**Goal:** Tornar o AirMouse à prova de fogo: trial Free de 30 min com bloqueio total (pop-up apelativo), ativação online única (1 chave = 1 utilizador = 1 máquina), uso offline com lease de 7 dias revalidado 1x por semana, e eliminar o bypass `--dev-pro`.

**Architecture:** Novo servidor de licenças **FastAPI + SQLite** em `license-server/` que emite chaves ligadas a `machine_id`, controla o trial (fonte de verdade) e emite leases **JWT ES256** (7 dias, `server_time`, `revocation_nonce`, `session_id`/`use_seq`). O cliente (`core/licensing.py` reescrito + `core/fingerprint.py` + `core/license_client.py`) ativa online, guarda o lease, **verifica a assinatura ES256 localmente** com a chave pública embutida, usa offline, e bloqueia no runtime quando o trial/lease expira. O gate de bloqueio entra no `process_frame` (partilhado pelas duas UIs).

**Tech Stack:** Servidor: Python + FastAPI + PyJWT (ES256) + `cryptography` + SQLite (stdlib `sqlite3`). Cliente: Python stdlib (`urllib.request`, `hashlib`) + **`cryptography`** (verificação ES256 local). O cliente continua SEM `requests` (padrão do projeto: `urllib.request`).

**Ambiente:** Windows, Python 3.10+ (projeto usa 3.12/3.14 dev), venv em `.venv`. Testes com `pytest` (config em `pyproject.toml`, testpaths=`tests`). O servidor tem os seus próprios testes em `license-server/tests` (corridos explicitamente).

---

## Pré-requisitos / Contexto do código atual (verificado no review)

- **`core/licensing.py`** (271 linhas) — `LicenseManager(secret, store_path, agency)`, `LicenseAgency`, `Tier`/`PRO_LOCKED`/`entitlements`/`is_pro_locked`, globals `set_active_license`/`active_license`/`active_tier`, e métodos usados externamente: `save/load/issue_pro_key/validate_key/activate/deactivate/is_pro/can/checkout_urls/open_checkout`, `_sign`/`_normalize_key`/`_format_key`/`_default_store_path`. **Estes símbolos mantêm-se** (Task 8 não os remove).
- **`main.py`** — `parse_args()` (linha 47) com `--dev-pro` (90-95); `lic_ = LicenseManager()` (194); `--activate-key` (208) e `--deactivate` (214) chamam `activate`/`deactivate`; `set_active_license(lic_)` (238); gate Free/Pro (238-251); dict `state` (325-333).
- **`core/engine.py:183`** — `process_frame(cfg, cam, tracker, mouse, gesture_ai, voice, tuner, ctx, state, E)`; `engine.py:629` faz short-circuit em `to_render=False` antes de aceder a `ui/fps/all_frames` → o gate que devolve `{"to_render": False}` é seguro nas duas UIs.
- **`config.py:156`** — `Config.license_tier: str = "free"`.
- **`i18n.py`** — `tr(key)`, mapa `_STRINGS` {key:{pt,en}}; sem strings de trial/bloqueio.
- **`ui/main_window.py`** — `_sync_license_ui` (395), `_tick` (438; chama `process_frame` em 469).
- **`ui/license_dlg.py`** — `LicenseDialog`, `PADDLE_VENDOR_ID=0`, `_open_checkout`/`_activate_key`/`_deactivate` (chamam `open_checkout`/`activate`/`deactivate` do manager), `MAIN_STYLESHEET` de `ui.theme`.
- **`tools/issue_pro_key.py`** — chama `LicenseManager().issue_pro_key(email)` com `AIRMOUSE_LICENSE_SECRET` (offline). **Task 8b substitui** por chamada ao servidor `/admin/keys`.
- **`pyproject.toml`** — pytest `testpaths=["tests"]`, `pythonpath=["."]`, `dependencies=[]` no `[project]` (runtime sem deps declaradas). Não há `app.py`/`storage.py` na raiz → o `sys.path.insert(0, licenseserver)` dos testes do servidor resolve `from app import ...` sem conflito; e `testpaths=["tests"]` significa que `pytest` do projeto NÃO descobre `license-server/tests` por defeito (só quando invocados explicitamente).

**Padrão HTTP do projeto:** `urllib.request` (nunca `requests`). Seguir no cliente.

**Token/crypto:** ES256 assimétrico. Servidor assina com **chave privada EC** (PEM, env `AIRMOUSE_LS_PRIVATE_KEY`). Cliente verifica com **chave pública EC embutida** (constante PEM em `core/licensing.py`). A secret HS256 NUNCA vai para o cliente (spec V3).

---

## Estrutura de ficheiros

```
license-server/
  app.py                 # FastAPI app + router + storage init
  storage.py             # SQLite access (chaves, máquinas, trial, config)
  service.py             # lógica de chaves, vínculo, trial, leases
  security.py            # ES256: chave privada, emitir/verificar assinatura, revocation_nonce, server_time
  keys.py                # gerador de keypair EC (dev): gera PEM privado + PEM público
  requirements.txt       # fastapi, uvicorn, PyJWT, cryptography, pytest, httpx
  tests/
    conftest.py          # app/test-client fixture (env de teste)
    test_app.py          # boot + health
    test_keys.py         # emissão de chave /admin/keys
    test_activate.py     # 1 chave = 1 máquina + lease ES256
    test_trial.py        # trial server-side idempotente (não reinicia)
    test_revalidate.py   # revalidate + revoke + nonce + anti-replay
core/
  fingerprint.py         # NOVO: machine_id (hardware)
  license_client.py      # NOVO: cliente HTTP urllib + failover + parsing
  licensing.py           # REESCRITO: trial 30min server-auth, lease ES256 verificado, bloqueio, API preservada
  licensing_public_key.pem  # NOVO: chave pública ES256 embutida p/ verificação offline (gerada em Task 8b)
tests/
  test_fingerprint.py
  test_license_client.py
  test_trial_30min.py
  test_lease.py
  test_license_gate.py
  test_main_flags.py
  test_licensing.py      # ajustar: trial/lease em vez de chave offline HMAC
config.py                # MODIFICAR: add license_server_urls, trial/lease flags
core/engine.py           # MODIFICAR: gate de bloqueio no process_frame
main.py                  # MODIFICAR: remover --dev-pro, ligar trial/lease no arranque
i18n.py                  # MODIFICAR: strings de trial/bloqueio
ui/license_dlg.py        # MODIFICAR: fluxo de ativação online + BlockDialog (sem quebrar open_checkout/deactivate)
tools/issue_pro_key.py   # MODIFICAR: emitir via servidor /admin/keys (não offline)
```

---

# PARTE 1 — Servidor de Licenças (`license-server/`)

## Task 1: Boot do servidor FastAPI + storage SQLite + ES256

**Files:**
- Create: `license-server/storage.py`, `license-server/security.py`, `license-server/keys.py`, `license-server/app.py`, `license-server/requirements.txt`
- Test: `license-server/tests/test_app.py`, `license-server/tests/conftest.py`

- [ ] **Step 1: Escrever o teste de boot/health**

Create `license-server/tests/conftest.py` (define env de teste no autouse):

```python
import os
import pytest


@pytest.fixture(autouse=True)
def _test_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRMOUSE_LS_DB", str(tmp_path / "ls.db"))
    monkeypatch.setenv("AIRMOUSE_LS_SECRET", "test-jwt-secret")
    monkeypatch.setenv("AIRMOUSE_LS_ADMIN_TOKEN", "dev-admin-token")
    from keys import ensure_test_keypair
    ensure_test_keypair(tmp_path)
```

Create `license-server/tests/test_app.py`:

```python
"""Tests for the license-server FastAPI app boot."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app import create_app


def test_health_endpoint():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
```

- [ ] **Step 2: Correr o teste e ver que falha**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests/test_app.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Implementar storage.py**

Create `license-server/storage.py`:

```python
"""SQLite storage for the license server.

Tabelas:
  keys        (key_hash PK, email, created_at)
  machines    (machine_id PK, key_hash, activated_at, last_use_seq, last_seen)
  trial       (machine_id PK, used_seconds, updated_at)
  config      (k PK, v)  -> revocation_nonce global
"""
import hashlib
import os
import sqlite3
import time


def _db_path() -> str:
    return os.getenv("AIRMOUSE_LS_DB", "license_server.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS keys (
            key_hash TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS machines (
            machine_id TEXT PRIMARY KEY,
            key_hash TEXT NOT NULL,
            activated_at INTEGER NOT NULL,
            last_use_seq INTEGER NOT NULL DEFAULT 0,
            last_seen INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS trial (
            machine_id TEXT PRIMARY KEY,
            used_seconds INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS config (
            k TEXT PRIMARY KEY,
            v TEXT NOT NULL
        );
        """
    )
    cur = conn.execute("SELECT v FROM config WHERE k='revocation_nonce'")
    if cur.fetchone() is None:
        conn.execute("INSERT INTO config(k,v) VALUES('revocation_nonce','0')")
    conn.commit()


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


# --- chaves ---
def insert_key(conn, key_hash: str, email: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO keys(key_hash, email, created_at) VALUES(?,?,?)",
        (key_hash, email, int(time.time())))
    conn.commit()


def key_exists(conn, key_hash: str) -> bool:
    cur = conn.execute("SELECT 1 FROM keys WHERE key_hash=?", (key_hash,))
    return cur.fetchone() is not None


# --- máquinas / vínculo ---
def bind_machine(conn, key_hash: str, machine_id: str) -> None:
    conn.execute(
        "INSERT INTO machines(machine_id, key_hash, activated_at) VALUES(?,?,?)",
        (machine_id, key_hash, int(time.time())))
    conn.commit()


def machine_for_key(conn, key_hash: str):
    cur = conn.execute("SELECT machine_id FROM machines WHERE key_hash=?", (key_hash,))
    return cur.fetchone()


def get_last_use_seq(conn, machine_id: str):
    cur = conn.execute("SELECT last_use_seq FROM machines WHERE machine_id=?", (machine_id,))
    row = cur.fetchone()
    return row["last_use_seq"] if row else None


def set_last_use_seq(conn, machine_id: str, seq: int) -> None:
    conn.execute("UPDATE machines SET last_use_seq=? WHERE machine_id=?",
                 (seq, machine_id))
    conn.commit()


def touch_last_seen(conn, machine_id: str) -> None:
    conn.execute("UPDATE machines SET last_seen=? WHERE machine_id=?",
                 (int(time.time()), machine_id))
    conn.commit()


def delete_machine(conn, machine_id: str) -> None:
    conn.execute("DELETE FROM machines WHERE machine_id=?", (machine_id,))
    conn.commit()


# --- revocation_nonce ---
def get_revocation_nonce(conn) -> int:
    cur = conn.execute("SELECT v FROM config WHERE k='revocation_nonce'")
    row = cur.fetchone()
    return int(row["v"]) if row else 0


def bump_revocation_nonce(conn) -> int:
    n = get_revocation_nonce(conn) + 1
    conn.execute("UPDATE config SET v=? WHERE k='revocation_nonce'", (str(n),))
    conn.commit()
    return n


# --- trial (fonte de verdade) ---
TRIAL_MAX_SECONDS = 30 * 60


def get_trial(conn, machine_id: str):
    cur = conn.execute("SELECT used_seconds FROM trial WHERE machine_id=?", (machine_id,))
    return cur.fetchone()


def set_trial_used(conn, machine_id: str, seconds: int) -> None:
    conn.execute(
        "INSERT INTO trial(machine_id, used_seconds, updated_at) VALUES(?,?,?) "
        "ON CONFLICT(machine_id) DO UPDATE SET "
        "used_seconds=MAX(trial.used_seconds, excluded.used_seconds),"
        "updated_at=excluded.updated_at",
        (machine_id, seconds, int(time.time())))
    conn.commit()
```

Nota: `set_trial_used` usa `MAX(...)` para nunca reduzir o uso já registado (trial nunca reinicia no servidor).

- [ ] **Step 4: Implementar security.py (ES256)**

Create `license-server/security.py`:

```python
"""ES256 JWT lease: assinatura assimétrica + revocation_nonce + server_time.

O servidor assina com chave PRIVADA EC; o cliente verifica com a PÚBLICA.
A secret simétrica NUNCA sai do servidor (spec V3).
"""
import base64
import os
import time

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

LEASE_TTL_SECONDS = 7 * 24 * 3600
CLOCK_SKEW_TOLERANCE = 600


def _private_key_path() -> str:
    return os.getenv("AIRMOUSE_LS_PRIVATE_KEY",
                     os.path.join(os.path.dirname(__file__), "private.pem"))


def _load_private_key():
    p = _private_key_path()
    with open(p, "rb") as fh:
        return serialization.load_pem_private_key(fh.read(), password=None)


def sign(claims: dict) -> str:
    """Assina um dict de claims e devolve o JWT ES256."""
    key = _load_private_key()
    return jwt.encode(claims, key, algorithm="ES256")


def issue_lease(machine_id: str, key_hash: str, revocation_nonce: int,
                session_id: str, use_seq: int) -> str:
    now = int(time.time())
    claims = {
        "sub": f"machine:{machine_id}",
        "key_hash": key_hash,
        "tier": "pro",
        "session_id": session_id,
        "use_seq": use_seq,
        "revocation_nonce": revocation_nonce,
        "iat": now,
        "nbf": now - CLOCK_SKEW_TOLERANCE,
        "exp": now + LEASE_TTL_SECONDS,
        "server_time": now,
    }
    return sign(claims)


def decode_jwt(token: str) -> dict:
    """Decodifica + verifica a assinatura ES256 usando a chave pública embutida
    (não confia em 'alg:none')."""
    from cryptography.hazmat.primitives import serialization as _ser

    pub_pem = os.getenv("AIRMOUSE_LS_PUBLIC_KEY", "")
    key = _ser.load_pem_public_key(pub_pem.encode()) if pub_pem \
        else _load_public_key_embedded()
    return jwt.decode(token, key, algorithms=["ES256"])
```

(Nota: para o servidor os testes usam `AIRMOUSE_LS_PUBLIC_KEY`; `_load_public_key_embedded` lê o mesmo ficheiro `public.pem` da chave emparelhada. Ver Task 1 Step 5.)

- [ ] **Step 5: Implementar keys.py (gerador de keypair EC para dev/teste)**

Create `license-server/keys.py`:

```python
"""Gera o keypair EC P-256 (privada no servidor, pública no cliente) em dev/teste."""
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def generate_keypair() -> tuple[bytes, bytes]:
    priv = ec.generate_private_key(ec.SECP256R1())
    priv_pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption())
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv_pem, pub_pem


def ensure_test_keypair(tmp) -> tuple[str, str]:
    priv_pem, pub_pem = generate_keypair()
    priv_f = os.path.join(str(tmp), "private.pem")
    pub_f = os.path.join(str(tmp), "public.pem")
    with open(priv_f, "wb") as fh:
        fh.write(priv_pem)
    with open(pub_f, "wb") as fh:
        fh.write(pub_pem)
    os.environ["AIRMOUSE_LS_PRIVATE_KEY"] = priv_f
    os.environ["AIRMOUSE_LS_PUBLIC_KEY"] = pub_f
    return priv_f, pub_f
```

E em `security.py`, `_load_public_key_embedded` (usada quando `AIRMOUSE_LS_PUBLIC_KEY` não está set) deve ler `public.pem` ao lado de `private.pem`:

```python
def _load_public_key_embedded():
    from cryptography.hazmat.primitives import serialization as _ser
    pub = os.path.join(os.path.dirname(os.path.dirname(_private_key_path())), "public.pem")
    with open(pub, "rb") as fh:
        return _ser.load_pem_public_key(fh.read())
```

(Nota do executor: o objetivo é o servidor ter a par chave {privada, pública}; a pública será a mesma embutida no cliente em `core/licensing_public_key.pem`. Em dev/teste usa-se o keypair gerado; em produção o `AIRMOUSE_LS_PRIVATE_KEY` aponta para a privada real e a pública correspondente é gravada em `core/licensing_public_key.pem`.)

- [ ] **Step 6: Implementar app.py (boot + health)**

Create `license-server/app.py`:

```python
"""FastAPI app for the AirMouse License Server."""
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from storage import connect, init_db


def get_db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def create_app() -> FastAPI:
    app = FastAPI(title="AirMouse License Server")

    @app.on_event("startup")
    def _startup():
        conn = connect()
        init_db(conn)
        conn.close()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 7: Criar requirements.txt**

Create `license-server/requirements.txt`:

```
fastapi>=0.110
uvicorn[standard]>=0.29
PyJWT>=2.8
cryptography>=42
pytest>=8
httpx>=0.27
```

(Instalar com `.venv\Scripts\python.exe -m pip install -r license-server/requirements.txt` antes de correr os testes do servidor.)

- [ ] **Step 8: Correr o teste e ver que passa**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests/test_app.py -v`
Expected: PASS (1 test).

- [ ] **Step 9: Commit**

```bash
git add license-server/
git commit -m "feat(license-server): boot FastAPI + storage SQLite + health + ES256 keypair"
```

---

## Task 2: Emissão e armazenamento de chaves (server)

**Files:**
- Modify: `license-server/service.py` (novo), `license-server/app.py`
- Test: `license-server/tests/test_keys.py`

- [ ] **Step 1: Escrever o teste de emissão/armazenamento de chave**

Create `license-server/tests/test_keys.py`:

```python
"""Tests for key issuance and storage on the license server."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app import create_app


def _client():
    return TestClient(create_app())


def test_admin_issue_key():
    client = _client()
    resp = client.post("/admin/keys", json={
        "email": "tester@example.com", "admin_token": "dev-admin-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["key"].startswith("MAO-")
    assert data["email"] == "tester@example.com"


def test_admin_issue_rejects_bad_token():
    client = _client()
    resp = client.post("/admin/keys", json={
        "email": "a@b.c", "admin_token": "wrong"})
    assert resp.status_code == 403
```

- [ ] **Step 2: Correr o teste e ver que falha**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests/test_keys.py -v`
Expected: FAIL — 404 (rota não existe).

- [ ] **Step 3: Implementar service.py (emissão de chave)**

Create `license-server/service.py`:

```python
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
```

- [ ] **Step 4: Adicionar a rota /admin/keys em app.py**

Adicionar em `license-server/app.py` (junto aos imports e campos BaseModel):

```python
from service import authorized, issue_key


class KeyRequest(BaseModel):
    email: str
    admin_token: str


class KeyResponse(BaseModel):
    key: str
    email: str


@app.post("/admin/keys")
def admin_issue_key(req: KeyRequest, db=Depends(get_db)):
    if not authorized(req.admin_token):
        return JSONResponse(status_code=403, content={"error": "forbidden"})
    key = issue_key(db, req.email)
    return KeyResponse(key=key, email=req.email)
```

- [ ] **Step 5: Correr os testes e ver que passam**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests/test_keys.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add license-server/
git commit -m "feat(license-server): emissao e armazenamento de chaves MAO-"
```

---

## Task 3: Vínculo 1 chave = 1 máquina + activate (lease ES256)

**Files:**
- Modify: `license-server/service.py`, `license-server/app.py`
- Test: `license-server/tests/test_activate.py`

- [ ] **Step 1: Escrever o teste de activate (vínculo máquina + assinatura)**

Create `license-server/tests/test_activate.py`:

```python
"""Tests for activate: 1 key = 1 machine hard rule + ES256-signed lease."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jwt
from fastapi.testclient import TestClient

from app import create_app
from security import _private_key_path
from cryptography.hazmat.primitives import serialization


def _client():
    return TestClient(create_app())


def _issue(client, email="tester@example.com"):
    resp = client.post("/admin/keys", json={
        "email": email, "admin_token": "dev-admin-token"})
    assert resp.status_code == 200
    return resp.json()["key"]


def test_activate_first_machine_ok(tmp_path, monkeypatch):
    client = _client()
    resp = client.post("/api/v1/activate", json={
        "key": _issue(client, "first@x.com"), "machine_id": "MACHINE-A"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["tier"] == "pro"
    assert body["lease"]
    # o lease é um JWT ES256 válido (3 segmentos) com sub correto
    assert body["lease"].count(".") == 2
    # verifica que o lease foi assinado com a privada (não é alg:none)
    priv = serialization.load_pem_private_key(
        open(_private_key_path(), "rb").read(), password=None)
    claims = jwt.decode(body["lease"], priv.public_key(), algorithms=["ES256"])
    assert claims["sub"] == "machine:MACHINE-A"
    assert claims["tier"] == "pro"


def test_activate_same_key_other_machine_rejected(tmp_path, monkeypatch):
    client = _client()
    key = _issue(client, "one@x.com")
    r1 = client.post("/api/v1/activate", json={"key": key, "machine_id": "MACHINE-A"})
    assert r1.status_code == 200
    r2 = client.post("/api/v1/activate", json={"key": key, "machine_id": "MACHINE-B"})
    assert r2.status_code == 403
    assert "maquina" in r2.json()["error"].lower()


def test_activate_same_key_same_machine_reissue_ok(tmp_path, monkeypatch):
    client = _client()
    key = _issue(client, "re@x.com")
    r1 = client.post("/api/v1/activate", json={"key": key, "machine_id": "M"})
    assert r1.status_code == 200
    r2 = client.post("/api/v1/activate", json={"key": key, "machine_id": "M"})
    assert r2.status_code == 200  # mesma máquina → reemite lease (idempotente)


def test_activate_invalid_key_rejected(tmp_path, monkeypatch):
    client = _client()
    resp = client.post("/api/v1/activate", json={
        "key": "MAO-NOTVALID", "machine_id": "M"})
    assert resp.status_code == 403
```

- [ ] **Step 2: Correr o teste e ver que falha**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests/test_activate.py -v`
Expected: FAIL — 404.

- [ ] **Step 3: Implementar service.activate**

Adicionar a `license-server/service.py`:

```python
import secrets

from security import issue_lease, decode_jwt
from storage import (bind_machine, hash_key, key_valid, machine_for_key,
                     get_current_nonce_helper)


def activate(conn, key: str, machine_id: str) -> tuple[str, str, int]:
    """Liga uma chave a uma máquina e emite um lease ES256.

    Regra dura: 1 chave = 1 máquina. Se a chave já está ligada a OUTRA máquina,
    levanta ValueError.
    """
    key_hash = hash_key(key)
    if not key_valid(conn, key_hash):
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


def get_current_nonce_helper(conn) -> int:
    from storage import get_revocation_nonce
    return get_revocation_nonce(conn)
```

- [ ] **Step 4: Adicionar a rota /api/v1/activate em app.py**

Adicionar em `license-server/app.py`:

```python
from service import activate


class ActivateRequest(BaseModel):
    key: str
    machine_id: str


class ActivateResponse(BaseModel):
    tier: str
    lease: str
    session_id: str
    use_seq: int


@app.post("/api/v1/activate")
def api_activate(req: ActivateRequest, db=Depends(get_db)):
    try:
        lease, session_id, use_seq = activate(
            db, req.key.strip(), req.machine_id.strip())
    except ValueError as exc:
        return JSONResponse(status_code=403, content={"error": str(exc)})
    return ActivateResponse(tier="pro", lease=lease,
                            session_id=session_id, use_seq=use_seq)
```

- [ ] **Step 5: Correr os testes e ver que passam**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests/test_activate.py -v`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add license-server/
git commit -m "feat(license-server): activate - vinculo 1 chave = 1 maquina + lease ES256"
```

---

## Task 4: Trial server-side (30 min, fonte de verdade) + report persistente

**Files:**
- Modify: `license-server/service.py`, `license-server/app.py`
- Test: `license-server/tests/test_trial.py`

**Objetivo anti-burla (spec §4.1/§6):** o servidor é a fonte de verdade do trial. `used_seconds` só cresce (nunca diminui via `MAX`). `trial/report` **persiste** os segundos de uso reportados pelo cliente — já não é stub. Apagar o ficheiro local do cliente NÃO reinicia, porque a verdade está no servidor.

- [ ] **Step 1: Escrever o teste de trial (idempotente, não reinicia, report persiste)**

Create `license-server/tests/test_trial.py`:

```python
"""Tests for server-side 30-min trial. Idempotente + nunca diminui + report persiste."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app import create_app
from storage import connect, init_db


def _client():
    return TestClient(create_app())


def test_trial_start_ok():
    client = _client()
    resp = client.post("/api/v1/trial/start", json={"machine_id": "M1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["remaining_seconds"] == 30 * 60


def test_trial_start_does_not_reset():
    client = _client()
    client.post("/api/v1/trial/start", json={"machine_id": "M2"})
    conn = connect(); init_db(conn)
    conn.execute("UPDATE trial SET used_seconds=1800 WHERE machine_id='M2'")
    conn.commit(); conn.close()
    body = client.post("/api/v1/trial/start", json={"machine_id": "M2"}).json()
    assert body["remaining_seconds"] == 0


def test_trial_report_persists_usage():
    client = _client()
    client.post("/api/v1/trial/start", json={"machine_id": "M3"})
    r = client.post("/api/v1/trial/report",
                    json={"machine_id": "M3", "used_seconds": 120})
    assert r.status_code == 200
    status = client.get("/api/v1/trial/status?machine_id=M3").json()
    assert status["remaining_seconds"] == 30 * 60 - 120


def test_trial_report_never_decreases():
    client = _client()
    client.post("/api/v1/trial/start", json={"machine_id": "M4"})
    client.post("/api/v1/trial/report", json={"machine_id": "M4", "used_seconds": 300})
    # report menor não reduz
    client.post("/api/v1/trial/report", json={"machine_id": "M4", "used_seconds": 60})
    status = client.get("/api/v1/trial/status?machine_id=M4").json()
    assert status["remaining_seconds"] == 30 * 60 - 300


def test_trial_status():
    client = _client()
    client.post("/api/v1/trial/start", json={"machine_id": "M5"})
    status = client.get("/api/v1/trial/status?machine_id=M5").json()
    assert "remaining_seconds" in status
```

- [ ] **Step 2: Correr e ver que falha**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests/test_trial.py -v`
Expected: FAIL — 404.

- [ ] **Step 3: Implementar service.trial**

Adicionar a `license-server/service.py`:

```python
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
```

- [ ] **Step 4: Adicionar rotas de trial em app.py (functional, não stub)**

Adicionar em `license-server/app.py`:

```python
from service import trial_remaining, trial_report
from storage import TRIAL_MAX_SECONDS


class TrialRequest(BaseModel):
    machine_id: str
    used_seconds: int = 0


class TrialReportRequest(BaseModel):
    machine_id: str
    used_seconds: int


@app.post("/api/v1/trial/start")
def trial_start(req: TrialRequest, db=Depends(get_db)):
    from storage import get_trial, set_trial_used
    row = get_trial(db, req.machine_id)
    if row is None:
        set_trial_used(db, req.machine_id, 0)
    remaining = trial_remaining(db, req.machine_id)
    return {"machine_id": req.machine_id, "remaining_seconds": remaining,
            "trial_seconds": TRIAL_MAX_SECONDS}


@app.post("/api/v1/trial/report")
def api_trial_report(req: TrialReportRequest, db=Depends(get_db)):
    remaining = trial_report(db, req.machine_id, req.used_seconds)
    return {"machine_id": req.machine_id, "remaining_seconds": remaining}


@app.get("/api/v1/trial/status")
def trial_status(machine_id: str, db=Depends(get_db)):
    return {"machine_id": machine_id,
            "remaining_seconds": trial_remaining(db, machine_id)}
```

- [ ] **Step 5: Correr os testes e ver que passam**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests/test_trial.py -v`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add license-server/
git commit -m "feat(license-server): trial server-side fonte de verdade - report persiste, nunca reinicia"
```

---

## Task 5: Revalidação + revocation_nonce + anti-replay

**Files:**
- Modify: `license-server/service.py`, `license-server/app.py`
- Test: `license-server/tests/test_revalidate.py`

- [ ] **Step 1: Escrever o teste de revalidate**

Create `license-server/tests/test_revalidate.py`:

```python
"""Tests for revalidate: renew lease, revoke via nonce, anti-replay."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app import create_app


def _client():
    return TestClient(create_app())


def _activate(client, machine="M1"):
    resp = client.post("/admin/keys", json={
        "email": "r@x.com", "admin_token": "dev-admin-token"})
    key = resp.json()["key"]
    r = client.post("/api/v1/activate", json={"key": key, "machine_id": machine})
    return r


def test_revalidate_returns_new_lease():
    client = _client()
    act = _activate(client).json()
    resp = client.post("/api/v1/revalidate", json={
        "machine_id": "M1", "old_lease": act["lease"]})
    assert resp.status_code == 200
    assert resp.json()["tier"] == "pro"
    assert resp.json()["lease"]


def test_revalidate_rejects_stale_nonce_after_revoke():
    client = _client()
    act = _activate(client).json()
    r = client.post("/api/v1/revoke", json={
        "machine_id": "M1", "admin_token": "dev-admin-token"})
    assert r.status_code == 200
    resp = client.post("/api/v1/revalidate", json={
        "machine_id": "M1", "old_lease": act["lease"]})
    assert resp.status_code == 403


def test_revalidate_rejects_unknown_machine():
    client = _client()
    resp = client.post("/api/v1/revalidate", json={
        "machine_id": "NOBODY", "old_lease": "garbage"})
    assert resp.status_code == 403
```

- [ ] **Step 2: Correr e ver que falha**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests/test_revalidate.py -v`
Expected: FAIL — 404.

- [ ] **Step 3: Implementar service.revalidate + revoke**

Adicionar a `license-server/service.py`:

```python
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
```

- [ ] **Step 4: Adicionar rotas /api/v1/revalidate e /api/v1/revoke em app.py**

Adicionar em `license-server/app.py`:

```python
from service import revalidate, revoke_machine, authorized


class RevalidateRequest(BaseModel):
    machine_id: str
    old_lease: str


class RevokeRequest(BaseModel):
    machine_id: str
    admin_token: str


@app.post("/api/v1/revalidate")
def api_revalidate(req: RevalidateRequest, db=Depends(get_db)):
    try:
        lease = revalidate(db, req.machine_id.strip(), req.old_lease.strip())
    except ValueError as exc:
        return JSONResponse(status_code=403, content={"error": str(exc)})
    return {"tier": "pro", "lease": lease}


@app.post("/api/v1/revoke")
def api_revoke(req: RevokeRequest, db=Depends(get_db)):
    if not authorized(req.admin_token):
        return JSONResponse(status_code=403, content={"error": "forbidden"})
    revoke_machine(db, req.machine_id)
    return {"ok": True}
```

- [ ] **Step 5: Correr os testes e ver que passam**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests/test_revalidate.py -v`
Expected: PASS (3 tests).

- [ ] **Step 6: Correr TODOS os testes do servidor**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests -v`
Expected: PASS (1 + 2 + 4 + 5 + 3 = 15 tests).

- [ ] **Step 7: Commit**

```bash
git add license-server/
git commit -m "feat(license-server): revalidate + revoke + nonce + anti-replay use_seq"
```

---

# PARTE 2 — Cliente (core)

## Task 6: `core/fingerprint.py` — machine_id

**Files:**
- Create: `core/fingerprint.py`
- Test: `tests/test_fingerprint.py`

- [ ] **Step 1: Escrever o teste**

Create `tests/test_fingerprint.py` (sem alterações vs plano original — já correto):

```python
"""Tests for machine fingerprint -> stable machine_id."""
import core.fingerprint as fp


def test_machine_id_deterministic():
    a = fp.machine_id()
    b = fp.machine_id()
    assert a == b
    assert len(a) >= 32


def test_machine_id_hex():
    mid = fp.machine_id()
    assert all(c in "0123456789abcdef" for c in mid)


def test_fingerprint_components_nonempty():
    comps = fp.collect_components()
    assert comps
```

- [ ] **Step 2: Correr e ver que falha**

Run: `.venv\Scripts\python.exe -m pytest tests/test_fingerprint.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.fingerprint'`.

- [ ] **Step 3: Implementar `core/fingerprint.py`**

```python
"""Hardware fingerprint -> deterministic machine_id (SHA-256)."""
import hashlib
import subprocess


def _read_machine_guid() -> str:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Cryptography") as k:
            val, _ = winreg.QueryValueEx(k, "MachineGuid")
            return str(val)
    except Exception:
        return ""


def _wmic(namespace_class: str) -> str:
    try:
        out = subprocess.run(
            ["wmic", namespace_class, "get", "SerialNumber"],
            capture_output=True, text=True, timeout=8).stdout
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        return lines[-1] if len(lines) > 1 else ""
    except Exception:
        return ""


def collect_components() -> dict:
    return {
        "machine_guid": _read_machine_guid(),
        "disk_serial": _wmic("diskdrive"),
        "board_uuid": _wmic("baseboard"),
    }


def machine_id() -> str:
    comps = collect_components()
    joined = "|".join(f"{k}={comps[k]}" for k in sorted(comps))
    return hashlib.sha256(joined.encode()).hexdigest()
```

- [ ] **Step 4: Correr o teste e ver que passa**

Run: `.venv\Scripts\python.exe -m pytest tests/test_fingerprint.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add core/fingerprint.py tests/test_fingerprint.py
git commit -m "feat(fingerprint): machine_id por hardware (MachineGuid + serial + board uuid)"
```

---

## Task 7: `core/license_client.py` — cliente HTTP urllib + failover

**Files:**
- Create: `core/license_client.py`
- Test: `tests/test_license_client.py`

O cliente usa `urllib.request` (padrão do projeto). Métodos: `activate`, `revalidate`, `trial_start`, `trial_report`, `trial_status`.

- [ ] **Step 1: Escrever o teste**

Create `tests/test_license_client.py` (teste original + acrescentar trial_report):

```python
"""Tests for LicenseClient HTTP transport (urllib) + failover."""
import json

import core.license_client as lc


class _FakeHandler:
    def __init__(self, responses):
        self._responses = responses
        self.calls = []

    def __call__(self, req, timeout=5):
        self.calls.append(req.full_url)
        url = req.full_url
        for base, payload in self._responses.items():
            if url.startswith(base):
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
    try:
        client.activate("BAD", "m")
        assert False, "deveria lançar LicenseError"
    except lc.LicenseError as exc:
        assert "chave" in str(exc)


def test_trial_report(monkeypatch):
    handler = _FakeHandler({"/api/v1/trial/report": (200, {"remaining_seconds": 30})})
    monkeypatch.setattr(lc.urllib.request, "urlopen", handler)
    client = lc.LicenseClient(["http://srv"])
    result = client.trial_report("mid", 120)
    assert result["remaining_seconds"] == 30
```

- [ ] **Step 2: Correr e ver que falha**

Run: `.venv\Scripts\python.exe -m pytest tests/test_license_client.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implementar `core/license_client.py`**

```python
"""Cliente HTTPS para o License Server (urllib + endpoint failover)."""
import json
import urllib.error
import urllib.request


class LicenseError(Exception):
    """Erro de licença (HTTP 4xx/5xx com corpo)."""


class LicenseClient:
    def __init__(self, endpoints, timeout=8):
        self._endpoints = [e.rstrip("/") for e in endpoints]
        self._timeout = timeout

    def _request(self, method, path, payload=None):
        last_err = None
        for base in self._endpoints:
            url = base + path
            data = None
            headers = {}
            if payload is not None:
                data = json.dumps(payload).encode()
                headers["Content-Type"] = "application/json"
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    raw = resp.read()
                    return json.loads(raw.decode("utf-8")) if raw else {}
            except urllib.error.HTTPError as exc:
                try:
                    body = json.loads(exc.read().decode("utf-8"))
                except Exception:
                    body = {"error": f"http {exc.code}"}
                raise LicenseError(body.get("error", f"http {exc.code}")) from exc
            except Exception as exc:
                last_err = exc
                continue
        raise LicenseError(f"sem_servidor_reachavel: {last_err}")

    def activate(self, key, machine_id):
        return self._request("POST", "/api/v1/activate",
                             {"key": key, "machine_id": machine_id})

    def revalidate(self, machine_id, old_lease):
        return self._request("POST", "/api/v1/revalidate",
                             {"machine_id": machine_id, "old_lease": old_lease})

    def trial_start(self, machine_id):
        return self._request("POST", "/api/v1/trial/start",
                             {"machine_id": machine_id})

    def trial_report(self, machine_id, used_seconds):
        return self._request("POST", "/api/v1/trial/report",
                             {"machine_id": machine_id, "used_seconds": used_seconds})

    def trial_status(self, machine_id):
        return self._request("GET", f"/api/v1/trial/status?machine_id={machine_id}")
```

Nota: o `LicenseClient` usa GET para `trial_status` (sem payload, sem `Content-Type`).

- [ ] **Step 4: Correr o teste e ver que passa**

Run: `.venv\Scripts\python.exe -m pytest tests/test_license_client.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add core/license_client.py tests/test_license_client.py
git commit -m "feat(license_client): transporte HTTP urllib com failover e trial report"
```

---

## Task 8: Reescrever `core/licensing.py` — trial 30min + lease ES256 verificado + bloqueio (API preservada)

**Files:**
- Modify: `core/licensing.py` (reescrita mantendo API pública compatível)
- Create: `core/licensing_public_key.pem` (chave pública ES256)
- Test: `tests/test_licensing.py` (ajustar), `tests/test_trial_30min.py` (novo), `tests/test_lease.py` (novo)

**Decisões-chave (fixas no review):**
1. **API preservada** — mantém `Tier`, `PRO_LOCKED`, `entitlements`, `is_pro_locked`, `LicenseManager`, `LicenseAgency`, `set_active_license`/`active_license`/`active_tier`, e os métodos `save/load/activate/deactivate/is_pro/can/checkout_urls/open_checkout`. `issue_pro_key`/`validate_key` mantêm-se na API pública mas **deixam de ser o caminho de produção** (o PATH de produção é a ativação online + lease ES256). `LicenseManager.__init__` ganha kwargs novos (`endpoints`, `trial_seconds`, `public_key_pem`) **sem quebrar** a assinatura atual `(secret, store_path, agency)` — os kwargs novos são adicionados com defaults.
2. **Trial server-authoritative** — quando há rede, o cliente **reconcilia** com o servidor (`trial/status` é autoritativo) e **reporta** uso (`trial/report`). Apagar `license.json` não reinicia: o servidor lembra o `used_seconds` da máquina.
3. **Lease verificado localmente (ES256)** — `_validate_local_lease` verifica a assinatura ES256 com a chave pública embutida (`cryptography`), `sub == machine:<id>`, `exp`, `revocation_nonce` (>= o último visto localmente) e `use_seq` (estritamente maior que o último visto localmente). **Recusa `alg:none` e assinatura inválida.**

- [ ] **Step 1: Escrever teste de trial de 30 min (cliente)**

Create `tests/test_trial_30min.py`:

```python
"""Trial de 30 min no cliente: conta uso real, is_blocked quando esgota,
e NÃO concede trial novo offline sem registo local (anti-reset)."""
import core.licensing as lic
from core.license_client import LicenseError


def test_default_state_is_free():
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=30 * 60)
    assert lm.tier is lic.Tier.FREE
    assert not lm.is_blocked()


def test_trial_uses_30_minutes(tmp_path):
    store = tmp_path / "lic.json"
    lm = lic.LicenseManager(store_path=str(store), trial_seconds=30 * 60)
    lm.report_usage(30 * 60)
    assert lm.trial_used_seconds() == 30 * 60
    assert lm.trial_remaining_seconds() == 0
    assert lm.is_blocked()
    assert lm.block_reason() == "trial_esgotado"


def test_trial_offline_without_local_record_blocks(monkeypatch, tmp_path):
    """Apagou-se license.json e está offline -> NÃO recebe 30 min novos."""
    store = tmp_path / "lic.json"  # não existe -> ficheiro novo (apagado)
    lm = lic.LicenseManager(store_path=str(store), trial_seconds=30 * 60)
    # força falha de rede no cliente
    def _boom(*a, **k):
        raise LicenseError("sem_servidor_reachavel")
    monkeypatch.setattr(lm._client, "trial_status", _boom)
    lm.reconcile_trial()
    assert lm.is_blocked()
    assert lm.block_reason() == "trial_requer_ligacao"
```

- [ ] **Step 2: Escrever teste de lease ES256 verificado (rejeita forgery)**

Create `tests/test_lease.py`:

```python
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
```

(Nota: estes testes exigem que `_validate_local_lease` verifique a assinatura ES256 com a chave pública. Como não há como gerar um JWT ES256 válido no teste sem a privada, testamos o caso NEGATIVO: qualquer lease não assinado/corrompido/de outra máquina é rejeitado. A validação POSITIVA do fluxo de ativação completa cobre-se no teste de integração Task 12 / ou com um JWT ES256 gerado pela chave de dev.)

- [ ] **Step 3: Correr e ver que falha**

Run: `.venv\Scripts\python.exe -m pytest tests/test_trial_30min.py tests/test_lease.py -v`
Expected: FAIL — falta de métodos (`report_usage`, `trial_used_seconds`, `is_pro_offline_valid`, etc.).

- [ ] **Step 4: Gerar a chave pública ES256 para o cliente + declarar dependência**

**Dependência do cliente:** `core/licensing.py` passa a importar `cryptography`. Esta é uma dependência **de runtime do cliente** e deve ser declarada em `pyproject.toml`. Adicionar a `[project.dependencies]` (que agora está vazio):

```toml
dependencies = [
    "cryptography>=42",
]
```

(E instalar no venv: `.venv\Scripts\python.exe -m pip install cryptography`.) Isto também é necessário para o PyInstaller empacotar o `cryptography` no executável.

Gerar o keypair e gravar a pública em `core/licensing_public_key.pem`:

```bash
.venv\Scripts\python.exe -c "from cryptography.hazmat.primitives import serialization; from cryptography.hazmat.primitives.asymmetric import ec; k=ec.generate_private_key(ec.SECP256R1()); open('core/licensing_public_key.pem','wb').write(k.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)); print('public key written')"
```

(Nota: em dev/teste cada env gera a sua; em produção a pública embutida em `core/licensing_public_key.pem` deve **corresponder** à privada do servidor real.)

- [ ] **Step 5: Implementar a reescrita de `core/licensing.py`**

Substituir o conteúdo (mantendo todos os símbolos públicos; a estrutura resumida abaixo é a implementação a seguir):

```python
"""Licenciamento AirMouse — trial 30min server-auth + ativacao online + lease ES256 + gate."""
import base64
import json
import os
import time
import webbrowser
from enum import Enum

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from core.fingerprint import machine_id
from core.license_client import LicenseClient, LicenseError

TRIAL_DEFAULT_SECONDS = 30 * 60
LEASE_DEFAULT_DAYS = 7

_PUBLIC_KEY_PEM = os.path.join(os.path.dirname(__file__), "licensing_public_key.pem")


class Tier(Enum):
    FREE = "free"
    PRO = "pro"


PRO_LOCKED = ("snap", "voice", "two_hands", "tts", "ai", "autotune", "low_light")


def entitlements(tier: Tier) -> dict:
    base = {"move": True, "click": True}
    pro_on = tier == Tier.PRO
    for f in PRO_LOCKED:
        base[f] = pro_on
    return base


def is_pro_locked(tier: Tier, feature: str) -> bool:
    return feature in PRO_LOCKED and tier != Tier.PRO


def _load_public_key():
    with open(_PUBLIC_KEY_PEM, "rb") as fh:
        return serialization.load_pem_public_key(fh.read())


class LicenseManager:
    def __init__(self, secret: str = "", store_path=None,
                 agency: "LicenseAgency | None" = None,
                 endpoints=None, trial_seconds=TRIAL_DEFAULT_SECONDS,
                 public_key=None):
        self._store_path = store_path or _default_store_path()
        self._agency = agency
        self._endpoints = endpoints or _default_endpoints()
        self._client = LicenseClient(self._endpoints)
        self._trial_seconds = trial_seconds
        self._public_key = public_key or _load_public_key()
        self._machine = machine_id()
        self.tier = Tier.FREE
        self.key = ""
        self.email = ""
        self._trial_used = 0
        self._last_nonce = 0
        self._last_use_seq = 0
        self._blocked = False
        self._block_reason = ""
        self.load()

    # ── Trial (server-authoritative + best-effort offline) ──
    def trial_used_seconds(self) -> int:
        return self._trial_used

    def trial_remaining_seconds(self) -> int:
        return max(0, self._trial_seconds - self._trial_used)

    def report_usage(self, seconds: int) -> None:
        self._trial_used = min(self._trial_seconds, self._trial_used + max(0, seconds))
        if self._trial_used >= self._trial_seconds:
            self._blocked = True
            self._block_reason = "trial_esgotado"
        self.save()

    def reconcile_trial(self) -> None:
        """Quando há rede, o servidor é a fonte de verdade: adota o MAIOR uso
        entre local e servidor, e reporta o uso local para o servidor persistir.

        Regra anti-reset: se não há registo local do trial (ex.: ficheiro apagado)
        e o servidor não está alcançável, este aparece como "primeira vez" sem prova
        — bloqueia com pedido de ligação em vez de conceder 30 min novos.
        """
        if self.is_pro:
            return
        had_local = self._trial_used > 0 or _store_exists(self._store_path)
        try:
            status = self._client.trial_status(self._machine)
            server_used = max(0, self._trial_seconds - status["remaining_seconds"])
        except LicenseError:
            if not had_local:
                # sem registo local E sem servidor -> não pode provar 1ª vez
                self._blocked = True
                self._block_reason = "trial_requer_ligacao"
            return
        try:
            self._client.trial_report(self._machine, self._trial_used)
        except LicenseError:
            pass
        self._trial_used = max(self._trial_used, server_used)
        if self._trial_used >= self._trial_seconds:
            self._blocked = True
            self._block_reason = "trial_esgotado"
        self.save()

    def tier_pending(self) -> str:
        if self.is_pro:
            return "pro"
        if self.is_blocked():
            return "trial_esgotado"
        return "trial"

    # ── Persistência ──
    def save(self) -> None:
        if self._store_path == ":memory:":
            return
        try:
            os.makedirs(os.path.dirname(self._store_path), exist_ok=True)
            with open(self._store_path, "w", encoding="utf-8") as fh:
                json.dump({
                    "lease": self.lease,
                    "email": self.email,
                    "machine_id": self._machine,
                    "trial_used": self._trial_used,
                    "last_nonce": self._last_nonce,
                    "last_use_seq": self._last_use_seq,
                }, fh, indent=2)
        except OSError:
            pass

    def load(self) -> None:
        if self._store_path == ":memory:":
            return
        data = self._read_store()
        if data is None:
            return
        if data.get("machine_id") != self._machine:
            return  # ficheiro de outra máquina -> não honrar
        self._trial_used = int(data.get("trial_used", 0))
        self._last_nonce = int(data.get("last_nonce", 0))
        self._last_use_seq = int(data.get("last_use_seq", 0))
        if data.get("lease") and self._validate_local_lease(data["lease"]):
            self.lease = data["lease"]
            self.email = data.get("email", "")
            self.tier = Tier.PRO

    def _read_store(self):
        try:
            with open(self._store_path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None

    # ── Validação local do lease (ES256, anti-forgery) ──
    def _verify_es256_with(self, pub_key, signing_input: bytes, raw_sig: bytes) -> bool:
        """Verifica a assinatura ES256 (raw r||s -> DER) com a chave pública."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
        try:
            r = int.from_bytes(raw_sig[:32], "big")
            s = int.from_bytes(raw_sig[32:], "big")
            der_sig = encode_dss_signature(r, s)
            pub_key.verify(der_sig, signing_input, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False

    def _validate_local_lease(self, lease: str) -> bool:
        try:
            header_b64, payload_b64, sig_b64 = lease.split(".")
        except ValueError:
            return False
        try:
            header = json.loads(_b64d(header_b64))
            payload = json.loads(_b64d(payload_b64))
            raw_sig = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))
        except Exception:
            return False
        if header.get("alg") != "ES256":
            return False  # rejeita alg:none e outras
        if not self._verify_es256_with(self._public_key,
                                       f"{header_b64}.{payload_b64}".encode(), raw_sig):
            return False
        if payload.get("sub") != f"machine:{self._machine}":
            return False
        if int(time.time()) > int(payload.get("exp", 0)):
            return False
        if int(payload.get("revocation_nonce", -1)) < self._last_nonce:
            return False
        if int(payload.get("use_seq", -1)) <= self._last_use_seq:
            return False
        self._last_nonce = int(payload.get("revocation_nonce", 0))
        self._last_use_seq = int(payload.get("use_seq", 0))
        return True

    def is_pro_offline_valid(self) -> bool:
        return bool(self.lease and self._validate_local_lease(self.lease))

    # ── Ativação online ──
    def activate(self, key: str) -> bool:
        try:
            result = self._client.activate(key.strip(), self._machine)
        except LicenseError as exc:
            self._blocked = True
            self._block_reason = f"ativacao_falhou: {exc}"
            return False
        self.lease = result["lease"]
        self.key = key.strip()
        self.tier = Tier.PRO
        self.save()
        return True

    def revalidate(self) -> bool:
        if not self.lease:
            return False
        try:
            result = self._client.revalidate(self._machine, self.lease)
        except LicenseError:
            return False
        self.lease = result["lease"]
        self.save()
        return True

    def maybe_revalidate(self) -> None:
        if not self.is_pro:
            return
        if self._needs_revalidation():
            self.revalidate()

    def _needs_revalidation(self) -> bool:
        try:
            payload = self._decode_payload(self.lease)
            issued = int(payload.get("iat", 0))
        except Exception:
            return True
        return (time.time() - issued) >= 7 * 24 * 3600 - 3600  # ~1h antes de expirar 7d

    def _decode_payload(self, lease: str) -> dict:
        payload_b64 = lease.split(".")[1]
        return json.loads(_b64d(payload_b64))

    # ── Bloqueio / gate ──
    def is_blocked(self) -> bool:
        if self.tier == Tier.PRO:
            if not self._validate_local_lease(self.lease):
                self._blocked = True
                self._block_reason = "lease_invalido_ou_expirado"
                return True
            return False
        if self._trial_used >= self._trial_seconds:
            return True
        return False

    def block_reason(self) -> str:
        if self._block_reason:
            return self._block_reason
        return "trial_esgotado" if self.is_blocked() else ""

    # ── Compat com UI / CLI / tools (API preservada) ──
    @property
    def is_pro(self) -> bool:
        return self.tier == Tier.PRO

    def can(self, feature: str) -> bool:
        return bool(entitlements(self.tier).get(feature, True))

    def deactivate(self) -> None:
        self.tier = Tier.FREE
        self.key = ""
        self.email = ""
        self.lease = ""
        self._blocked = False
        self._block_reason = ""
        if os.path.exists(self._store_path):
            try:
                os.remove(self._store_path)
            except OSError:
                pass

    def checkout_urls(self, vendor_id: int) -> dict[str, str]:
        url = PADDLE_PRODUCT_URLS.get("lifetime")
        payment = PADDLE_PRODUCT_URLS.get("subscription")
        family = PADDLE_PRODUCT_URLS.get("family")
        access = PADDLE_PRODUCT_URLS.get("access")
        return {
            "lifetime": url or f"https://checkout.paddle.com/{vendor_id}?product=maouse-pro-lifetime",
            "subscription": payment or f"https://checkout.paddle.com/{vendor_id}?product=maouse-pro-subscription",
            "family": family or f"https://checkout.paddle.com/{vendor_id}?product=maouse-family",
            "access": access or f"https://checkout.paddle.com/{vendor_id}?product=maouse-pro-access",
        }

    def open_checkout(self, product: str, vendor_id: int) -> bool:
        urls = self.checkout_urls(vendor_id)
        url = urls.get(product)
        if not url:
            return False
        try:
            return bool(webbrowser.open(url, new=2))
        except webbrowser.Error:
            return False

    # issue_pro_key / validate_key: mantidos NA API pública mas já NÃO usados
    # no caminho de produção (o servidor emite; o cliente só ativa online).
    def issue_pro_key(self, email: str) -> str:
        raise NotImplementedError(
            "Emissão de chaves é feita pelo servidor (license-server). "
            "Use tools/issue_pro_key.py remoto.")
```

> **Nota de implementação (importante — esquema ES256 raw vs DER):** PyJWT produz assinaturas ES256 JWS no formato **raw `r‖s`** (RFC 7518: 64 bytes para P-256, 32 bytes de `r` + 32 bytes de `s`). A API `cryptography` `verify` espera a assinatura em **DER** (ASN.1). Por isso o cliente tem de **converter raw→DER** antes de verificar:
> ```python
> import base64
> from cryptography.exceptions import InvalidSignature
> from cryptography.hazmat.primitives import hashes
> from cryptography.hazmat.primitives.asymmetric import ec
> from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
>
> def _verify_es256_with(pub_key, signing_input: bytes, raw_sig: bytes) -> bool:
>     # raw_sig tem 64 bytes (r||s, 32+32) para P-256
>     r = int.from_bytes(raw_sig[:32], "big")
>     s = int.from_bytes(raw_sig[32:], "big")
>     der_sig = encode_dss_signature(r, s)
>     try:
>         pub_key.verify(der_sig, signing_input, ec.ECDSA(hashes.SHA256()))
>         return True
>     except InvalidSignature:
>         return False
> ```
> E em `_validate_local_lease`, após `lease.split(".")`:
> ```python
> raw_sig = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))
> if not _verify_es256_with(self._public_key,
>                           f"{header_b64}.{payload_b64}".encode(), raw_sig):
>     return False
> ```
> Usa este snippet VERDADEIRO — o esqueleto `_verify_es256` acima (com `ec.ECDSA(r).to_der() if False else None`) NÃO deve ser copiado literalmente; é apenas um marcador de design.

E os helpers no topo do ficheiro:

```python
def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _default_store_path() -> str:
    base = os.getenv("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "AirMouse", "license.json")


def _store_exists(store_path: str) -> bool:
    return store_path != ":memory:" and os.path.exists(store_path)


def _default_endpoints():
    raw = os.getenv("AIRMOUSE_LICENSE_URLS", "")
    return [u.strip() for u in raw.split(",") if u.strip()] or [
        "https://licenses.maouse.example.com"
    ]


_ACTIVE: "LicenseManager | None" = None


def set_active_license(manager: "LicenseManager") -> None:
    global _ACTIVE
    _ACTIVE = manager


def active_license() -> "LicenseManager":
    return _ACTIVE or LicenseManager()


def active_tier() -> Tier:
    return active_license().tier
```

Manter também `class LicenseAgency` (interface `online_validate`, default `True`) e o dict `PADDLE_PRODUCT_URLS` (importados por compat). `__all__` = `["Tier","PRO_LOCKED","entitlements","is_pro_locked","LicenseManager","LicenseAgency","set_active_license","active_license","active_tier"]`.

- [ ] **Step 6: Ajustar os testes existentes em `tests/test_licensing.py`**

Os testes antigos de chave offline HMAC (`test_issue_and_validate_pro_key`, `test_validate_rejects_*`, `test_activate_pro_sets_tier`, `test_activate_invalid_keeps_free`, `test_state_roundtrip`, `test_checkout_*`) mudam: a validação offline de chave deixa de ser o caminho. Reescrever `tests/test_licensing.py`:

```python
"""Tests for core/licensing.py — tier model, trial gate, lease persistence, compat API."""
import json

import core.licensing as lic


def test_default_tier_is_free():
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=60)
    assert lm.tier is lic.Tier.FREE
    assert not lm.is_pro


def test_free_entitlements():
    ent = lic.entitlements(lic.Tier.FREE)
    assert ent["move"] is True
    assert ent["click"] is True
    for f in ("snap", "voice", "two_hands", "tts", "ai", "autotune", "low_light"):
        assert ent[f] is False


def test_pro_entitlements_all_on():
    ent = lic.entitlements(lic.Tier.PRO)
    for f in ("move", "click", "snap", "voice", "two_hands", "tts",
              "ai", "autotune", "low_light"):
        assert ent[f] is True


def test_is_pro_locked():
    assert lic.is_pro_locked(lic.Tier.FREE, "snap")
    assert not lic.is_pro_locked(lic.Tier.FREE, "move")
    assert not lic.is_pro_locked(lic.Tier.PRO, "snap")


def test_trial_blocks_when_exhausted(tmp_path):
    store = tmp_path / "lic.json"
    lm = lic.LicenseManager(store_path=str(store), trial_seconds=30 * 60)
    lm.report_usage(30 * 60)
    assert lm.is_blocked()
    assert lm.trial_remaining_seconds() == 0
    assert lm.block_reason() == "trial_esgotado"


def test_store_from_other_machine_not_honored(tmp_path):
    p = tmp_path / "lic.json"
    p.write_text(json.dumps({"machine_id": "OTHER", "trial_used": 0,
                             "lease": "", "last_nonce": 0, "last_use_seq": 0}),
                 encoding="utf-8")
    lm = lic.LicenseManager(store_path=str(p), trial_seconds=60)
    lm.load()
    assert lm.tier is lic.Tier.FREE


def test_checkout_urls_built_from_config(monkeypatch):
    lm = lic.LicenseManager(store_path=":memory:")
    urls = lm.checkout_urls(vendor_id=12345)
    assert "checkout.paddle.com" in urls["lifetime"]


def test_open_checkout_calls_browser(monkeypatch):
    lm = lic.LicenseManager(store_path=":memory:")
    monkeypatch.setattr(lic.webbrowser, "open", lambda url, new=0: True)
    assert lm.open_checkout("lifetime", 12345) is True


def test_active_license_defaults_to_free():
    assert lic.active_tier() is lic.Tier.FREE
    lic.set_active_license(lic.LicenseManager(store_path=":memory:"))
    assert lic.active_tier() is lic.Tier.FREE
```

- [ ] **Step 7: Correr toda a suite do cliente**

Run: `.venv\Scripts\python.exe -m pytest tests -v`
Expected: PASS (as novas + as existentes não relacionadas).

- [ ] **Step 8: Commit**

```bash
git add core/licensing.py core/licensing_public_key.pem tests/test_licensing.py tests/test_trial_30min.py tests/test_lease.py
git commit -m "feat(licensing): trial 30min server-auth + lease ES256 verificado + bloqueio + API preservada"
```

---

## Task 8b: `tools/issue_pro_key.py` → emissão remota via servidor

**Files:**
- Modify: `tools/issue_pro_key.py`
- Test: (opcional) manual / smoke

**Contexto:** antes emitia offline via `LicenseManager.issue_pro_key` + `AIRMOUSE_LICENSE_SECRET`. Agora a emissão é no servidor (`/admin/keys`). A ferramenta passa a ser um cliente admin que chama o servidor com `admin_token`.

- [ ] **Step 1: Reescrever `tools/issue_pro_key.py`**

```python
"""Emite uma chave Pro no servidor de licenças (admin).

Uso:
  python tools/issue_pro_key.py comprador@exemplo.pt
  (com AIRMOUSE_LS_URL e AIRMOUSE_LS_ADMIN_TOKEN no ambiente)
"""
import json
import os
import sys
import urllib.error
import urllib.request


def main():
    if len(sys.argv) < 2:
        print("Uso: python tools/issue_pro_key.py <email-do-comprador>")
        return 1
    email = sys.argv[1]
    url = (os.getenv("AIRMOUSE_LS_URL", "") or "https://licenses.maouse.example.com").rstrip("/")
    token = os.getenv("AIRMOUSE_LS_ADMIN_TOKEN", "")
    if not token:
        print("ERRO: defina AIRMOUSE_LS_ADMIN_TOKEN.")
        return 1
    req = urllib.request.Request(
        url + "/admin/keys",
        data=json.dumps({"email": email, "admin_token": token}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            print(f"Chave gerada para {email}:\n{body['key']}")
    except urllib.error.HTTPError as exc:
        print(f"ERRO {exc.code}: {exc.read().decode('utf-8', 'replace')}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Smoke test manual**

Run: `.venv\Scripts\python.exe tools/issue_pro_key.py` (sem args) → mostra uso.
Correr contra um servidor de teste exige o `license-server` a correr; o core do teste é que deixa de usar a emissão offline.

- [ ] **Step 3: Commit**

```bash
git add tools/issue_pro_key.py
git commit -m "feat(tools): issue_pro_key emite remotamente via servidor /admin/keys"
```

---

# PARTE 3 — Runtime Gate (bloqueio total)

## Task 9: Gate de bloqueio no `process_frame`

**Files:**
- Modify: `core/engine.py` (process_frame, linha 183)
- Test: `tests/test_license_gate.py`

**Abordagem robusta (fixa no review):** o gate lê `state["license_blocked"]` (set no arranque pelo `main.py`) OU `active_license().is_blocked()`. Teste usa a flag de estado — NÃO usa `_forceblock` (não existe) nem helpers sem define.

- [ ] **Step 1: Escrever o teste do gate (flag de estado)**

Create `tests/test_license_gate.py`:

```python
"""Tests for the runtime block gate inside process_frame (via state flag)."""
import types

import core.licensing as lic
from core import engine


class _NoopMouse:
    def __init__(self):
        self.moved = False
        self.clicked = False

    def move(self, *a, **k):
        self.moved = True

    def click(self, *a, **k):
        self.clicked = True


class _NoopCam:
    def read(self):
        return None, None  # frame=None -> engine retorna cedo (sem movimento)


def _ctx():
    return types.SimpleNamespace(
        toast=lambda *a, **k: None, warmup_left=0, last_seq=-1,
        active_side=None, fps=0, ui=None, light=None, gray_check=0,
    )


def test_process_frame_blocks_when_license_blocked(monkeypatch):
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=60)
    lm.report_usage(60)  # esgota o trial
    monkeypatch.setattr(engine, "active_license", lambda: lm)

    cfg = types.SimpleNamespace(mirror=True, license_tier="free")
    state = {"license_blocked": True, "paused": False}
    mouse = _NoopMouse()
    cam = _NoopCam()

    engine.process_frame(cfg, cam, None, mouse, None, None, None, None, state, _ctx())
    assert mouse.moved is False


def test_process_frame_moves_when_not_blocked(monkeypatch):
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=60)
    monkeypatch.setattr(engine, "active_license", lambda: lm)

    cfg = types.SimpleNamespace(mirror=True, license_tier="free")
    state = {"license_blocked": False, "paused": False}
    mouse = _NoopMouse()
    cam = _NoopCam()

    engine.process_frame(cfg, cam, None, mouse, None, None, None, None, state, _ctx())
    # sem frame (cam.read() -> None) -> sem movimento; o que conta é não falhar
    assert isinstance(mouse, _NoopMouse)
```

(Nota do executor: `process_frame` começa com `frame, seq = cam.read()` e, se `frame is None`, retorna cedo **antes** do gate. Para o teste provar que o gate bloqueia, o `_NoopCam.read()` deve devolver um frame "espectável" ou o gate deve ser verificado de forma que `mouse.move` nunca seja chamado com `state["license_blocked"]=True`. **Ajusta o helper `_NoopCam.read()` para devolver um frame sintético não-None** e verifica que, com `license_blocked=True`, `mouse.move` NÃO é chamado, e com `False` é chamado. Consulta os testes de engine existentes em `tests/` para a forma real de construir um frame falso.)

- [ ] **Step 2: Correr e ver que falha (inicialmente sem gate, o mouse move-se)**

Run: `.venv\Scripts\python.exe -m pytest tests/test_license_gate.py -v`
Expected: FAIL — o mouse move-se apesar de `license_blocked=True` (falta o gate).

- [ ] **Step 3: Implementar o gate**

Modificar `core/engine.py`. No topo de `process_frame`, imediatamente após ler o frame e o `if frame is None`, adicionar:

```python
from core.licensing import active_license  # junto aos imports no topo do ficheiro

# dentro de process_frame, depois de resolver 'frame':
if state.get("license_blocked") or active_license().is_blocked():
    if not state.get("_license_warned"):
        E.toast("A tua experiencia Free terminou - ativa o PRO")
        state["_license_warned"] = True
    return {"frame": frame, "done": False, "to_render": False}
```

- [ ] **Step 4: Correr o teste e ver que passa**

Run: `.venv\Scripts\python.exe -m pytest tests/test_license_gate.py -v`
Expected: PASS.

- [ ] **Step 5: Correr toda a suite para garantir que não quebrou nada**

Run: `.venv\Scripts\python.exe -m pytest tests -v`
Expected: PASS (sem regressões nos testes de engine existentes).

- [ ] **Step 6: Commit**

```bash
git add core/engine.py tests/test_license_gate.py
git commit -m "feat(engine): gate de bloqueio total no process_frame (trial/lease expirados)"
```

---

## Task 10: Remover `--dev-pro` / `AIRMOUSE_DEV_PRO` e ligar trial+revalidação no arranque

**Files:**
- Modify: `main.py`
- Test: `tests/test_main_flags.py` (novo, com argv controlado)

- [ ] **Step 1: Escrever o teste de ausência do bypass (argv controlado)**

Create `tests/test_main_flags.py`:

```python
"""--dev-pro removido. O teste usa um argv controlado (não o sys.argv do pytest)."""
import sys

import main


def test_no_dev_pro_in_parse_args(monkeypatch):
    # controla argv para o argparse não ler os args reais do pytest
    monkeypatch.setattr(sys, "argv", ["airmouse", "--no-gui"])
    parser = main.parse_args()
    opts = set()
    for action in parser._actions:
        opts.update(action.option_strings)
    assert "--dev-pro" not in opts
```

- [ ] **Step 2: Correr e ver que falha**

Run: `.venv\Scripts\python.exe -m pytest tests/test_main_flags.py -v`
Expected: FAIL — `--dev-pro` ainda existe.

- [ ] **Step 3: Remover `--dev-pro` do `parse_args` em `main.py`**

Remover o bloco (linhas 90-95):

```python
    parser.add_argument(
        "--dev-pro",
        action="store_true",
        help="DEV: desbloqueia todas as funcionalidades Pro SEM chave "
             "(apenas em desenvolvimento; nunca usar no executavel).",
    )
```

E remover o bloco do `main()` (linhas 198-205):

```python
    dev_pro = args.dev_pro or os.getenv("AIRMOUSE_DEV_PRO") == "1"
    if dev_pro:
        lic_.tier = Tier.PRO
        cfg.license_tier = Tier.PRO.value
        log.warning("MODO DEV-PRO ATIVO: funcionalidades Pro desbloqueadas sem chave.")
```

**Importante (lint):** `Tier` (importado em `main.py:30`) era usado apenas no bloco dev-pro removido. Remover `Tier` do `from core.licensing import (...)` em `main.py:28-34`, senão o `ruff F401` na Task 12 falha. Manter `LicenseManager`, `entitlements`, `is_pro_locked`, `set_active_license` (usados em 239-245).

**Help text desatualizado:** o help do `--activate-key` (linha 83) ainda diz "offline"; a ativação agora é online. Atualizar a ajuda para refletir ativação online.

- [ ] **Step 4: Ligar trial+lease no arranque**

Onde já está `lic_ = LicenseManager()` (linha 194), substituir por:

```python
    lic_ = LicenseManager()        # o construtor já chama load() internamente
    lic_.reconcile_trial()         # quando há rede, alinha com o servidor (não reinicia)
    lic_.maybe_revalidate()        # revalidação periódica best-effort (pro)
    cfg.license_tier = lic_.tier.value
```

(Remover a chamada redundante `lic_.load()` que existia na linha 195 — `load()` é idempotente e já é chamado no `__init__`; manter as duas é só desperdício.)

E no dict `state` (linha 325), adicionar o gate de bloqueio:

```python
    state = {
        "paused": False,
        ...
        "license_blocked": lic_.is_blocked(),
        "_license_warned": False,
    }
```

E um watchdog de uso simples, no loop principal, para contar tempo real de Free. No `main.py`, após criar o `state` e o `set_active_license`, adicionar:

```python
    class _UsageWatchdog:
        """Reporta o tempo de uso efetivo ao trial enquanto está Free."""
        def __init__(self, lic):
            self._lic = lic
            self._t0 = time.time()

        def tick(self):
            if self._lic.is_pro or self._lic.is_blocked():
                return
            now = time.time()
            delta = int(now - self._t0)
            self._t0 = now
            if delta >= 1:
                self._lic.report_usage(delta)
                if self._lic.is_blocked():
                    state["license_blocked"] = True
```

E invocar `watchdog.tick()` no loop principal a cada iteração (entrada de `run_loop` no `main.py` final e no `_tick` do `main_window.py` — ver Task 11, podem ser feitas em conjunto).

- [ ] **Step 5: Correr o teste e ver que passa**

Run: `.venv\Scripts\python.exe -m pytest tests/test_main_flags.py -v`
Expected: PASS.

- [ ] **Step 6: Correr a suite do cliente**

Run: `.venv\Scripts\python.exe -m pytest tests -v`
Expected: PASS (sem regressões).

- [ ] **Step 7: Commit**

```bash
git add main.py tests/test_main_flags.py
git commit -m "feat(main): remove bypass --dev-pro e liga trial/revalidacao no arranque"
```

---

# PARTE 4 — UI e i18n

## Task 11: Strings de trial/bloqueio + watchdog de uso + pop-up de bloqueio

**Files:**
- Modify: `i18n.py`, `ui/license_dlg.py`, `ui/main_window.py`
- Test: `tests/test_i18n.py` (se existir) ou adicionar

- [ ] **Step 1: Adicionar strings de trial/bloqueio a `i18n.py`**

Em `i18n.py`, adicionar ao `_STRINGS`:

```python
    "license.trial_remaining": {
        "pt": "Trial gratis: {m} min restantes",
        "en": "Free trial: {m} min left",
    },
    "license.trial_ended": {
        "pt": "A tua experiencia Free terminou",
        "en": "Your free experience has ended",
    },
    "license.trial_ended_sub": {
        "pt": "Ativa o M\u00e3ouse PRO para continuar a controlar o cursor por gestos.",
        "en": "Activate M\u00e3ouse PRO to keep controlling your cursor by gestures.",
    },
    "license.activate_now": {
        "pt": "ATIVAR PRO AGORA",
        "en": "ACTIVATE PRO NOW",
    },
    "license.revalidate_failed": {
        "pt": "A tua licenca expirou. Liga-te para a renovar.",
        "en": "Your license expired. Connect to renew it.",
    },
    "license.ledge_blocked": {
        "pt": "Licenca nao valida nesta maquina.",
        "en": "License not valid on this machine.",
    },
    "license.has_key": {
        "pt": "Cola a tua chave Pro...",
        "en": "Paste your Pro key...",
    },
    "license.activate_key": {
        "pt": "Ativar Chave",
        "en": "Activate Key",
    },
    "license.enter_key": {
        "pt": "Cola primeiro a tua chave Pro.",
        "en": "Paste your Pro key first.",
    },
    "license.activate_failed": {
        "pt": "Ativacao falhou. Verifica a chave e a ligacao.",
        "en": "Activation failed. Check the key and connection.",
    },
    "license.needs_connection": {
        "pt": "Liga-te para confirmar o teu trial antes de começar.",
        "en": "Connect to confirm your trial before starting.",
    },
```

- [ ] **Step 2: Escrever um teste para as novas strings**

Criar/adicionar `tests/test_i18n.py`:

```python
import i18n


def test_license_block_strings_exist():
    for key in ("license.trial_remaining", "license.trial_ended",
                "license.activate_now", "license.revalidate_failed",
                "license.has_key", "license.activate_key",
                "license.enter_key", "license.activate_failed",
                "license.needs_connection"):
        t = i18n.tr(key)
        assert t and t != key
```

- [ ] **Step 3: Adicionar o watchdog de uso ao `main_window.py` `_tick`**

O trial conta tempo de uso real. No `_tick` do `main_window` (que já chama `process_frame`), quando `not self._license.is_pro` e `not is_blocked`, reportar `delta` de tempo ao `report_usage`. Ligar com o `state["license_blocked"]`.

- [ ] **Step 4: Adicionar o pop-up de bloqueio ao `ui/license_dlg.py`**

Adicionar um `BlockDialog` (pop-up de bloqueio total). **Importante:** o botão de upgrade chama `self._lm.open_checkout(...)` que ainda existe (API preservada). O fluxo de ativação online usa `self._lm.activate(key)` (que agora é a ativação online, sem `validate_key`):

```python
class BlockDialog(QDialog):
    """Pop-up de bloqueio total mostrado quando trial/lease expira."""
    def __init__(self, cfg, license_mgr, parent=None):
        super().__init__(parent)
        self._cfg = cfg
        self._lm = license_mgr
        self.setWindowTitle("M\u00e3ouse Pro \u2014 Licenca Terminada")
        self.setObjectName("SettingsDialog")
        self.setStyleSheet(MAIN_STYLESHEET)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(tr("license.trial_ended")))
        sub = QLabel(tr("license.trial_ended_sub"))
        sub.setWordWrap(True)
        lay.addWidget(sub)
        cta = QPushButton(tr("license.activate_now"))
        cta.setObjectName("ProCta")
        cta.clicked.connect(lambda: self._lm.open_checkout("lifetime", PADDLE_VENDOR_ID))
        lay.addWidget(cta)
        self._key_edit = QLineEdit()
        self._key_edit.setPlaceholderText(tr("license.has_key"))
        key_btn = QPushButton(tr("license.activate_key"))
        key_btn.clicked.connect(self._activate)
        lay.addWidget(self._key_edit)
        lay.addWidget(key_btn)
        self._error = QLabel("")
        lay.addWidget(self._error)

    def _activate(self):
        key = self._key_edit.text().strip()
        if not key:
            self._error.setText(tr("license.enter_key"))
            return
        if self._lm.activate(key):
            self._cfg.license_tier = Tier.PRO.value
            self.accept()
        else:
            self._error.setText(tr("license.activate_failed"))
```

E atualizar `LicenseDialog._activate_key` para o fluxo online (mostra feedback de sucesso/falha; `self._cfg.license_tier = Tier.PRO.value; self.accept()`). Manter `_deactivate`/`_open_checkout` (chamam métodos que continuam a existir).

- [ ] **Step 5: Abrir o pop-up de bloqueio no `main_window.py`**

No `_tick` (ou `_sync_license_ui`), abrir o `BlockDialog` uma única vez por sessão quando `is_blocked()`:

```python
from ui.license_dlg import BlockDialog  # no topo

# dentro de _tick / _sync_license_ui:
if (self._license is not None and self._license.is_blocked()
        and not self._block_shown):
    self._block_shown = True
    BlockDialog(self._cfg, self._license, self).exec()
```

- [ ] **Step 6: Correr os testes**

Run: `.venv\Scripts\python.exe -m pytest tests -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add i18n.py ui/license_dlg.py ui/main_window.py tests/
git commit -m "feat(ui): pop-up de bloqueio total + strings de trial + ativacao online"
```

---

## Task 12: Verificação final e penetração manual (checklist)

**Files:**
- Verify: toda a suite

- [ ] **Step 1: Correr toda a suite de testes do cliente**

Run: `.venv\Scripts\python.exe -m pytest tests -v`
Expected: PASS.

- [ ] **Step 2: Correr a suite do servidor**

Run: `.venv\Scripts\python.exe -m pytest license-server/tests -v`
Expected: PASS (15 tests).

- [ ] **Step 3: Verificação manual anti-burla**

Checklist (executar no ambiente):
- [ ] `--dev-pro` não existe: `python main.py --help` → sem `--dev-pro`.
- [ ] `AIRMOUSE_DEV_PRO=1` não tem efeito (removido).
- [ ] Trial esgota os 30 min → `is_blocked()` True → `process_frame` não move o rato.
- [ ] Apagar `license.json` e voltar a ligar com rede → `reconcile_trial()` puxa o `used_seconds` do servidor → NÃO volta a 30 min.
- [ ] Apagar `license.json` e estar SEM rede → `reconcile_trial()` bloqueia com `trial_requer_ligacao` (não concede trial novo).
- [ ] Forjar `license.json` com JWT `alg:none` / assinatura errada → `_validate_local_lease` rejeita → não concede PRO.
- [ ] Copiar `license.json` para outra máquina → `machine_id` difere → `load()` ignora → Free/trial.
- [ ] Ativar chave online liga a máquina; noutra máquina → 403 no servidor.
- [ ] Lease expira → `is_blocked()` True → bloqueio + pop-up.
- [ ] Revalidação com internet renova; sem internet usa até expirar.

- [ ] **Step 4: Lint/typecheck**

Run: `.venv\Scripts\python.exe -m ruff check core ui main.py config.py tools/`
Expected: PASS (sem erros novos).
Run: `.venv\Scripts\python.exe -m mypy core/`
Expected: sem erros novos críticos.

- [ ] **Step 5: Commit final (se houver alterações de fix)**

```bash
git add -A
git commit -m "chore: verificacao final do sistema de licenciamento a prova de fogo"
```

---

## Notas de execução / decisões a confirmar

- **Servidor** criado MAS a execução real do servidor (uvicorn) e o endpoint real de produção (`https://licenses.maouse.example.com`) ficam como tarefa de deploy fora deste plano (precisam do domínio e do VPS).
- **Chave pública ES256 embutida** (`core/licensing_public_key.pem`): em produção deve corresponder à privada do servidor real. O deploy deve substituir este ficheiro pela pública da chave privada de produção.
- **`cryptography` é nova dependência de runtime do cliente** (declarada em `pyproject.toml [project.dependencies]`, Task 8 Step 4). Necessária também para que o PyInstaller a inclua no exe. Verificar no packaging (spec do PyInstaller) que `cryptography` é coletada.
- **Paddle webhook** é mencionado no spec mas **fora** deste plano (o spec §8 YAGNI não o detalha; o webhook só ativa licença automaticamente pós-pagamento — pode ser adicionado depois). Este plano cobre emissão de chave via `/admin/keys` (fluxo manual de venda).
- O `PADDLE_VENDOR_ID` real continua TODO; o checkout mantém-se mas não é central para o bloqueio.
- **Trial offline sem registo local:** se o utilizador apagar `license.json` e estiver SEM rede, `reconcile_trial()` bloqueia com `trial_requer_ligacao` (não concede 30 min novos sem prova de "primeira vez"). Quando há rede, repõe o `used_seconds` real do servidor. Isto fecha o reset por delete (online-first híbrido, spec §6: "apagar ficheiro não reinicia").
- O watchdog de uso (Task 10/11) reporta apenas tempo de uso efetivo (não conta enquanto bloqueado/pausado).
- O `process_frame` gate usa `state["license_blocked"]` (set no arranque e atualizado pelo watchdog) + `active_license().is_blocked()`. A integração do watchdog atualiza `state["license_blocked"]` à medida que o trial consome.
