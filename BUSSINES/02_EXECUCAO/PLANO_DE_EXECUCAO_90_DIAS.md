# Plano de Execução — 90 Dias — Mãouse (AirMouse)

> Passa do modelo de negócio para **execução**. Prioriza os **bloqueadores de receita**
> sinalizados em `REVISAO_E_VALIDACAO.md` (§4: marca, posicionamento acessibilidade,
> fúnel, code-signing) e integra as decisões de `DECISOES.md`.
> **Data:** 2026-09-03 (atualizado) · Autor: Luar Studio Angola · Alcance: 90 dias (3 sprints de 30 dias).

---

## 0. Norte do plano

> **Objetivo:** lançar as primeiras vendas pagas no final dos 90 dias, com o segmento 1
> (acessibilidade) como motor, sem quebrar os bloqueadores técnicos (assinatura .exe,
> Play policy, entidade UE). Cada fase termina com **algo vendável ou prova de receita**.

Os **3 riscos bloqueadores de receita** (prioridade total, antes de qualquer feature nova):

| # | Bloqueador | Janela |
|---|---|---|
| 🔴 1 | Registo de **marca + domínios** (moat nº1) | Semana 1 |
| 🔴 2 | **Posicionamento acessibilidade** em tudo (site, loja, docs, Play policy) | Semana 1–4 |
| 🔴 3 | **Code-signing** do `.exe` (EV) + presença nas lojas | Semana 2–10 |

---

## 1. Sprint 1 — Fundação jurídica e de marca (Dias 1–30)

### 1.1. Identidade e propriedade intelectual (Semana 1)

| Ação | Detalhe | Quem/Como | ✅ |
|---|---|---|---|
| Registo da marca `Mãouse` | EUIPO (CTM) + USPTO + PT/BR; depositar logótipo + slogan "a mão é o novo mouse" | Advogado de PI / Agente oficial | |
| Registo de domínios | `maouse.app / .io / .pt / .com` + variantes anti-typosquatting | Registo imediato (barato, fecha a porta) | |
| Contas oficiais | GitHub org, e-mail institucional, redes sociais com handle `maouse` | Fundador | |
| Primeiro `AGENTS.md` de marca | Tom de voz, linguagem, regras de comunicação | Escrever nesta repo | |

### 1.2. Estrutura jurídica (Semana 1–4) — decisão D5

| Ação | Detalhe | ✅ |
|---|---|---|
| Consulta de contabilista PT | Forma exata (Soc. Unipessoal Lda) + registo de VAT | |
| Constituição da entidade UE | Necessária p/ Paddle, lojas, subsídios EU, contratos B2B | |
| Acordo de licença de IP Angola → PT | Separar riscos e propriedade intelectual | |
| Conta multi-moeda | EUR principal; corretora/gateway multi-currency | |

### 1.3. Fúnel & posicionamento (Semana 2–4)

| Ação | Detalhe | ✅ |
|---|---|---|
| **Landing page** (`maouse.app`) | Demo 10–30s no topo; posicionamento **acessibilidade** primeiro; desconto 50% (D3) visível; botão download Free + Pro | |
| **3 vídeos de demonstração** | (1) Acessibilidade/independência, (2) Apresentação mão-livre, (3) Mobile→PC modo remoto | |
| Wizard de onboarding | Guiar o utilizador do download ao "primeiro wow" < 3 min | |
| Lista de 10 centros de reabilitação | PT/BR/AO + 5 universidades — contactos para pilotos | |
| Open-core no GitHub | Publicar núcleo gestos/IA (gera comunidade + provas + SEO) | |

### 1.4. Validação técnica do arranque (Semana 2–4)

| Ação | Detalhe | ✅ |
|---|---|---|
| Teste de polimorfismo antivírus | Antivírus falsos positivos ao `.exe` | |
| Confirmar assinatura de código | EV signing / Microsoft Store route (risco nº3) | |
| Revisão Pocket A11y policy | Documentação de conformidade p/ Google Play (risco nº2) | |
| **Iniciar LAB de hardware** | Montar a área `HARDWARE/` (LAB.md, PROBLEMAS_KNOWN, CHECKLIST) e preencher a `MATRIZ_DE_DISPOSITIVOS.md` com 5+ devices (desktop + mobile low-end) durante o beta | |

### 1.5. Validação da PROCURA (Semana 2–4) — novo, do ESTRATEGIA_GLOBAL §2.1a

| Ação | Detalhe | ✅ |
|---|---|---|
| **10–15 conversas de descoberta** | Centros de reabilitação PT/BR/AO, RH hospitalar, juristas de compliance | |
| Testar a disposição a pagar | "Quanto pagariam por utente/ano por acesso por gestos+voz?" | |
| Decidir tamanho da aposta | Confirmar ou reajustar o pilar institucional do Y1 | |
| Agendar auditoria WCAG independente + seguro RC | Para vender pacote compliance sem risco legal (ESTRATEGIA §2.2 Ações 2–3) | |

**Saída do Sprint 1:** marca+domínios registados, entidade UE em constituição, landing +
3 vídeos ar, open-core publicado, 10 contactos institucionais feitos, **procura validada**,
auditoria WCAG + seguro RG agendados.

---

## 2. Sprint 2 — Produto vendável + 1º piloto (Dias 31–60)

> Estas ações correspondem aos **bloqueadores técnicos de venda** auditados em
> `PRONTIDAO_PARA_VENDA.md` (TOP 5). Têm **data**, não "quando houver tempo" — é a
> resposta concreta ao risco de o clonador chegar à loja primeiro (ESTRATEGIA §6.2).

### 2.1. Desktop vendável (bloqueador nº3 + nº1 + nº2)

| Ação | Detalhe | ✅ |
|---|---|---|
| `.exe` polido | PyInstaller + **EV code-signing** + `console=False` + ícone + VersionInfo (empresa/produto) + instalador 1-clique (Inno/NSIS) | |
| **Licenciamento** | Validar licença Pro (D1) — chave/serial offline+online via **Paddle** (D2); deteção de chave | |
| **Gate Free/Pro** | Watermark na Free; bloquear snap/voz/2 mãos/IA para Free; modal de upgrade Pro | |
| Installer robusto | "1-clique", sem SmartScreen assustador | |
| Teste em máquinas limpas | 5 máquinas sem Python: instalação → 1º uso sem erros | |

### 2.2. Primeiros receitas

| Ação | Detalhe | ✅ |
|---|---|---|
| Paddle checkout activo | Licença Pro lifetime + sub + desconto acessibilidade + **política de reembolso (D7)** aplicada na configuração de refunds (`POLITICA_DE_REEMBOLSO.md`) | |
| Primeiras licenças Pro | Beta users → conversão paga | |
| **1º piloto institucional** | Assinar 1 centro de reabilitação (piloto: 5–20 licenças; objetivo = 1 contrato pequeno p/ ano, break-even mais curto) | |
| Protocolo de prova clínica | Esboçar com universidade (não esperar Y3) — lacuna L4 | |

### 2.3. Mobile Android (Play Store)

| Ação | Detalhe | ✅ |
|---|---|---|
| **Implementar ações nativas Android** | Touch, Keyboard, System via módulos + **AccessibilityService** no Manifest (bloqueador nº4 de `PRONTIDAO`) | |
| Remover permissões mortas | Tirar `WRITE_SETTINGS`/`SYSTEM_ALERT_WINDOW` se não houver código que as use (risco de rejeição Play) | |
| **IAP Pro (pago único)** | Play Billing / expo-iap + product `maouse_mobile_pro` + validação server-side no license-server (`/api/v1/mobile/entitle` → Google Play → lease `tier=mobile_pro`) + restore (**✅ code feito 2026-09-03**; falta prebuild/upload) | |
| Store listing | Posicionamento **acessibilidade**; vídeo de conformidade; privacy policy URL; icons Mãouse | |
| Testes em 5 dispositivos low-end | FPS, estabilidade, policy A11y | |
| Submissão à Play Store | Posicionamento **acessibilidade** como propósito primário | |

**Saída do Sprint 2:** desktop vendável com assinatura, checkout Paddle a funcionar,
1º piloto institucional assinado, mobile submetido/na Play Store.

---

## 3. Sprint 3 — Escala do fúnel + primeiros pagantes (Dias 61–90)

### 3.1. Crescimento orgânico

| Ação | Detalhe | ✅ |
|---|---|---|
| Lançar criadores | 5 criadores de tech/acessibilidade (demo viral) | |
| Video Shorts TikTok/YouTube/IG | Clip "a webcam já é um rato" | |
| Parceria com 3 terapeutas ocupacionais | Como "prescribes" do Mãouse | |
| SEO da landing | PT-BR + EN | |

### 3.2. Operação de vendas

| Ação | Detalhe | ✅ |
|---|---|---|
| SLA definido (L2) | N1 < 8h úteis · N2 < 48h · atendimento 5×8 | |
| Modelo DPA (L3) | ART. 28 GDPR pronto p/ contratos B2B/B2G | |
| Política de privacidade → conformidade | Opt-in telemetria OFF (D6); GDPR/LGPD | |
| Dashboard de métricas | Downloads, conversão, churn, NPS, pipeline institucional | |

### 3.3. Decisão de roadmap (dia 90)

Revisão dos 3 cenários (`MODELO_DE_NEGOCIO` §13) com dados reais da fase final.
Decidir se acelerar: institucional (B2G), consumer mass (lojas), ou OEM.

**Saída do Sprint 3:** fúnel a converter, primeiros pagantes recorrentes, pipeline
institucional ativo, decisão de direção Y2 tomada com dados.

---

## 4. Quadro resumo das 7 lacunas (L1–L7) → onde entram no plano

| Lacuna | Sprint | Ação |
|---|---|---|
| L1 Dialetos PT | S2/S3 | PT-BR base (D4); roadmap pt_PT/pt_AO explícito; **não prometer "PT" genérico** |
| L2 SLA | S3 | Fixar N1/N2 e disponibilidade |
| L3 DPA | S1 | Modelo ART. 28 GDPR para B2B/B2G |
| L4 Prova clínica | S2 | Protocolo com universidade desde já (não Y3) |
| L5 Canal familiar C2C | S3 | Relegado p/ fase consumer |
| L6 Custos de pagamento/VAT | S1/S2 | Paddle MoR (D2); modelar ~3% + VAT nas margens |
| L7 Compliance de loja com datas | S2 | Datas explícitas: Play submissão, revisão docs policy |

---

## 5. Orçamento indicativo (90 dias)

| Categoria | Estimativa | Nota |
|---|---|---|
| Registo marca (EUIPO+USPTO) | €300–600 | Uma vez; moat nº1 |
| Domínios | €50 | Barato, fechar cedo |
| Constituição entidade UE + advogado | €600–1.500 | Bloqueador B2B/B2G |
| Assinatura de código EV | €300–500/ano | Bloqueador desktop |
| Landing + 3 vídeos | €200–500 | Pode ser DIY com IA |
| Ferramentas (Paddle, EAS, CI) | €100–300 | Near-zero |
| Marketing orgânico criadores | €300 | Demo viral = CAC principal |
| **Total aproximado** | **€1.900–3.700** | Dentro do custo fixo ~€2k/mês da sec. 12 |

---

## 6. Definição de "feito" (completar os 90 dias)

1. ✅ Marca + domínios `Mãouse` registados (moat nº1).
2. ✅ Desktop vendável com assinatura de código e checkout Paddle a funcionar.
3. ✅ Mobile Android na Play Store, posicionado como acessibilidade.
4. ✅ Fúnel ativo: landing + 3 vídeos + open-core, a converter.
5. ✅ **1º piloto/contrato institucional** assinado (caminho mais curto para break-even).
6. ✅ Entidade UE em ordem (VAT, IP Angola→PT).
7. ✅ Métricas e SLA operacionais a reportar.

---

## 7. Estado atual & ponto de retoma (CHECKPOINT — atualizado 2026-09-01)

> **Para retomar:** lê esta secção. Tudo o que está ✅ está feito e fundamentado em documentos;
> o "Próximo passo" é a decisão mais óbvia que resta. Basta dizer "vamos fazer X".

### 7.1 Estado estratégico (o que já está fechado)

| Área | Estado | Ficheiro |
|---|---|---|
| Decisões comerciais D1–D7 | ✅ Fechadas | `DECISOES.md` |
| Modelo de negócio (break-even corrigido) | ✅ | `MODELO_DE_NEGOCIO.md` |
| Validação técnica | ✅ VALIDADO | `REVISAO_E_VALIDACAO.md` |
| Estratégia global / 1ª venda com lucro / alvos UE+EN | ✅ | `ESTRATEGIA_GLOBAL.md` |
| Auditoria técnica de prontidão (5+1 blockers) | ✅ | `PRONTIDAO_PARA_VENDA.md` |
| O que NÃO fazer / riscos / quando lançar | ✅ | `ANTIPADROES_E_RISCOS.md` |
| Política de reembolso (D7, receita-first) | ✅ texto pronto | `POLITICA_DE_REEMBOLSO.md` |
| Área do gargalo de hardware | ✅ criada | `HARDWARE/` (LAB, PROBLEMAS_KNOWN, CHECKLIST) |
| Matriz de dispositivos (resultados) | 🟡 0 ✅ / 1 🟡 / 0 ❌ | `MATRIZ_DE_DISPOSITIVOS.md` |

### 7.2 Bloqueadores de venda (implementação = código)

| # | Bloqueador | Estado (2026-09-03) | Onde implementar |
|---|---|---|---|
| 1 | Licenciamento + gate Free/Pro + trial + leases | ✅ Feito — servidor FastAPI+SQLite em `license-server/`; cliente em `core/licensing.py`/`license_client.py`/`fingerprint.py`; gate em `core/engine.py:process_frame` | Desktop |
| 1b | **Paddle checkout** (pagamento automático → emissão de chave + email) | ✅ Feito — webhook `transaction.completed` com HMAC + dedup + email (`license-server/paddle.py`) | Desktop (S2) |
| 2 | Gate + modal de upgrade | ✅ `ui/license_dlg.py` (upgrade/desativação) | Desktop |
| 3 | `.exe` polido (assinatura/ícone/versão/console=False) | 🔴 Só falta **assinatura de código** (cert EV/OV ×PFX); ícone/versão/console/instalador/pipeline de assinatura automática já ✅ | Desktop (S2) |
| 3b | Instalador 1-clique (Inno Setup) | ✅ Feito — `installer.iss` + `dist/Maouse-Setup-1.0.0.exe` (15,6 MB) | Desktop (S1) |
| 4 | Ações nativas Android + AccessibilityService | ✅ Feito — `AirMouseAccessibilityService` + Touch/Keyboard/System modules ligados no JS; permissões mortas removidas | `mobile/airmouse-mobile/` (S2) |
| 5 | **IAP mobile + store listing** | 🟡 **IAP ✅ code feito** (expo-iap + validação Google no license-server + paywall `ProGate`); falta **prebuild/upload/listing Play Console** | `mobile/airmouse-mobile/` (S2) |
| 6 | LAB de hardware a correr / preencher matriz | 🟡 | `HARDWARE/` (S1–S2) |

### 7.3 Testes de hardware já feitos

| Dispositivo | FPS | Veredito | Detalhe |
|---|---|---|---|
| HP Notebook · Intel i3-5005U · sem GPU | 14.6 fps (48.3 ms) | 🟡 Aceite | 0 glitches; câmara 640×480@30; `python main.py --frames 60 --no-preview --no-gui` |

### 7.4 Próximo passo (escolher UMA via)

- **A) Fechar blockers de execução comercial → 1ª venda paga:**
  - ✅ Licenciamento + trial + leases + **Paddle automático** + gate + **IAP mobile Pro** (code) já feitos.
  - 🔴 Falta (execução, não código): **certificado de code-signing** (EV/OV ×PFX → assinar `.exe`/instalador via `build.bat`) + **prebuild/upload/listing mobile Play Console** + **LAB de hardware** na matriz.
- **B) Testar hardware real** — desbloqueia a matriz e as promessas honestas:
  - Desktop com GPU/NPU (confirmar se sobe aos 25+ fps → ✅).
  - 1º telemóvel low-end Android (risco tela preta).

> Recomendação: como o **gargalo é hardware**, testar um **desktop com GPU** primeiro dá a prova
> rápida de que o produto sobe a 25+ fps (desbloqueia ✅ no marketing e contratos); em paralelo
> trata-se do **certificado de code-signing** (bloqueador desktop nº1) e do **upload/listing mobile**.

---

*Plano de execução — Luar Studio Angola · 2026. Baseado em MODELO_DE_NEGOCIO.md + REVISAO_E_VALIDACAO.md + DECISOES.md + HARDWARE/.*
