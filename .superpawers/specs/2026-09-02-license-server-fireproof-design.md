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
- **Leases:** emitir um **lease assinado (JWT HS256, secret do servidor)** com
  `exp` de **30 minutos** e mecanismos anti-burla (heartbeat + server_time,
  revocation_nonce, session_id/use_seq) — ver desenho robusto §4.4. O lease curto
  + heartbeat limitam a janela offline a poucos minutos: impossível usar o Pro
  com uma licença revogada/expirada por longos períodos.
- **Webhook Paddle:** confirmar pagamento e emitir a chave/licença
  automaticamente (transição de trial → ativado).
- **Heartbeat:** endpoint para renovar o lease, devolver `server_time` assinado e
  `revocation_nonce`, e atualizar `last_seen` (mantém §4.4 M1/M2).

**Alta disponibilidade do servidor (essencial para zero-graça):**
Como o cliente já não tolera offline (zero graça), o servidor tem de estar
**praticamente sempre acessível** — caso contrário pune-se o utilizador legítimo:

- **Multi-região / edge**: implantar o License Server em múltiplas regiões
  (ex.: Vercel/Fly edge) ou atrás de um CDN/load-balancer global.
- **Failover automático**: o cliente mantém uma **lista de endpoints** e tenta o
  seguinte quando o atual falha.
- **Health checks** contínuos; se um endpoint cai, os pedidos migram
  automaticamente.
- **Armazenamento partilhado e consistente** entre regiões (Postgres gerido /
  banco com replicação global), para o `machine_id`, trial e leases serem os
  mesmos onde quer que o pedido chegue.
- **Objectivo de disponibilidade**: ≥99.5% medida em pedidos recebidos, de modo
  a que a "falta de servidor" seja um evento raro, não um argumento de burla.

Endpoints propostos:

| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/v1/trial/start` | Regista máquina e inicia trial (idempotente) |
| GET  | `/api/v1/trial/status` | Consulta tempo de trial restante do servidor |
| POST | `/api/v1/activate` | `{key, machine_id}` → liga chave à máquina; devolve lease |
| GET  | `/api/v1/lease` | Renova/obtém lease de Pro offline |
| POST | `/api/v1/revoke` | Revoga máquina/chave |
| POST | `/api/v1/webhook/paddle` | Ativação pós-pagamento |
| POST | `/api/v1/heartbeat` | Heartbeat / renova lease |

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
  verificar assinatura + `machine_id` + `exp` + `revocation_nonce` + `use_seq`
  antes de conceder Pro offline (ver desenho robusto §4.4).
- **Heartbeat periódico** (~30–60 s) que renova o lease e reporta `last_seen`;
  verifica o `server_time` devolvido contra o relógio local (anti-clock-skew).
- **Failover de endpoints** (HA): guarda uma lista de endpoints do servidor e
  tenta o seguinte quando o atual falha; bloqueia só se todos falharem.
- **Zero-graça offline**: não arranca nem continua sem contactar o servidor —
  bloqueio imediato se o heartbeat/heartbeat de arranque falhar (ver §4.4 M1).
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

### 4.4 Desenho robusto do lease (melhorado)

O lease é o coração da segurança. O design anterior (JWT com `exp` de 30 min)
era fraco por três motivos — um utilizador determinado podia:

1. **Congelar o relógio** do PC → o `exp` nunca chega, o Pro dura para sempre.
2. **Guardar/reutilizar o lease** (ou um snapshot do `license.json`) para se
   manter Pro offline indefinidamente.
3. **Não haver revogação imediata** — uma revogação só surtiria efeito no
   próximo heartbeat (até 30 min).

O lease **melhorado** resolve isto combinando três mecanismos:

#### M1 — Heartbeat + relógio verificado (estrito, zero-graça)
- O cliente envia heartbeat ao servidor em intervalos curtos (ex.: **30–60 s**).
- O servidor responde com um **`server_time` assinado**. O cliente compara o
  relógio local com o `server_time`: se o relógio local divergir muito (clock
  skew > tolerância, ex.: ±10 min), o lease é **invalidado** e exige reativação.
- O lease não é apenas temporal: guarda também **contador de atividade** e o
  cliente prova atividade regular via heartbeat. Estar "offline com relógio
  congelado" deixa de funcionar porque o servidor marca o `last_seen` e anula o
  lease quando o cliente deixa de aparecer.
- **Zero-graça offline:** o cliente **não tolera offline**. Se o heartbeat
  falhar (ou se não haver servidor atingível no arranque), o AirMouse **bloqueia
  imediatamente** — sem período de graça. Em vez de o cliente "aguentar" quedas
  de rede (o que dava a janela de 2–3 min ao reincidente), a disponibilidade é
  garantida pelo **servidor de alta disponibilidade** (multi-região + failover,
  §4.1). O utilizador legítimo com falha de rede momentânea é raro e remediado
  pela HA do servidor; o reincidente que bloqueia o servidor ganha **0 segundos**
  porque o cliente pára sem servidor.

#### M2 — Nonce de revogação server-side (stateless revocation)
- O servidor mantém um **número de revogação global** (`revocation_nonce`) que
  incrementa sempre que QUALQUER licença é revogada/expira forçosamente.
- Cada lease emitido embute o valor corrente de `revocation_nonce`.
- O heartbeat devolve o nonce corrente ao cliente.
- **Regra:** um lease com `revocation_nonce < nonce_atual` é **inválido à primeira
  falha de heartbeat** — o cliente, ao reconectar, descobre que o seu lease está
  obsoleto mesmo sem o servidor lhe apontar a chave individual. Leases antigos
  são anulados globalmente quando o servidor volta a estar online.

#### M3 — Anti-clock-skew + anti-snapshot
- **Anti-clock-skew:** além de comparar com `server_time`, o lease usa `nbf` +
  `exp` com margem; o servidor regista `last_seen` por máquina e rejeita pedidos
  cujo timestamps impliquem saltos no relógio.
- **Anti-snapshot:** o lease contém um **`session_id` único** criado na ativação
  e um **contador de uso crescente** (`use_seq`). Restaurar um snapshot antigo
  do `license.json` reintroduz um `session_id`/`use_seq` velho que o servidor já
  viu — o servidor deteta a repetição (números já usados) e rejeita, obrigando a
  reativação. Isto elimina o "backup e restauro da licença Pro".

#### Estrutura do lease (exemplo — JWT HS256)
```json
{
  "sub": "machine:<machine_id>",
  "key_hash": "ab12...",            // chave ligada
  "tier": "pro",
  "session_id": "uuid-sessao-unica",
  "use_seq": 128445,                 // contador crescente de uso
  "revocation_nonce": 7,            // valor corrente no servidor
  "iat": 1756820000,
  "nbf": 1756817000,
  "exp": 1756821800,                // +30 min
  "server_time": 1756818800        // relógio do servidor no momento
}
```

#### Regras de decisão no cliente (são: gate de bloqueio)
- Lease válido (assinatura + `machine_id` + `exp` + nonce + seq OK) **e**
  servidor atingível → **Pro liberto**.
- Qualquer falha de contacto com o servidor (arranque ou heartbeat) →
  **bloqueio imediato, zero graça**. O cliente tenta os endpoints de failover
  (HA) e, se nenhum responder, pára.
- Lease expirado / nonce obsoleto / relógio divergente / seq repetido →
  **bloqueio total** + pedido de reativação/heartbeat.

**Resultado:** com `server_time` verificado, `revocation_nonce`, `session_id` +
`use_seq` antireplay, **zero graça offline** e servidor de alta disponibilidade,
nenhum dos ataques (relógio congelado, snapshot, falta de revogação, isolar o
servidor) sobrevive. O pior cenário para um reincidente é **0 segundos** de uso
Pro não pago: sem contacto com o servidor, o cliente bloqueia logo. A
compensação para o utilizador legítimo é a **disponibilidade ≥99.5%** do servidor
e o **failover** entre endpoints, garantindo que a ausência de servidor é um
evento raro — não um benefício para burla.

## 5. Fluxo de utilizador (happy path)

1. User instala AirMouse → Free, trial de 30 min começa (servidor regista
   `machine_id`).
2. User usa features Free até 30 min.
3. Trial expira → bloqueio total + pop-up: "A tua experiência Free terminou" com
   botões para os planos (Lifetime €39,90 / Sub €4,99 / Família / Access).
4. User compra via Paddle → webhook ativa a licença no servidor.
5. User recebe a chave → cola no AirMouse → `activate` liga `key↔machine_id`.
6. Cliente guarda o lease e usa Pro (lease de 30 min, ver §4.4).
7. O **heartbeat (~30–60 s)** renova o lease e mantém o Pro vivo enquanto há
   contacto com o servidor. Se o servidor se tornar inalcançável (todos os
   endpoints de failover falharem), há **bloqueio imediato, zero graça** (com
   aviso a pedir ligação) — ver §4.4 M1.
8. Tentativa de usar a **mesma chave noutra máquina** → servidor rejeita
   (`machine_id` não corresponde ao vinculado). Aparece erro claro.

## 6. Tratamento de erros e casos edge

- **Offline no arranque, sem servidor atingível (nem failover)** → **bloqueio
  imediato** (mensagem a pedir ligação). Não concede uso se não for possível
  provar a licença.
- **Perda de conexão durante uso** → o heartbeat falha; após tentar todos os
  endpoints de failover sem resposta → **bloqueio imediato, zero graça** (§4.4 M1).
- **Clock do utilizador adiantado/atrasado** → `exp` verificado com `nbf`/margem
  E comparado com o `server_time` assinado do servidor (§4.4 M1).
- **Snapshot antigo do lease restaurado** → `session_id`/`use_seq` repetido →
  replay rejeitado, reativação obrigatória (§4.4 M3).
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
- **Lease com `revocation_nonce` obsoleto → bloqueio** (M2).
- **Lease com `use_seq` repetido (replay/snapshot) → bloqueio** (M3).
- **Relógio local divergente do `server_time` (clock skew) → bloqueio/reativação**
  (M1).
- **Qualquer falha de heartbeat (arranque ou durante uso, todos os endpoints de
  failover esgotados) → bloqueio imediato, zero graça** (M1).
- **Failover: endpoint primário cai → cliente tenta os seguintes com sucesso** (HA).
- Offline sem lease → bloqueio com mensagem.
- `--dev-pro` ausente/neutro → sem bypass.

### Servidor (pytest/vitest)
- Emissão de chave; vínculo `key↔machine` exatamente 1.
- Segunda ativação noutra máquina → 409/403.
- Trial server-side idempotente (não reinicia).
- Webhook Paddle assinado ativa licença.
- Leases expiram e renovam.
- **`revocation_nonce` incrementa em revogação e anula leases antigos** (M2).
- **`session_id`/`use_seq` repetidos são detetados e rejeitados** (M3).
- **`server_time` assinado é devolvido; heartbeat atualiza `last_seen`** (M1).
- **Estado partilhado/consistente entre regiões (machine_id, trial, leases)** (HA).
- **Health check e migração de pedidos quando uma região cai** (HA).

### Segurança / penetração (manual, checklist)
- Copiar `license.json`+binário para outro PC → bloqueado (fingerprint diff).
- Editar `license.json` → assinatura rejeitada.
- **Congelar o relógio do PC → clock-skew deteta e bloqueia** (M1).
- **Guardar/restaurar um snapshot antigo do lease → `use_seq` replay rejeitado**
  (M3).
- **Banir/bloquear TODOS os endpoints do servidor via firewall num PC clonado →
  cliente bloqueia em 0s** (M1 + HA).
- **Derrubar uma região → failover migra para outra, licença continua a validar**
  (HA).
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
- Duração do lease offline: **30 minutos** (curto — limita a janela offline e
  obriga a revalidação frequente com o servidor).
- **Heartbeat:** intervalos de **~30–60 s**; **zero graça offline** (bloqueio
  imediato sem contacto com o servidor, ver §4.4 M1).
- **Alta disponibilidade:** multi-região/edge + failover entre endpoints;
  objetivo de disponibilidade ≥99.5% (§4.1).
- **Clock-skew tolerância:** ±10 min entre relógio local e `server_time` (M1).
- Storage: **SQLite** suficiente para 1 pessoa/start; migrar para Postgres
  replicado entre regiões se escalar (para a HA).
- Formato do lease: **JWT HS256** assinado com secret do servidor.

---

*Este design segue a Abordagem B (híbrida) aprovada: validação online na
ativação/renovação, lease offline de 30 minutos, com a regra dura
1 chave = 1 utilizador = 1 máquina e trial Free de 30 min com bloqueio total.*
