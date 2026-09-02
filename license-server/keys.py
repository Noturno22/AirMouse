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
