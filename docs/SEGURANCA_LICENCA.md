# Segurança do Licenciamento — Mãouse (Anti-Bypass)

> **Objetivo:** descrever o modelo de ameaça, o que o sistema de licenciamento bloqueia, as
> margens residuais honestas e as regras operacionais de produção — para o dossiê técnico e
> para a equipa não vender "impenetrável".
> **Data:** 2026-09-05 · Autor: Luar Studio Angola · Estado: **implementado e validado** (ver §5).

---

## 0. Resumo

O licenciamento usa **defense-in-depth**: o servidor é a fonte de verdade (trial e ligação
chave↔máquina), as leases são **JWT assinadas com ES256** (verificadas localmente com a chave
pública embutida), e o runtime bloqueia quando trial/lease termina. Isto elimina os bypasses
"casuais" (apagar ficheiro, forjar JWT, copiar licença para outra máquina, dev-pro). **Não é**
impermeável a um reverse engineer dedicado que patche o binário — isso é inerente a qualquer
aplicação desktop local (o servidor continua a validar em cada ativação/revalidação).

---

## 1. Modelo de ameaça

| Atacante | Habilidade | O que tenta | Risco tratável |
|---|---|---|---|
| **Utilizador casual** | Apagar ficheiros, mexer em definições | Reiniciar o trial (apagar `license.json`) | ✅ Fechado (servidor-lembra) |
| **Script kiddie** | Editar JSON, procurar "cracks", usar ferramentas de edição de JWT | Forjar `license.json` com `alg:none`, copiar licença de outro PC | ✅ Fechado (ES256 + machine binding) |
| **Power user** | Conhecer o sistema de ficheiros, variáveis de ambiente | Procurar flag "developer", variável de bypass | ✅ Fechado (`--dev-pro`/`AIRMOUSE_DEV_PRO` removidos) |
| **Reverse engineer** | Desmontar o `.exe` (PyInstaller) e patchar o gate | Saltar a verificação no binário | ⚠️ Contido, não eliminado (ver §4) |
| **Atacante da API** | `curl`/script contra o license-server | Abusar `/api/v1/trial/*` com `machine_id` inventado | ⚠️ Contido — não abre PRO sem chave (ver §4) |

**Ativos protegidos:** a funcionalidade Pro (snap, voz, duas mãos, TTS, IA, autotune, low-light)
e a integridade da venda (1 chave = 1 utilizador = 1 máquina; trial de 30 min como degustação).

---

## 2. Superfície de ataque

1. **Cliente distribuído** — `AirMouse.exe` (PyInstaller), ficheiro `license.json`,
   `core/licensing_public_key.pem` (pública, embutida de propósito).
2. **Rede** — `HTTPS` para o license-server (`activate`, `revalidate`, `trial/*`).
3. **Servidor** — `license-server/` (FastAPI + SQLite), env vars de produção
   (`AIRMOUSE_LS_PRIVATE_KEY`, `AIRMOUSE_LS_ADMIN_TOKEN`, credenciais Google Play, segredos Paddle).
4. **Compra** — webhook Paddle (`transaction.completed`) → emissão de chave.

---

## 3. Mitigações implementadas (mapeamento bypass → mecanismo)

| Ataque | Resultado (sem mitigação) | Mecanismo | Onde |
|---|---|---|---|
| Apagar `license.json` com rede | Ganha 30 min novos | Trial **server-authoritative**: `used_seconds` só cresce (`MAX()`) e fica no servidor; o cliente reconcilia via `trial/status` + `trial/report` | `license-server/storage.py:set_trial_used` · `core/licensing.py:reconcile_trial` |
| Apagar `license.json` **sem** rede | Ganha 30 min novos offline | Sem registo local + servidor inalcançável → bloqueia com `trial_requer_ligacao` (não concede "primeira vez" sem prova) | `core/licensing.py:reconcile_trial` |
| Forjar `license.json` com JWT `alg:none` / assinatura errada | PRO offline | Lease é **JWT ES256**: `_validate_local_lease` só aceita `alg=ES256`, verifica a assinatura com a chave pública embutida (raw `r‖s` → DER) e recusa corrupção | `core/licensing.py:_validate_local_lease` · `_verify_es256_with` · `core/licensing_public_key.pem` |
| Copiar `license.json` para outra máquina | PRO noutro PC | Store carrega `machine_id`; se ≠ fingerprint local é **ignorado** → Free/trial | `core/licensing.py:load` · `core/fingerprint.py:machine_id` |
| Ativar a mesma chave noutra máquina | 1 chave = N máquinas | Regra dura no servidor: `machine_for_key` → segunda máquina recebe **403** | `license-server/service.py:activate` |
| Replay de uma lease antiga | Renova indefinidamente | `revocation_nonce` (≥ último visto) + `use_seq` estritamente crescente; anti-replay rejeita leases antigos | `core/licensing.py:_validate_local_lease` · `license-server/service.py:revalidate` · `storage.py:bump_revocation_nonce` |
| Replay do webhook Paddle | Emite chaves sem pagar | Webhook verifica **HMAC** e **dedup por `event_id`** | `license-server/app.py` (`POST /webhooks/paddle`) |
| Flag de dev `--dev-pro` / `AIRMOUSE_DEV_PRO` | PRO sem chave | **Removido** do CLI e do runtime | `main.py` (verificado em `tests/test_main_flags.py`) |
| Roubar a chave privada do README/docs | Forja leases | Chave privada **nunca** entra no repo (`license-server/*.pem` no `.gitignore`); só a pública é trackeada | `docs/ASSINATURA_DIGITAL.md` · `git` (ver §3.1) |

### 3.1. Higiene de segredos (verificada 2026-09-05)

- `git ls-files` → apenas `core/licensing_public_key.pem` (pública) está trackeado.
- `license-server/private.pem` e `public.pem` estão no `.gitignore` → não versionados.
- Token admin e chave privada do servidor vêm de **env vars** (`AIRMOUSE_LS_ADMIN_TOKEN`,
  `AIRMOUSE_LS_PRIVATE_KEY`) — sem defaults funcionais de produção.
- `PADDLE_PRODUCT_URLS` lê de env (`AIRMOUSE_PADDLE_*_URL`); `ui/license_dlg.py:26`
  tem `PADDLE_VENDOR_ID = 0  # TODO` — ainda **não operacional** (ver §6).

---

## 4. Margens residuais (honestas)

1. **Patch/RE do binário** — um atacante com o `.exe` (PyInstaller) pode desmontar e saltar o
   gate no cliente. **Mitigação:** o servidor continua a ser a fonte de verdade — cada
   ativação/revalidação valida a chave e a máquina; um binário adulterado não obtém leases
   novos nem concede PRO persistente contra a vontade do servidor. Proteção adicional prática:
   assinatura de código (o `.exe` assinado é detetado se modificado pelo SmartScreen/AV — ver
   `docs/ASSINATURA_DIGITAL.md`).

2. **Trial por `machine_id` não autenticado** — `/api/v1/trial/*` aceita um `machine_id`
   arbitrário; alguém a chamar diretamente com IDs novos obtém trial novo no servidor.
   **Não concede PRO** (requer chave/lease válida). O cliente distribuído usa sempre o
   fingerprint real. Se quiseres apertar mais tarde: rate-limit por IP + heurística
   (muitos `machine_id` por IP = abuso) — fora do alcance atual (YAGNI).

3. **Segredos de produção** — o elo mais fraco não é o código, é a operação: se
   `AIRMOUSE_LS_PRIVATE_KEY`, `AIRMOUSE_LS_ADMIN_TOKEN`, credenciais Play ou segredos Paddle
   forem expostos (logs, repo, imagem, suporte), o sistema torna-se forjável. Regras → §6.

---

## 5. Checklist de verificação (pente fino)

Reprodutível localmente (ver `docs/DESKTOP_LICENSE_URL.md` para arrancar o servidor de teste):

- [ ] `--dev-pro` não existe: `python main.py --help` → ausente.
- [ ] `AIRMOUSE_DEV_PRO=1` não tem efeito.
- [ ] Trial esgota 30 min → `is_blocked()` True → `process_frame` não move o rato
      (teste: `pytest tests/test_license_gate.py`).
- [ ] Apagar `license.json` + rede → `reconcile_trial()` puxa `used_seconds` do servidor → não volta a 30 min.
- [ ] Apagar `license.json` + SEM rede → bloqueia `trial_requer_ligacao`.
- [ ] Forjar `license.json` com `alg:none`/assinatura errada → rejeitado (teste: `tests/test_lease.py`).
- [ ] Copiar `license.json` para outra máquina → `load()` ignora (teste: `tests/test_licensing.py`).
- [ ] Ativar chave online liga a máquina; noutra máquina → 403 (teste: `license-server/tests/test_activate.py`).
- [ ] Lease expira → bloqueio + pop-up; revalidação com internet renova.
- [ ] `git ls-files` sem `*.pem` privado nem segredos (repetir antes de cada release).

**Estado atual (2026-09-05):** 137 testes ✅ (client + server) incluem os acima; smoke e2e real
contra servidor local ✅ (trial → chave `MAO-` → ativar → PRO → restart → revalidate → reativar).

---

## 6. Regras operacionais (produção)

1. **Segredos só no servidor** (Render env, nunca no repo, logs ou imagens): `AIRMOUSE_LS_PRIVATE_KEY`,
   `AIRMOUSE_LS_ADMIN_TOKEN`, `AIRMOUSE_GOOGLE_PLAY_CREDENTIALS_JSON`, segredos Paddle.
2. **Par privada↔pública emparelhada:** a pública embutida em `core/licensing_public_key.pem`
   **deve corresponder** à privada de produção antes do bake (verificar:
   `.venv\Scripts\python.exe tools/check_keypair.py` ou comparação PEM manual). Se a privada de
   produção for regenerada, **rebuildar o cliente na mesma release** — nunca a meio.
3. **Bake do URL:** gravar `PROD_LICENSE_SERVER_URL` real em `core/licensing.py:25` antes do
   build final (procedimento completo em `docs/DESKTOP_LICENSE_URL.md`).
4. **Paddle:** preencher `PADDLE_VENDOR_ID` e `AIRMOUSE_PADDLE_*_URL` quando a entidade UE e o
   catálogo existirem — hoje o checkout é fallback genérico (não operacional).
5. **Monitorização:** alerta para `/health` down e para picos de `403` (abuso de ativação);
   revisão periódica de `keys` (chaves emitidas via `/admin/keys` são as únicas vendas).
6. **`AIRMOUSE_MOBILE_DEV_ALLOW=1`** é só para dev do mobile — **nunca** em produção (validação
   Play real é obrigatória).

---

## 7. Go / No-go

- **Go (venda desktop consumer):** §6 cumprida + `PRONTIDAO_PARA_VENDA.md` bloqueadores
  (assinatura, bake URL, Paddle operacional). O nível atual já elimina o utilizador comum e
  levanta o preço do atacante dedicado — padrão da indústria para licenciamento desktop.
- **Fora de alcance (não prometer):** proteção absoluta contra RE de binário e DRM "bank-grade"
  (requer ofuscação/comparação remota contínua — não é o objetivo do produto).

---

*Segurança operacional — Luar Studio Angola · 2026. Complementa `docs/DESKTOP_LICENSE_URL.md`,
`docs/ASSINATURA_DIGITAL.md` e `BUSSINES/02_EXECUCAO/PRONTIDAO_PARA_VENDA.md`.*