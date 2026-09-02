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
