"""Leases ES256: assinatura com chave privada via caminho OU conteúdo PEM.

O conftest carrega as chaves por caminho (envs apontam para ficheiros). Aqui
forçamos o modo Render: AIRMOUSE_LS_PRIVATE_KEY/PUBLIC_KEY contêm o PEM literal
multi-linha, como quem cola o valor no painel do Render.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import security
from jwt import InvalidSignatureError


@pytest.fixture
def content_keys(monkeypatch):
    """Troca as envs de caminho para o conteúdo PEM (modo Render)."""
    with open(security._private_key_path(), "rb") as fh:
        priv_pem = fh.read().decode()
    with open(os.environ["AIRMOUSE_LS_PUBLIC_KEY"], "rb") as fh:
        pub_pem = fh.read().decode()
    monkeypatch.setenv("AIRMOUSE_LS_PRIVATE_KEY", priv_pem)
    monkeypatch.setenv("AIRMOUSE_LS_PUBLIC_KEY", pub_pem)


def test_sign_decode_roundtrip_with_content_envs(content_keys):
    claims = {"sub": "machine:abc", "tier": "pro", "use_seq": 3}
    token = security.sign(claims)
    decoded = security.decode_jwt(token)
    assert decoded["tier"] == "pro"
    assert decoded["use_seq"] == 3


def test_tampered_token_rejected_with_content_envs(content_keys):
    token = security.sign({"sub": "machine:abc", "tier": "pro"})
    tampered = token[:-1] + ("B" if token[-1] != "B" else "C")
    with pytest.raises(InvalidSignatureError):
        security.decode_jwt(tampered)
