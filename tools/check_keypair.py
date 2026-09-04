"""Verifica que a chave pública do license-server coincide com a embutida no cliente.

Uso:
  python tools/check_keypair.py
  python tools/check_keypair.py --server license-server/private.pem \\
      --client core/licensing_public_key.pem

Sem --server: usa `AIRMOUSE_LS_PRIVATE_KEY` ou `license-server/private.pem` (default).
Sem --client: usa `core/licensing_public_key.pem` (default).

Saída: 0 se forem o mesmo par (pública derivada == pública embutida), 1 caso contrário.
"""
import argparse
import os
import sys

from cryptography.hazmat.primitives import serialization


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server", default="",
                    help="caminho da chave privada do servidor")
    ap.add_argument("--client", default="core/licensing_public_key.pem",
                    help="caminho da chave publica embutida no cliente")
    args = ap.parse_args()

    server_priv = args.server or os.getenv(
        "AIRMOUSE_LS_PRIVATE_KEY",
        os.path.join("license-server", "private.pem"))

    for path, label in ((server_priv, "privada do servidor"),
                        (args.client, "publica embutida no cliente")):
        if not os.path.exists(path):
            print(f"ERRO: ficheiro nao existe: {path} ({label})")
            return 1

    with open(server_priv, "rb") as fh:
        priv = serialization.load_pem_private_key(fh.read(), password=None)
    server_pub = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo).strip()

    with open(args.client, "rb") as fh:
        client_pub = fh.read().strip()

    if server_pub != client_pub:
        print("ERRO: as chaves NAO coincidem.")
        print("A privada apontada pelo servidor e a publica embutida no cliente")
        print("tem de ser o mesmo par. Regenera/embute antes do bake")
        print("(docs/SEGURANCA_LICENCA.md §6.2).")
        return 1

    print("OK: a chave publica do servidor coincide com a embutida no cliente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

