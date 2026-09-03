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
