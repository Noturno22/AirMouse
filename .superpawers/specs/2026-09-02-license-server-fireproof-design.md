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
│  - fingerprint           │   revalidate / trial     │  - emissão de chaves        │
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
  `exp` de **7 dias** e mecanismos anti-burla (server_time verificado,
  revocation_nonce, session_id/use_seq) — ver desenho robusto §4.4. O lease
  cobre o uso offline do pagante (revalidação 1x por semana) e limita a janela
  máxima de "uso sem revalidação" de um burlão a 7 dias.
- **Webhook Paddle:** confirmar pagamento e emitir a chave/licença
  automaticamente (transição de trial → ativado).
- **Revalidação periódica:** endpoint que renova o lease (devolvendo `server_time`
  assinado e `revocation_nonce`) e atualiza `last_seen` (mantém §4.4 M1/M2).

**Modelo de disponibilidade (o cliente funciona offline):**
A solução aceita que o utilizador **pode não ter internet permanente**. O cliente
**não** precisa de estar online para usar — só na **ativação inicial** e na
**revalidação periódica (1x por semana)**. Como a revalidação é só semanal, o
servidor não tem de ter disponibilidade 99.9% em tempo real; mesmo assim
recomenda-se robustez mínima para que a revalidação não falhe por causa do nosso
lado:

- **Replicação/backup** do storage para o `machine_id`, trial e leases sobreviverem
  a falhas.
- **Endpoints de failover** no cliente (lista de URLs) para o caso de um endpoint
  estar temporariamente em baixo na hora de revalidar.
- Evitar ponto único de falha simples (mínimo 2 instâncias / backups automáticos).

Isto mantém o utilizador pago a funcionar offline até 7 dias sem penalização, ao
mesmo tempo que garante que a janela de "revogação surtir efeito" é de no máximo
1 semana.

Endpoints propostos:

| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/v1/trial/start` | Regista máquina e inicia trial (idempotente) |
| GET  | `/api/v1/trial/status` | Consulta tempo de trial restante do servidor |
| POST | `/api/v1/activate` | `{key, machine_id}` → liga chave à máquina; devolve lease |
| GET  | `/api/v1/lease` | Renova/obtém lease de Pro offline |
| POST | `/api/v1/revoke` | Revoga máquina/chave |
| POST | `/api/v1/webhook/paddle` | Ativação pós-pagamento |
| GET  | `/api/v1/revalidate` | Revalidação periódica (1x/semana) — renova lease, devolve `server_time` + `revocation_nonce` |

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
- **Uso offline normal:** após a ativação inicial, o utilizador pago funciona
  sem internet — o lease local válido é a prova de licença. Não bloqueia por
  falta de conexão, apenas se o lease tiver expirado.
- **Revalidação periódica (1x por semana):** quando há internet, o cliente
  tenta renovar o lease (~a cada 7 dias). Se conseguir, tem mais 7 dias. Se não,
  continua offline até o lease expirar; só então pede ligação para renovar.
- **Failover de endpoints:** guarda uma lista de endpoints do servidor e tenta o
  seguinte quando o atual falha na hora de ativar/revalidar.
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

O lease é o coração da segurança. O ponto-chave da solução é que **o pagante
funciona offline** — por isso não se usa "estar online" para distinguir burlão.
O que distingue pagante de burlão é um **lease local criptograficamente válido**
(assinado pelo servidor + `machine_id` correto + campos anti-replay). Sem um
lease válido, ninguém usa Pro, esteja online ou não.

O lease **melhorado** resolve quatro ataques:

1. **Congelar o relógio** do PC → o `exp` nunca chega, o Pro dura para sempre.
2. **Guardar/reutilizar o lease** (ou um snapshot do `license.json`) para se
   manter Pro offline indefinidamente.
3. **Reutilizar a mesma chave noutra máquina** (cópia/clone).
4. **Não haver revogação** — uma revogação tem de surtir efeito num prazo
   aceitável.

Mecanismos (M1–M3):

#### M1 — Lease temporal + relógio verificado (offline-friendly)
- O servidor emite um lease com `exp` de **7 dias** (alinhado com a revalidação
  semanal). Durante esses 7 dias, o utilizador **funciona offline** — o lease
  local é a prova de licença. Não há heartbeat por segundo; a revalidação é
  **1x por semana** quando há internet.
- O servidor devolve um **`server_time` assinado** a cada renovação. O cliente
  compara o relógio local com esse `server_time`: se o relógio divergir mais que
  a tolerância (ex.: ±10 min), o lease é **invalidado** (anti-congelar relógio).
- O lease inclui `nbf` + `exp` com margem; o servidor regista `last_seen` por
  máquina e rejeita renovações cujos timestamps impliquem saltos de relógio.
- **Ao expirar o lease sem renovação** (7 dias sem internet / sem renovar), o
  cliente **bloqueia** e pede ligação -> isto limita o tempo máximo de "uso sem
  revalidação" a 7 dias, mesmo para o burlão que tente isolar o servidor.

#### M2 — Nonce de revogação server-side (stateless revocation)
- O servidor mantém um **número de revogação global** (`revocation_nonce`) que
  incrementa sempre que QUALQUER licença é revogada/expira forçosamente.
- Cada lease emitido embute o valor corrente de `revocation_nonce`.
- A revalidação devolve o nonce corrente ao cliente.
- **Regra:** um lease com `revocation_nonce` inferior ao nonce corrente é
  **inválido na próxima revalidação** — o cliente ao reconectar descobre que o
  lease está obsoleto sem o servidor apontar a chave individual. Associado à exp
  de 7 dias, isto garante que uma revogação surte efeito em **no máximo 7 dias**
  (limite da janela de "graça" de um burlão que isole o servidor).

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
  "exp": 1757424800,                // +7 dias (revalidação semanal)
  "server_time": 1756818800        // relógio do servidor no momento
}
```

#### Regras de decisão no cliente (são: gate de bloqueio)
- **Uso offline normal:** o cliente **não exige servidor**. Se o lease local é
  válido (assinatura + `machine_id` + `exp` não expirado + nonce + seq OK), o
  utilizador usa Pro **mesmo offline**. (É assim que o pagante sem internet
  continua a usar.)
- **Revalidação (1x/semana, com internet):** quando há conexão, o cliente tenta
  renovar. Sucesso → novo lease de 7 dias. Falha de rede → continua com o lease
  atual até expirar.
- **Bloqueio (apenas se):**
  - lease expirado (`exp` passado) e sem conseguir renovar → bloqueia e pede
    ligação;
  - lease com assinatura inválida / `machine_id` errado / nonce obsoleto / seq
    repetido → bloqueia.
- O burlão **sem lease válido** (chave clonada noutra máquina, snapshot antigo,
  relógio congelado) **nunca** entra — falha sempre a validação local do lease.

**Resultado:** com `server_time` verificado, `revocation_nonce`, `session_id` +
`use_seq` antireplay e `exp` de 7 dias, nenhum ataque sobrevive:
- Congelar o relógio → detetado pelo `server_time` verificado (M1) → bloqueia.
- Snapshot/backup do lease → `use_seq` replay detetado (M3) → bloqueia.
- Clonar a chave noutra máquina → `machine_id` não corresponde (M3) → bloqueia.
- Reincidente que isole o servidor → no máximo mantém o lease válido expirado em
  7 dias; sem renovação, bloqueia.

O pagante usa offline sem penalização dentro dos 7 dias do lease. O **pior
cenário para um reincidente** é usar o lease já emitido por até **7 dias** sem
renovar — e nunca além disso; para continuar a burlar teria de obter uma nova
chave paga. Este é um equilíbrio pro: segurança forte + boa experiência para o
cliente pago.

## 5. Fluxo de utilizador (happy path)

1. User instala AirMouse → Free, trial de 30 min começa (servidor regista
   `machine_id`).
2. User usa features Free até 30 min.
3. Trial expira → bloqueio total + pop-up: "A tua experiência Free terminou" com
   botões para os planos (Lifetime €39,90 / Sub €4,99 / Família / Access).
4. User compra via Paddle → webhook ativa a licença no servidor.
5. User recebe a chave → cola no AirMouse → `activate` liga `key↔machine_id`
   (ativação online, única vez obrigatória).
6. Cliente guarda o lease e passa a usar Pro **normalmente, offline se quiser**
   (lease válido 7 dias, ver §4.4).
7. **Revalidação 1x por semana:** quando houver internet, o cliente renova o
   lease (mais 7 dias). Sem internet, continua a usar até o lease expirar; ao
   expirar sem renovar → bloqueio + pedido de ligação (ver §4.4 M1).
8. Tentativa de usar a **mesma chave noutra máquina** → servidor rejeita
   (`machine_id` não corresponde ao vinculado). Aparece erro claro.

## 6. Tratamento de erros e casos edge

- **Offline no arranque com lease local válido** → **usa normalmente** (lease é a
  prova de licença; não exige servidor).
- **Offline no arranque sem lease válido** → **bloqueio** (mensagem a pedir
  ligação para ativar/renovar). Não concede uso sem licença provada.
- **Perda de conexão durante o uso** → continua a usar até o lease expirar; na
  revalidação seguinte (ou em vez disso, quando tentar renovar), se falhar, só
  bloqueia no termo do lease (§4.4 M1).
- **Lease expirado (7 dias) sem renovação** → **bloqueio** + pedido de ligação.
- **Clock do utilizador adiantado/atrasado (congelar relógio)** → `exp` verificado
  com `nbf`/margem e comparado com `server_time` assinado do servidor → invalida
  o lease (§4.4 M1).
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
- **Uso offline com lease válido → FUNCIONA (sem exigir servidor)** (M1).
- **Lease com `revocation_nonce` obsoleto → bloqueio** (M2).
- **Lease com `use_seq` repetido (replay/snapshot) → bloqueio** (M3).
- **Relógio local divergente do `server_time` (clock skew) → bloqueio/reativação**
  (M1).
- **Revalidação semanal: com internet renova (+7 dias); sem internet continua até
  expirar; expirado sem renovar → bloqueio** (M1).
- **Failover: endpoint primário falha na revalidação → cliente tenta os seguintes
  com sucesso** (§4.1).
- Offline sem lease válido → bloqueio com mensagem.
- `--dev-pro` ausente/neutro → sem bypass.

### Servidor (pytest/vitest)
- Emissão de chave; vínculo `key↔machine` exatamente 1.
- Segunda ativação noutra máquina → 409/403.
- Trial server-side idempotente (não reinicia).
- Webhook Paddle assinado ativa licença.
- Leases expiram (7 dias) e renovam (mais 7 dias).
- **`revocation_nonce` incrementa em revogação e anula leases antigos na próxima
  revalidação** (M2).
- **`session_id`/`use_seq` repetidos são detetados e rejeitados** (M3).
- **`server_time` assinado é devolvido na revalidação; `last_seen` atualizado** (M1).
- **Revalidação offline do cliente com lease válido não depende de estado
  regional** (dados partilhados por `machine_id`).

### Segurança / penetração (manual, checklist)
- Copiar `license.json`+binário para outro PC → bloqueado (fingerprint diff).
- Editar `license.json` → assinatura rejeitada.
- **Congelar o relógio do PC → clock-skew deteta e bloqueia** (M1).
- **Guardar/restaurar um snapshot antigo do lease → `use_seq` replay rejeitado**
  (M3).
- **Clonar chave/lease para outra máquina e bloquear o servidor via firewall →
  o clone nunca valida (machine_id) → bloqueado logo** (M3).
- **Sustentar o clone online por muito tempo → a exp de 7 dias expira sem
  renovação → bloqueio** (M1).
- **Servidor temporariamente fora na revalidação → o pagante com lease válido
  mantém uso até renovar** (§4.1).
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
- **Validação online:** obrigatória na **ativação inicial** (liga a chave à
  máquina) e na **revalidação periódica**; o uso seguinte é **offline**.
- **Duração do lease (revalidação):** **7 dias** — o utilizador pago funciona
  offline dentro do lease; renova 1x por semana quando há internet (§4.4 M1).
- **Sem zero-graça/online-strict:** o cliente usa offline com lease válido; só
  bloqueia se o lease expirar sem renovar ou se for inválido (§4.4).
- **Revalidação:** automática quando há internet (~a cada 7 dias); tentativa de
  renovação silenciosa.
- **Robustez do servidor:** backups/replicasção e failover de endpoints para a
  revalidação não falhar por causa do nosso lado (§4.1).
- **Clock-skew tolerância:** ±10 min entre relógio local e `server_time` (M1).
- Storage: **SQLite** suficiente para 1 pessoa/start; migrar para Postgres com
  réplicas se escalar.
- Formato do lease: **JWT HS256** assinado com secret do servidor.

---

*Este design segue a Abordagem B (híbrida) aprovada: ativação online única + uso
offline, revalidação 1x por semana (lease de 7 dias), regra dura
1 chave = 1 utilizador = 1 máquina e trial Free de 30 min com bloqueio total.*
