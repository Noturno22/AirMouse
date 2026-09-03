# Anti-padrões, Riscos de Falha e Prontidão de Lançamento — Mãouse (AirMouse)

> O **complemento de prudência** à estratégia. Enquanto `ESTRATEGIA_GLOBAL.md` diz o que
> fazer, este documento diz o que **NÃO** fazer e o que **pode fazer o produto falhar** —
> sobretudo o cenário "*e se não funcionar em vários dispositivos?*" — e **quando é (e não é)
> seguro lançar**. Termina com a tese de que **Europa, EUA e Ásia são os alvos de maior
> liquidez** e por que a ordem de ataque deve refletir isso.
> **Data:** 2026-09-01 · Autor: Luar Studio Angola · Estado: **documento de prudência**.

---

## 0. A pergunta que este documento responde

> *"E se não funcionar em vários dispositivos? Ainda assim vendemos?"*
> *"Europa, EUA e Ásia também devem comprar — na verdade são os alvos de maior liquidez."*

Respostas curtas (detalhe nas secções seguintes):

1. **"E se não funcionar em vários dispositivos? Ainda assim vendemos?"** → **Sim, mas com
   regras.** Vendemos onde funcciona, **nunca** prometemos universalidade que não verificámos,
   e restringimos o "garantido" a um **conjunto de dispositivos validado**. A pior coisa que
   pode acontecer ao Mãouse não é vender pouco — é **vender a um hospital, prometer
   universalidade, e deixar 40% dos computadores a funcionar mal**. Esse é o risco que
   destrói a confiança institucional, a nossa maior alavanca de lucro.
2. **"Europa, EUA e Ásia são os alvos de maior liquidez"** → **Correto e decisivo.** Não são
   só os maiores mercados — são onde o **poder de compra, o consentimento a pagar por
   acessibilidade/compliance e o acesso a capital B2B** são mais altos. A ordem de ataque dos
   documentos anteriores (PT/BR/AO first) é **certa como *prova* e *linguagem***, mas a
   **maior liquidez está em EN/global (EUA/UE/Ásia) desde o dia 1** — a estratégia global
   (sec. 6 de `ESTRATEGIA_GLOBAL.md`) já prevê EN como 2.ª língua imediata; este documento
   reforça que **EN é o idioma da liquidez e não pode ser adiado**.

---

## 1. O que NÃO fazer (anti-padrões)

> Regra de ouro: **no arranque, o Mãouse é frágil em hardware alheio. A sobrevivência é não
> deixar que uma promessa universal vire uma reputação quebrada.** Estes são os anti-padrões
> que custam mais caro.

### 1.1. Não prometer "funciona em qualquer dispositivo" sem uma matriz validada

- **NÃO** escrever "funciona em qualquer webcam/portátil/telemóvel" em landing, loja ou
  contratos enquanto não houver uma **matriz de compatibilidade testada**.
- Os modelos MediaPipe/OpenCV são excelentes, mas **webcams fracas, drivers de câmera
  bloqueados, máquinas sem GPU/NPU, luz baixa e telemóveis low-end variam muito** (ver §2).
- **Em vez disso:** publicar a matriz de dispositivos compatíveis tan válida quanto possível e
  comunicar "*otimizado para X, Y, Z*" — não "*funciona em tudo*".

### 1.2. Não vender "acessibilidade garantida" nem "compliance garantido" sem prova

- **NÃO** usar "compliance EU EAA/WCAG" como promessa de conformidade auditável sem **auditoria
  independente** (risco legal — ver `ESTRATEGIA_GLOBAL.md` §2.2 Ação 2).
- **NÃO** prometer "independência" ou qualquer resultado terapêutico (disclaimer clínico
  obrigatório).
- **Em vez disso:** vender **capacidade de acesso certificada** (onde testada) + documentação;
  e um **roadmap de conformidade** honesto.

### 1.3. Não desbloquear o mercado institucional antes do produto ser estável

- **NÃO** fazer o marketing B2G/B2B "grande" (`ESTRATEGIA_GLOBAL` §3.1 onda 2) antes de ter
  blindado os bloqueadores técnicos (`PRONTIDAO_PARA_VENDA` TOP 5).
- Um contrato institucional, uma vez assinado, exige **SLA e suporte a sério**. Se não temos
  sequer licenciamento/gate/suporte prontos, **não vendemos a hospitais ainda** — a mancha de
  um contrato público mal servido é pior do que a ausência de contrato.

### 1.4. Não fazer o "mundo inteiro" no Y1 (escala prematura)

- **NÃO** localizar para ES/FR/DE/ja/zh... no Y1. O "global" tem de ser **EN como língua de
  liquidez + persistência geográfica (UE/PT/BR/AO)** e nada mais (ver `ESTRATEGIA` §6.1).
- **NÃO** abrir escritórios, equipas ou suporte em cada país. O modelo é **nativa IA**, custo
  ~zero — abrir operações reais mata a margem.

### 1.5. Não ancorar preço zero nem dar tudo de graça

- **NÃO** tornar o Free demasiado bom (o risco "grátis mata a venda" da sec. 17.3).
- Free = núcleo limitado com watermark. **Pro = snap, voz, duas mãos, IA, autotune** (gate a
  implementar — `PRONTIDAO` TOP 2).

### 1.6. Não ignorar o custo de processamento/VAT nem cobrar em moeda única frágil

- **NÃO** esquecer o ~3% + €0,30 + VAT UE nas margens (lacuna L6).
- **NÃO** depender de uma moeda volátil; cobrar em **EUR/USD**, contas multi-moeda (D5).

### 1.7. Não construir features novas antes de fechar os bloqueadores de venda

- **NÃO** adicionar gestos/novas funcionalidades enquanto o licenciamento, gate Free/Pro,
  assinatura do `.exe` e ações nativas Android não existirem. Features não vendem; a
  capacidade de **cobrar e proteger** é que vende.

---

## 2. O que pode fazer o Mãouse não funcionar — e o cenário multi-dispositivo

> Este é o coração do "e se não funcionar em vários dispositivos?". Duas dimensões:
> **(A)** fatores que degradam a experiência; **(B)** como responder **sem** matar a venda.

### 2.A. Fatores reais de heterogeneidade (por que varia de dispositivo para dispositivo)

| Fator | Impacto | Onde já mitigado |
|---|---|---|
| **Webcam fraca (resolução/fps baixos, sensor de má qualidade)** | Inferência mais lenta, gestos menos fiáveis | Realce luz baixa (CLAHE), tolerância confiança 0.5, auto-afinação |
| **Luz ambiente baixa/contraluz** | Perde landmarks da mão | CLAHE + exposição automática; mas há limites |
| **Sem GPU/NPU / CPU fraco** | FPS cai; latência aumenta; 180 Hz não atinge | `--gpu` cai para CPU; `--no-gui`; mas 30 fps pode não ser possível |
| **Driver de câmera bloqueado/antivírus** | Câmera não abre / `.exe` bloqueado | Code-signing EV; mas alguns drivers são manhosos |
| **Telemóvel Android low-end** | Frame processor trava; tela preta | Já houve crashes corrigidos; otimização low-end ainda pendente (`PROGRESSO`/`MOBILE_PLAN`) |
| **Adaptadores/telemóveis chineses com permissões invulgares** | AccessibilityService/perm não pedem corretamente | Teste em 5+ dispositivos variados (ver §2.B) |
| **Windows regionalizado em outras línguas** | UI Automation/snap pode variar | `core/snap.py` isolado + fallback geométrico |

### 2.B. A resposta comercial: "ainda assim vendemos?" → regra dos 3 tipos de dispositivo

A chave é **não tratar todos os dispositivos como iguais**. Definir 3 tipos:

| Tipo | Exemplo | Como tratar nas vendas |
|---|---|---|
| **Validado** | Matriz testada (ex.: notebooks comuns, webcam ≥720p, Android de gama média) | Vender com confiança; **marketing e contratos** baseiam-se aqui |
| **Aceite** | Funciona com ressalvas (luz fraca, CPU fraco) | Vender mas com aviso claro "requer luz/bom CPU"; **desconto/Pro menos essenciais** |
| **Não validado** | Dispositivos raros/antigos, telemóveis low-end extremos | **Não prometer**; oferecer trial free; **nunca** em contrato institucional |

**Regra de ouro comercial:**
- **Consumer:** **NÃO** vender com "trial + reembolso aberto" — uma política de devolução em
  aberto atrai **entusiastas que só querem experimentar e devolver**, corroendo a receita e o
  CAC. Em vez disso:
  - **O "experimentar" é a Free tier** (gated, com watermark) — o entusiasta prova de graça,
    sem nunca nos custar um reembolso.
  - **Refund apenas em casos legítimos:** falha técnica real em hardware **Validado** ou falha
    de entrega do serviço institucional (violação de SLA). Como só prometemos o que está na
    matriz ✅, o reembolso é raro — a matriz **previne** o abuso.
  - **IAP mobile:** a loja gere; sem "refund" promovido.
- **Institucional/B2B (o dinheiro gordo):** **NUNCA** fazer contrato sobre uma base de
  dispositivos não validados. No contrato, **especificar o parque de dispositivos** que o
  Mãouse suporta, e oferecer **piloto técnico de 2–4 semanas** para validar no parque real
  do cliente **antes** do contrato anual. Isto transforma a fraqueza em **prova e
  diferenciação** ("validamos com o teu parque antes de te prometer").

> **Resposta direta à pergunta:** *sim, ainda vendemos — mas* **com segmentação de
> dispositivos e prova antes do contrato**. Vendemos onde funcciona validado, restringimos o
> prometido, e usamos a validação como arma de venda. **Não vendemos cegos a um hospital com
> 500 computadores.** Essa é a diferença entre um negócio que cresce e um que morre na primeira
> máquina que falha.

### 2.C. Matriz de compatibilidade — como recolher os dados

A regra dos 3 tipos exige **dados reais, não opiniões**. A matriz é um ficheiro operacional
(`MATRIZ_DE_DISPOSITIVOS.md`) que se preenche **a cada teste em hardware real** — no arranque,
durante o beta fechado e a cada 5–10 dispositivos. Quanto mais completa e honesta, mais forte
a venda ("validámos no teu parque antes de te prometer") e mais baixo o risco de falha.

**Como classificar (escala de veredito):**

| Veredito | Critério observável |
|---|---|
| ✅ **Validado** | FPS ≥ 25, latência gesto→ação < 80 ms, zero cliques fantasma, gestos 12+ a funcionar, snap OK |
| 🟡 **Aceite** | Funciona com ressalvas documentadas (luz fraca, CPU fraco, ~20 fps) — exige aviso ao vender |
| ❌ **Não-validado** | Falha ou experiência inaceitável — **nunca** prometer; usar só em trial free |
| ⚠️ **Bloqueado** | Hardware/driver/perm impede o uso — **não** consta de contratos |

**Regra de distribuição por parque institucional:** um contrato B2B **só** pode cobrir
dispositivos ✅ Validado (e 🟡 Aceite com aviso assinado). Os ❌/⚠️ ficam fora — e isto é o que
permite ao piloto técnico validar no parque real do cliente antes do contrato anual.

> A **tabela-padrão preenchível** (para desktop e mobile) está em `MATRIZ_DE_DISPOSITIVOS.md`.
> Preencher uma linha por dispositivo testado; marcar com a data e o `--geometry` do build.

---

## 3. Quando NÃO devemos lançar (checklist de bloqueio)

> Lançar cedo demais com um produto frágil em hardware alheio é o erro nº1. O lançamento público
> só acontece quando as respostas a estas perguntas são "sim". Antes disso, só **beta fechado**.

| Pergunta | NÃO lançar se... | Sim quando... |
|---|---|---|
| **Consegue cobrar e proteger?** | Sem licenciamento/Paddle/gate Free-Pro | Bloqueadores 1–2 de `PRONTIDAO` fechados |
| **O `.exe` não assusta?** | Sem code-signing/instalador/versão | Bloqueador 3 fechado |
| **Mobile funciona de verdade?** | Ações nativas Android são no-op; sem IAP | Bloqueadores 4–5 fechados |
| **Há matriz de dispositivos?** | Testámos em <5 dispositivos variados | Matriz Validado/Aceite/Não-validado estabelecida |
| **Temos suporte?** | Sem SLA/tickets/DPA | SLA N1/N2 + DPA prontos (L2/L3) |
| **Legal blindado?** | Sem disclaimers clínicos/seguro RC/auditoria WCAG p/ institucional | Ações 2–3 de `ESTRATEGIA` §2.2 prontas |
| **Procura validada?** | Sem 10–15 descobertas institucionais | Validação de procura feita (S1 do plano 90d) |

**Faseamento de lançamento recomendado:**
1. **Beta fechado (Y0–S1):** 100 utilizadores, validação de procura, matriz de dispositivos,
   roadshow institucional, PR de origem.
2. **Consumer (EN/PT):** lançamento Free+Pro — sem reembolso em aberto (ver §5 Reembolso).
3. **Institucional (só depois de provas):** piloto pago + contrato, com parque validado.

---

## 4. Quando PODEMOS lançar — o que tem de estar pronto no dia 1

| Camada | Mínimo para o launch |
|---|---|
| **Produto** | Desktop vendável (bloqueadores 1–3), mobile na Play (bloqueadores 4–5) |
| **Cobrança** | Paddle (D2) + IAP + gate Free/Pro (D1) |
| **Legal** | Marca/domínios, entidade UE (D5), privacy policy, disclaimers, termos PT/BR/EN |
| **Suporte** | SLA N1/N2 (L2), DPA (L3), canal de tickets |
| **Fúnel** | Landing + 3 vídeos (PT-BR + EN) + open-core GitHub |
| **Prova** | Matriz de dispositivos + (p/ institucional) auditoria WCAG + 1 piloto |

> **EN no dia 1, não no dia 400.** Se Europa/EUA/Ásia são a maior liquidez, a landing e o
> produto têm de estar em **EN desde o arranque** (a decisão D4 já o exige). Adiar EN é
> adiar os mercados de maior liquidez.

---

## 4.5. Política de Reembolso — receita-first (contra o entusiasta "só a experimentar")

> **Problema:** uma política de reembolso em aberto ("trial, devolve se não gostares") atrai
> **entusiastas que pagam, usam 15 dias e pedem devolução** só para experimentar. Isso corrói
> a receita, infla o CAC e drena a equipa com pedidos. **O "experimentar" não pode ser o
> reembolso.**

### A regra: quem quer experimentar → usa a Free tier, não a devolução

| Quem quer... | Usa | Porquê |
|---|---|---|
| Experimentar sem risco | **Free tier** (gated, watermark) | Prova de graça, sem nos custar um reembolso |
| Por no PC do dia-a-dia/empresa | **Pro** (paga) | Compromete porque já viu o Free a funcionar |
| Instituição (centro/hospital) | **Piloto técnico** (2–4 semanas) | Valida no parque real antes de assinar |

### Quando fazemos refund (raramente)

| Cenário | Reembolso? |
|---|---|
| Falha técnica real em hardware **Validado** (matriz ✅) | ✅ Sim (raro — a matriz previne) |
| Falha de entrega/SLA em institucional | ✅ Sim (contrato) |
| "Não gosto/não estava à espera" | ❌ Não (o Free tier cobria a experimentação) |
| IAP mobile | Loja gere; nunca promovemos refund |

> **Como a matriz protege a receita:** só prometemos o que está ✅ Validado — logo, quase nunca
> devolvemos por "não funciona". O reembolso legítimo é **raro por desenho**, não por generosidade.

---

## 5. Europa, EUA e Ásia — os alvos de maior liquidez (tese e ordem)

### 5.1. Por que são de maior liquidez (não só maiores)

| Mercado | Por que liquidez alta | Alavanca Mãouse |
|---|---|---|
| **EUA** | Maior poder de compra; **Section 508** (federal); cultura de startups/VC/PR; primeiro em adotar "morte do periférico" | Marketing EN; verticais apresentadores/criadores; B2B healthcare; licenciamento OEM |
| **Europa (UE)** | **EU EAA (28/06/2025)** = procura legal institucional; orçamento de compliance; subsídios | Pacote compliance turnkey (o motor de lucro §2 de `ESTRATEGIA`) |
| **Ásia (JP/KR/CN/SEA)** | Mercado tech massivo; telemóveis low/mid-end; alta densidade de apresentadores/criadores | Volume mobile; OEM (PC/telemóvel); acessibilidade emergente |

### 5.2. A ordem correta (não é "PT/BR first" na prática comercial)

- **Prova & linguagem:** começar em PT/BR/AO (custo zero, voz pt_BR pronta, casa do fundador).
- **Liquidez:** **EN (EUA/UE/global) desde o dia 1** para capturar quem mais paga.
- **Institucional UE:** aproveitar a EU EAA (a maior procura legal paga).
- **Ásia/OEM:** só após provas e produto estável (Y2–Y3).
- **Replicação:** o clonador ataca primeiro EN/global — por isso **EN e chegada à loja têm
  data**, como em `ESTRATEGIA` §6.2.

> **Conclusão de liquidez:** o objetivo "lucro exorbitante nas primeiras vendas"
> (`ESTRATEGIA`, sec. 1) é **alcançado mais depressa em EN/EUA/UE** (compliance + B2B) do que
> em qualquer mercado de baixa liquidez. PT/BR/AO são a **prova e a origem**; EN/EUA/UE são a
> **caixa**. Os dois não se excluem — **EN é 2.ª língua imediata** e o institucional UE é o
> motor, como já planeado.

---

## 6. Resumo executivo — o que NÃO fazer vs o que fazer

| ❌ NÃO | ✅ SIM |
|---|---|---|
| Prometer "funciona em qualquer dispositivo" | Matriz de dispositivos Validado/Aceite/Não-validado |
| Vender compliance/independência sem prova auditada | Roadmap de conformidade + disclaimer clínico + auditoria WCAG |
| Abrir escritórios/equipas por país | Modelo nativa IA, EN global, tudo remoto |
| Lançar institucional antes de produto estável | Piloto técnico no parque do cliente antes do contrato |
| Funcionalidade nova antes dos bloqueadores de venda | Licenciamento/gate/assinatura/ações nativas primeiro |
| Adiar EN | EN no dia 1 (EN = liquidez) |
| Escala prematura no mundo todo no Y1 | UE + PT/BR/AO + EN, só depois expandir |
| **Reembolso em aberto ("trial, devolve se não gostares")** | **Free tier = experimentação; refund só p/ falha real em Validado/SLA** |

---

*Documento de prudência — Luar Studio Angola · 2026. Complementa ESTRATEGIA_GLOBAL.md, PLANO_DE_EXECUCAO_90_DIAS.md, DECISOES.md e PRONTIDAO_PARA_VENDA.md.*
