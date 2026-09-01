"""
Emite uma chave Pro (offline, HMAC) para um comprador do Mãouse.

Ferramenta para o fundador/suporte: USAR APENAS COM O SECRET REAL DE
PRODUÇÃO (variavel de ambiente AIRMOUSE_LICENSE_SECRET). Nunca emitir com o
secret de dev default — essa chave seria valida no executavel. O script recusa
quando o secret é o default inseguro.

Uso:
    python tools/issue_pro_key.py comprador@exemplo.pt
    AIRMOUSE_LICENSE_SECRET=... python tools/issue_pro_key.py a@b.c
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.licensing import _DEFAULT_SECRET, LicenseManager

_SECRET = os.getenv("AIRMOUSE_LICENSE_SECRET", "")


def main():
    if len(sys.argv) < 2:
        print("Uso: python tools/issue_pro_key.py <email-do-comprador>")
        sys.exit(1)
    if not _SECRET or _SECRET == _DEFAULT_SECRET:
        print("ERRO: defina AIRMOUSE_LICENSE_SECRET com o secret real de "
              "producao antes de emitir chaves. O default de dev nao e seguro.")
        sys.exit(1)
    email = sys.argv[1].strip()
    if "@" not in email:
        print(f"Email invalido: {email!r}")
        sys.exit(1)
    lm = LicenseManager()
    key = lm.issue_pro_key(email)
    print(key)
    print("Guarde esta chave e envie ao comprador. Depois da compra Paddle,")
    print("o comprador cola a chave em Ficheiro > Licenca > Ativar Chave.")


if __name__ == "__main__":
    main()
