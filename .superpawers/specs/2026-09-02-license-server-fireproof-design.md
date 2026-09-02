# AirMouse — Sistema de Licenciamento à Prova de Fogo (Design)

- **Data:** 2026-09-02
- **Estado:** Aprovado pelo utilizador
- **Branch:** `feature/license-server-fireproof`

## 1. Objetivo

Tornar o sistema de pagamento/licenciamento do AirMouse **à prova de fogo** contra
burla e uso não pago. Princípios centrais definidos pelo proprietário:

> "Só usufrui da experiência quem paga; quem não paga tem pouco tempo."

Regras de negócio fixadas:

- **1 chave = 1 utilizador = 1 máquina. Nada mais.** Uma chave Pro não pode ser
  reutilizada noutro hardware nem partilhada entre pessoas.
- **Trial Free de 30 minutos de uso.** Ao expirar, **bloqueio total** com um
  pop-up apelativo para ativação dos planos.
- **Validação online-first** na ativação/renovação, com **lease offline** de
  duração longa (Abordagem B híbrida) para não degradar a experiência.
- Servidor de licenças corre num **VPS sempre online (~€4–6/mês)**.
- A câmara/voz/IA continuam **100% locais** — o servidor nunca processa esses
  dados (privacidade mantida, posicionamento do produto intacto).

## 2. Vulnerabilidades que este design elimina

O sistema atual (`core/licensing.py`) tem falhas críticas:

| # | Vulnerabilidade atual | Correção neste design |
|---|----------------------|----------------------|
| V1 | Sem limite de tempo no Free — uso ilimitado grátis | Trial de 30 min + bloqueio total |
| V2 | Flag CLI `--dev-pro` / `AIRMOUSE_DEV_PRO=1` desbloqueia tudo | Removida do executável final (compilada como off/ausente) |
| V3 | Secret HMAC em texto plano no source (`_DEFAULT_SECRET`) | Secret só no servidor; cliente assina com fingerprint + JWK pública |
| V4 | Validação 100% offline — chave copiável | Validação online na ativação + lease assinado por servidor |
| V5 | Chave não vinculada à máquina — serve em N equipamentos | Hardware fingerprint liga 1 chave a 1 máquina |
| V6 | `license.json` editável / restaurável (backup de licença Pro) | Estado assinado e o tier só é concedido por lease válido do servidor |

## 3. Visão geral da arquitetura

```
┌──────────────────────────┐        HTTPS/JWT         ┌──────────────────────────────┐
│    AirMouse Desktop      │ ◄──────────────────────► │  License Server (VPS)       │
│  (cliente — câmara/voz)  │   activate / lease /     │  Node.js + Postgres/SQLite  │
│  - fingerprint           │   heartbeat / trial      │  - emissão de chaves        │
│  - trial local (30min)   │                          │  - vínculo key↔machine      │
│  - valida lease offline  │                          │  - trial server-side        │
└──────────────────────────┘                          │  - webhook Paddle           │
        │ câmara/voz locais                           └──────────────┬───────────────┘
        └► nunca saem do dispositivo                                  │ webhook pago
                                                                      ▼
                                                            ┌──────────────────┐
                                                            │     Paddle       │
                                                            │ (merchant record)│
                                                            └──────────────────┘
```

**Ponte de integração:** o servidor tem um storage de licenças (equipamentos
vinculados, leases, trial) e expõe uma API assinada. O cliente guarda apenas o
estado localmente **assinado e de curtíssima validade** para funcionar offline.

## 4. Componentes

### 4.1 License Server (novo — diretoria `license-server/`)

Servidor autónomo em **Node.js/TypeScript ou Python/FastAPI** (escolher durante
implementação; recomendo FastAPI por coerência com o stack Python do projeto).

Responsabilidades:

- **Catálogo de chaves:** gerar chaves Pro, armazenar por hash da chave.
- **Vínculo máquina:** guardar `key_hash → {machine_id, email, activated_at}`.
  1 chave ligada a **exatamente 1** `machine_id`. Nova ativação com outro
  `machine_id` → **rejeitada** (este é o ponto duro da regra "1 chave = 1 máquina").
- **Trial:** associar `machine_id → {trial_used_seconds, expires_at}`. O servidor
  é a fonte de verdade do trial, para que apagar o ficheiro local não reinicie
  os 30 min.
- **Leases:** emitir um **lease assinado (JWT assinado com secret do servidor)**,
  com `exp` de duração configurável (ex.: 7 dias), que o cliente usa offline.
- **Webhook Paddle:** confirmar pagamento e emitir a chave/licença
  automaticamente (transição de trial → ativado).
- **Heartbeat:** endpoint para renovar/estender o lease e reportar keep-alive.

Endpoints propostos:

| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/v1/trial/start` | Regista máquina e inicia trial (idempotente) |
| GET  | `/api/v1/trial/status` | Consulta tempo de trial restante do servidor |
| POST | `/api/v1/activate` | `{key, machine_id}` → liga chave à máquina; devolve lease |
| GET  | `/api/v1/lease` | Renova/obtém lease de Pro offline |
| POST | `/api/v1/revoke` | Revoga máquina/chave |
| POST | `/api/v1/webhook/paddle` | Ativação pós-pagamento |
| POST | `/api/v1/heartbeat` | Keep-alive / renova lease |

Segurança do servidor:

- Chaves/secret **nunca em texto plano** no source do cliente.
- Hash das chaves (argon2/bcrypt) no storage — mesmo que a BD vaze, não dá para
  gerar chaves a partir dela.
- Rate-limiting e validação de `machine_id`.
- Logs de auditoria (ativação, revogações, tentativas de reutilização de chave).

### 4.2 Cliente AirMouse (modificação de `core/licensing.py`)

O `LicenseManager` é reescrito para:

- **Remover `--dev-pro` / `AIRMOUSE_DEV_PRO`** do fluxo de produção.
- **Calcular `machine_id`** (hardware fingerprint) e enviá-lo na ativação.
- **Gerir o trial de 30 min**: conta tempo de uso real (não relógio), sabe que
  fechar e reabrir não repõe o trial (fonte da verdade no servidor quando
  online; local assinado como fallback).
- **Guardar o lease** (JWT/assinatura do servidor) num ficheiro local assinado e
  verificar assinatura + `exp` antes de conceder Pro offline.
- **Bloqueio total** quando trial expira ou lease expira sem renovação: mostra o
  pop-up apelativo de ativação e não permite usar o AirMouse (nem move/click).

Ficheiros novos/alterados no cliente:

- `core/licensing.py` — reescrita (activation, lease, trial, fingerprint).
- `core/fingerprint.py` (novo) — calcula `machine_id` a partir de componentes
  únicos do hardware.
- `core/license_client.py` (novo) — transporte HTTPS + parsing de respostas.
- `ui/license_dlg.py` — pop-up apelativo (já existe p/ upgrade; estender para o
  bloqueio total).
- `main.py` — remover `--dev-pro`, integrar trial/lease no arranque.

### 4.3 Hardware fingerprint (`machine_id`)

Cálculo determinístico no Windows a partir de componentes difíceis de clonar:

- Serial do disco (Volume Serial / disk drive serial).
- UUID/MAC da placa-mãe e da interface de rede.
- Machine GUID (`HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid`).

Combinados num hash (SHA-256) → `machine_id`. Estável entre reinstalações,
diferente entre máquinas → **cópia de chave/ficheiro local para outro PC falha**
porque o `machine_id` não bate com o registado no servidor.

## 5. Fluxo de utilizador (happy path)

1. User instala AirMouse → Free, trial de 30 min começa (servidor regista
   `machine_id`).
2. User usa features Free até 30 min.
3. Trial expira → bloqueio total + pop-up: "A tua experiência Free terminou" com
   botões para os planos (Lifetime €39,90 / Sub €4,99 / Família / Access).
4. User compra via Paddle → webhook ativa a licença no servidor.
5. User recebe a chave → cola no AirMouse → `activate` liga `key↔machine_id`.
6. Cliente guarda lease e usa Pro **offline** até expirar (ex.: 7 dias).
7. De tempos a tempos, heartbeat renova o lease. Sem renovação → degrada para
   trial/bloqueio, com aviso.
8. Tentativa de usar a **mesma chave noutra máquina** → servidor rejeita
   (`machine_id` não corresponde ao vinculado). Aparece erro claro.

## 6. Tratamento de erros e casos edge

- **Offline no arranque sem lease válido** → bloqueio (com mensagem a pedir
  ligação). Não concede Pro se não for possível provar.
- **Offline com lease válido** → funciona (Abordagem B respeita usabilidade).
- **Clock do utilizador adiantado/atrasado** → `exp` do lease verificado com
  margem; lease assinado também inclui `nbf` para mitigar clock skew.
- **Apagar `license.json` / reinstalar** → trial não reinicia (servidor é a fonte
  da verdade por `machine_id`); chave continua ligada ao mesmo `machine_id`.
- **Fingerprint muda** (troca de disco/MAC) → revalidação via servidor pode
  pedir login ou um cooldown de segurança; caso legítimo de hardware novo é
  tratado pelo suporte com revogação da máquina antiga.
- **Reutilização de chave noutra máquina** → rejeitada; log de auditoria marca a
  tentativa.

## 7. Testes

### Cliente (pytest — continuar suite existente)
- `machine_id` determinístico na mesma máquina; distinto entre amostras.
- `activate` happy path com servidor fake → guarda lease, tier=PRO.
- Chave reutilizada noutro `machine_id` → rejeitada.
- Trial: contagem de uso real; não reinicia ao apagar ficheiro local.
- Lease expirado/corrompido → bloqueio total (não concede Pro).
- Offline sem lease → bloqueio com mensagem.
- `--dev-pro` ausente/neutro → sem bypass.

### Servidor (pytest/vitest)
- Emissão de chave; vínculo `key↔machine` exatamente 1.
- Segunda ativação noutra máquina → 409/403.
- Trial server-side idempotente (não reinicia).
- Webhook Paddle assinado ativa licença.
- Leases expiram e renovam.

### Segurança / penetração (manual, checklist)
- Copiar `license.json`+binário para outro PC → bloqueado (fingerprint diff).
- Editar `license.json` → assinatura rejeitada.
- Brute-force de chave → rate-limit / logout.
- Reverter relógio → não estende trial/lease.

## 8. Fora de âmbito (YAGNI)

- **Store App/Play IAP** da app mobile (monetização móvel é fase futura, já
  declarada no plano de negócio) — não neste spec.
- **Telemetria/análise** — não exigida; não adicionar.
- **Suporte multi-máquina / família** via servidor com associação >1 — a regra
  é estritamente 1:1:1; o plano "Família" (3 dispositivos) fica como item futuro
  com design próprio, fora deste spec.
- **Offline puro sem servidor** — o utilizador escolheu online-first híbrido.

## 9. Custo

- VPS sempre online: ~€4–6/mês (escolhido pelo utilizador).
- Domínio (opcional, se o endpoint for público com nome próprio): ~€10–15/ano.
- Sem custo de compute por uso (câmara/voz locais; servidor só validação).

## 10. Decisões a fechar durante implementação

- Stack do servidor: **FastAPI (Python)** recomendado por coerência com o projeto.
- Duração do lease offline: default **7 dias** (configurável no servidor).
- Storage: **SQLite** suficiente para 1 pessoa/start; migrar para Postgres se
  escalar.
- Formato do lease: **JWT HS256** assinado com secret do servidor.

---

*Este design segue a Abordagem B (híbrida) aprovada: validação online na
ativação/renovação, lease offline de longa duração, com a regra dura
1 chave = 1 utilizador = 1 máquina e trial Free de 30 min com bloqueio total.*
