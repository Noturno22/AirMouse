# Desktop — URL do License Server em Produção

> **Gap de produção (descoberto 2026-09-04, durante verificação do fluxo de licença).**
> Este documento descreve como o desktop descobre o servidor de licenças e o que é preciso
> fazer **antes de distribuir o `.exe`** para que a ativação de licenças funcione no cliente.

---

## O problema

O `LicenseManager` do desktop obtém o(s) URL(s) do license-server a partir da variável de
ambiente `AIRMOUSE_LICENSE_URLS`:

```
core/licensing.py → _default_endpoints()
    raw = os.getenv("AIRMOUSE_LICENSE_URLS", "")
    return [...] or ["https://licenses.maouse.example.com"]
```

Sem a env var definida, cai num **placeholder** (`licenses.maouse.example.com`, que não existe).
**Clientes não têm nem vão ter env vars** — portanto, num `.exe` distribuído tal como está hoje,
a ativação/validação de licença **falharia sempre** (mas o trial local continua a funcionar).

O `tools/issue_pro_key.py` (lado operacional) tem o mesmo padrão mas usa `AIRMOUSE_LS_URL`.

## O que foi verificado (2026-09-04)

- O **fluxo completo** (trial → emitir chave `MAO-` → ativar → PRO → restart persiste → revalidate)
  **passa de ponta a ponta** contra um license-server real a correr localmente (release `4e12423`).
- As chaves pública/privada do servidor e a chave pública embutida no cliente **coincidem**
  (diferença anterior era só um newline de fim de ficheiro).

## Como corrigir (ações a executar na release)

### 1. Deployar o license-server
Seguir `license-server/DEPLOY_RENDER.md` (conta Render + env vars + disco). Fica um URL real:
`https://<service>.onrender.com`.

### 2. Gravar o URL real como default de produção no build
Em `core/licensing.py`, `_default_endpoints()`: substituir o placeholder pelo URL real (ou
configurar num ponto único). O env `AIRMOUSE_LICENSE_URLS` continua a ser o override para testes.

```python
def _default_endpoints():
    raw = os.getenv("AIRMOUSE_LICENSE_URLS", "")
    return [u.strip() for u in raw.split(",") if u.strip()] or [
        "https://<service>.onrender.com"   # ← URL REAL de produção
    ]
```

> Igualar também `tools/issue_pro_key.py` (`AIRMOUSE_LS_URL` default) se o desktop a usar.

### 3. Rebuildar e assinar o `.exe`
Depois do bake, correr `build.bat` (que já assina com `cert\maouse.pfx`, ver
`docs/ASSINATURA_DIGITAL.md`) e redistribuir **simultaneamente** com o novo URL — nunca mudar o
URL depois de distribuir sem o rebuildar.

### 4. Smoke test de ativação no `.exe` final
Abrir o `.exe` distribuído e ativar com uma chave real → confirmar que fica PRO e que o lease
é validado (ver `Get-AuthenticodeSignature` para a assinatura e o fluxo descrito na
`PRONTIDAO_PARA_VENDA.md` §1).

## Notas

- **Não partilhar o URL**: apesar de público, evitar documentá-lo no README do utilizador;
  deve ficar só no build e nas docs operacionais.
- **Ambiente de teste:** para apontar a um servidor local/QA, definir `AIRMOUSE_LICENSE_URLS`
  (ex.: `http://127.0.0.1:8099`) antes de correr `main.py`.
- **Não reverter o URL a meio:** um `.exe` antigo com o placeholder deve ser substituído, não
  "reparado" server-side.

---

*Operacional · Luar Studio Angola · 2026. Complementa `license-server/DEPLOY_RENDER.md`,
`BUSSINES/02_EXECUCAO/PRONTIDAO_PARA_VENDA.md` e `docs/ASSINATURA_DIGITAL.md`.*
