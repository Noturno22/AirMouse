# Modelo de Marketing & Vendas — Mãouse (AirMouse)

> O motor de aquisição e conversão que liga o produto à receita. Construído sobre
> `MODELO_DE_NEGOCIO.md`, `DECISOES.md`, `ESTRATEGIA_GLOBAL.md`, `ANTIPADROES_E_RISCOS.md`
> e `PLANO_DE_EXECUCAO_90_DIAS.md`. **Data:** 2026-09-02 · Autor: Luar Studio Angola.
> **Promessa deste documento:** um modelo que se **corrige a si próprio** antes de
> transformar um erro em prejuízo grave — o mais próximo de "infalível" que a física
> do mercado permite.

---

## Índice

1. [A verdade sobre "infalível" — e como este modelo o consegue](#1-a-verdade-sobre-infalível--e-como-este-modelo-o-consegue)
2. [A Arquitetura do Funil — dois canos, um motor](#2-a-arquitetura-do-funil--dois-canos-um-motor)
3. [A Mensagem-Mãe e o Banco de Copy](#3-a-mensagem-mãe-e-o-banco-de-copy)
4. [O Loop Viral — o produto é o anúncio](#4-o-loop-viral--o-produto-é-o-anúncio)
5. [Playbook de Vendas Institucionais (o dinheiro gordo)](#5-playbook-de-vendas-institucionais-o-dinheiro-gordo)
6. [Canais por Fase — 90 dias / Y1 / Y2](#6-canais-por-fase--90-dias--y1--y2)
7. [Precificação como Arma de Marketing](#7-precificação-como-arma-de-marketing)
8. [Radar de Métricas — o painel semanal](#8-radar-de-métricas--o-painel-semanal)
9. [Gatilhos de Decisão — Kill / Pivot / Scale](#9-gatilhos-de-decisão--kill--pivot--scale)
10. [Checklists Anti-Erro — pré-lançamento por canal](#10-checklists-anti-erro--pré-lançamento-por-canal)
11. [Orçamento e Alocação](#11-orçamento-e-alocação)
12. [Contingências — o que fazer se X falhar](#12-contingências--o-que-fazer-se-x-falhar)
13. [OKRs de Marketing — 90 dias](#13-okrs-de-marketing--90-dias)

---

## 1. A verdade sobre "infalível" — e como este modelo o consegue

Nenhum marketing é infalível por si; **o mercado é um adversário que se adapta**. Um modelo é
infalível *na prática* quando **deteta o erro antes de ele custar caro** e **tem uma decisão
pré-programada para cada falha provável**. É exatamente isso que este documento entrega:
não uma previsão, mas um **sistema de verificação contínua**.

As 9 regras que tornam este modelo à prova de falha:

| # | Regra | Porquê evita erro |
|---|---|---|
| 1 | **Métrica por hipótese, gatilho por métrica** | Nenhuma campanha "corre por fé": cada uma tem um número que decide Kill/Pivot/Scale (§9) |
| 2 | **Verificar antes de afirmar** | Nada se publica sem passar a checklist anti-erro do seu canal (§10) — imita a cultura de verificação do repo |
| 3 | **Dois canos de receita em paralelo** | Se o consumer falhar, o institucional mantém a empresa; e vice-versa (§2) |
| 4 | **O produto é o anúncio** | Elimina o erro nº1 de startups: gastar em ads antes de ter prova de valor (§4) |
| 5 | **Nunca prometer o que não está provado** | Matriz de dispositivos antes de prometer; compliance auditado antes de vender (§5, §10) |
| 6 | **EN no dia 1** | Liquidez global (EE.UU./UE/Ásia) não espera localização (§6, D4) |
| 7 | **Reembolso raro por desenho** | Free tier = experimentação; refund só falha real em dispositivo Validado (D7) |
| 8 | **Orçamento com teto por teste** | Erro financeiro limitado a um valor decidido antes — nunca "vamos ver quanto custa" (§11) |
| 9 | **Revisão semanal obrigatória** | Os números decidem; o ego não (§8) |

> **Definição operacional de "infalível":** um modelo onde, para qualquer desvio do plano,
> existe uma deteção ≤ 7 dias e uma resposta pré-escrita. Desvio sem deteção é acidente;
> desvio com resposta é estratégia.

---

## 2. A Arquitetura do Funil — dois canos, um motor

O Mãouse tem **dois funis paralelos** que se alimentam mutuamente:

```
        ┌─────────────────────── CANO A: CONSUMER ───────────────────────┐
        │  Descoberta → Demo (10-30 s) → Free (watermark) → "Wow" <3 min  │
        │  → Upgrade Pro → Comunidade → UGC → novo descoberto             │
        │  O Free é o anúncio contínuo: cada watermark é uma impressão.   │
        └──────────────────────────────┬──────────────────────────────────┘
                                       │ prods prova social de impacto
                                       ▼
        ┌─────────────────────── CANO B: INSTITUCIONAL ──────────────────┐
        │  Descoberta (EU EAA) → Conversa de validação → Piloto pago      │
        │  (€2-5k, 4-8 sem.) → Relatório compliance → Contrato €5-50k/yr │
        └──────────────────────────────┬──────────────────────────────────┘
                                       │ caso de estudo + brilho de marca
                                       ▼
                                     MOTOR (comum): marca Mãouse + PR
```

### 2.1. Porquê os dois em paralelo (e não em série)

| Argumento | Decisão |
|---|---|
| O institucional paga mais por unidade (1 contrato ≈ 375 subs) | 🔴 Prioridade no **Cano B** para caixa |
| O consumer gera volume, provas, e alimenta o storytelling institucional | 🔴 Prioridade no **Cano A** para futuro e prova |
| 90% das falhas de marketing vêm de depender de **um só** canal | Ter sempre ambos ativos desde o dia 1 |

### 2.2. Regras de entrada em cada cano

- **Cano A (consumer):** só abre em força quando o Free gated + watermark existir e o `.exe`
  estiver assinado (bloqueadores 1–3 de `PRONTIDAO_PARA_VENDA.md`). Antes disso = **só beta
  fechado + lista de espera**.
- **Cano B (institucional):** só assina contrato quando houver **matriz de dispositivos
  validada**, **auditoria WCAG** e **seguro RC** (`ANTIPADROES_E_RISCOS.md` §3). O **piloto
  pago** pode começar logo após essas provas — nunca antes.

> **Erro mortal evitado:** lançar o funil consumer antes de poder cobrar, ou assinar contrato
> antes de poder cumprir. Ambos estão bloqueados por checklist, não por intenção.

---

## 3. A Mensagem-Mãe e o Banco de Copy

### 3.1. A Mensagem-Mãe (o pitch em 1 frase que toda a comunicação herda)

> **"A tua webcam já é um rato. Nós só precisamos do software."**

### 3.2. Os 5 ângulos de valor (banco de copy)

| Ângulo | Público | Frase âncora | CTA padrão |
|---|---|---|---|
| **Independência** | Acessibilidade/saúde | "Controla o teu PC e telemóvel só com a mão e a voz. Sem hardware, sem fios, 100% privado." | "Testa grátis em 3 minutos" |
| **Morte do periférico** | Tech / imprensa | "O rato físico de €25–100 acabou. O futuro é software." | "Assiste à demo" |
| **Mão livre** | Apresentadores/professores | "Apresenta a andar, controla os slides à distância, fala com as mãos como sempre quiseste." | "Vê o professor Rui" |
| **Compliance** | Instituições | "Acessibilidade EU EAA em apenas uma semana — software + relatório + formação, num pacote." | "Falar com a equipa" |
| **Ergonomia/LER** | Escritórios/teletrabalho | "Descansa os tendões sem largar o trabalho. Alterna mão e rato quando dói." | "Saber mais" |

### 3.3. Regras de copy (imutáveis)

1. **Verbo ativo, benefício concreto:** "Controla...", "Apresenta...", "Descansa...". Nunca
   adjetivos vazios ("incrível", "revolucionário") sem prova ao lado.
2. **1 frase, 1 ideia, 1 CTA.** Sem parágrafos de argumentação nas peças.
3. **Nunca prometer universalidade** ("funciona em qualquer PC") — dizer "otimizado para
   [modelos/matriz] ✅" quando a matriz existir.
4. **Nunca prometer cura/tratamento** — palavra permitida: **acesso**; proibida: **independência
   garantida/resultado terapêutico** (`ESTRATEGIA_GLOBAL.md` §2.2 Ação 3).
5. **Números sempre verdadeiros e datados** (fps, latência, testes) — coerente com a persona
   "pro para venda" do repo.
6. **PT-BR base + EN imediato** (D4): nunca uma peça só em PT quando o mercado de liquidez é EN.

### 3.4. As 4 peças-mestras (criar primeiro, tudo o resto deriva)

| Peça | Formato | Função no funil |
|---|---|---|
| 1 | **Demo hero 10–30 s** ("a webcam já é um rato") | Topo da landing + PR + criadores |
| 2 | **Demo acessibilidade 60 s** (pessoa real a mover o cursor só com a mão) | Cano B + segmento 1 |
| 3 | **Demo mão-livre 30 s** (professor a andar) | Cano A + apresentadores |
| 4 | **Demo modo remoto 30 s** (telemóvel controla o PC) | Diferencial PC↔móvel que ninguém tem |

> **Regra de ouro:** todos os vídeos terminam em CTA acionável (download free / falar com a
> equipa). Uma peça de marketing sem CTA é uma despesa, não um ativo.

---

## 4. O Loop Viral — o produto é o anúncio

A genialidade deste produto é que **o próprio produto gera o conteúdo de marketing**.

### 4.1. O ciclo

```
Utilizador instala Free → webcam ligada → grava o ecrã com a mão a mover o cursor
→ publica "olhem o que fiz" → o watermark "Mãouse — a mão é o novo mouse" publicita
→ novo utilizador instala → (repete)
```

### 4.2. Como alimentar o loop (ações concretas)

| Ação | Detalhe | Custo |
|---|---|---|
| **Gravação em 1 clique** | Botão no Free: "Grava a tua demo (10 s)" → gera clip pronto a partilhar com watermark | Dev (S2) |
| **Campanha "A tua webcam é um rato"** | Hashtag + desafio TikTok/Shorts: substituir rato pela mão por 24 h | €0 |
| **Prémio mensal** | A melhor demo ganha 1 ano Pro | €0 (vitrina) |
| **Sebo para criadores** | 5 criadores recebem o Free completo para gerarem o 1.º vírus, com link de CTA | €300 (S3) |

### 4.3. Regra anti-erro do loop

- **O watermark é obrigatório no Free** (é a impressão publicitária) — mas **não pode
  degradar a demo** (sobrepor demasiado = utilizador não partilha). Watermark discreto no
  canto, corpo da mão sempre visível.
- **Nunca pagar views.** Pagar criadores de verdade, não tráfego. Views compradas matam o
  algoritmo e o credibilidade.

---

## 5. Playbook de Vendas Institucionais (o dinheiro gordo)

> Sequência completa, do primeiro contacto ao contrato anual. Cada etapa tem **saída
> verificável** e **regra de não-negociação**.

### 5.1. Sequência de 6 etapas

| # | Etapa | Ação | Saída verificável | Não-negociável |
|---|---|---|---|---|
| 1 | **Lista** | 10 centros de reabilitação PT/BR/AO + 5 universidades + RH hospitalar | Ficheiro com 15 entradas e contacto nomeado | — |
| 2 | **Descoberta** | Conversa 30 min: *"comprariam acesso por gestos+voz para cumprir EU EAA? Quanto por utente/ano?"* (10–15 conversas obrigatórias) | Notas + resposta WTP registada | NUNCA começar em piloto sem 10–15 descobertas |
| 3 | **Prova técnica** | Piloto técnico 2–4 semanas no **parque real** do cliente (matriz validate) | Relatório de compatibilidade assinado | PILOTO TÉCNICO = GRÁTIS por desenho; PILOTO PAGO é a etapa 4 |
| 4 | **Piloto pago** | 4–8 semanas por **€2.000–5.000** (instalação + formação + relatório compliance) | **Pagamento antecipado integral** na conta | Sem adiantamento = sem piloto |
| 5 | **Contrato anual** | €5.000–50.000/ano: licenças + SLA + relatório + renovação | Assinatura + 1.ª parcela | Sem SLA definido (N1<8h, N2<48h) = sem contrato |
| 6 | **Caso de estudo** | Documento publicável + testemunho "Hospital/centro X" | PDF + permissão de citação | Nunca inventar métricas de impacto |

### 5.2. Os 7 erros fatais nas vendas B2B (e a correção)

| ❌ Erro fatal | ✅ Correção |
|---|---|
| Vender universalidade antes da matriz | Vender "validámos no teu parque antes de prometer" |
| Piloto grátis "só para experimentar" | Piloto **técnico** grátis (2–4 sem.) → piloto **pago** (€2–5k) |
| Confiar em 1–2 oportunidades | Pipeline de ≥10 em paralelo; modelar 50–70% de falhas |
| Pagamento 50/50 | **Pagamento antecipado integral** ou carta de crédito |
| Vender compliance sem auditoria | Vender **roadmap de conformidade + documentação**, com auditoria agendada |
| Prometer "independência/tratamento" | Prometer **capacidade de acesso** + disclaimer clínico |
| Depender do ciclo B2G lento | Iniciar consumer em paralelo (caixa intermédia) |

### 5.3. O pacote "compliance turnkey" (a arma de preço)

| Componente | O que resolve no cliente | Preço implícito |
|---|---|---|
| Software Mãouse (licenças) | Acesso por gestos+voz nos postos | Base |
| Relatório de conformidade de acessibilidade | Obrigação EU EAA/WCAG | €2–5k/ano |
| Formação a terapeutas/professores | Adoção real | €1–2k |
| DPA + política de privacidade | GDPR/LGPD contratual | Incluído |
| SLA de suporte | Continuidade operacional | Incluído |

> O preço premium é justificável porque resolve uma **obrigação legal** cujo custo de não
> cumprir (multa/litígio) é muito maior que o contrato.

---

## 6. Canais por Fase — 90 dias / Y1 / Y2

> Regra transversal: **cada canal tem CTA, métrica e orçamento-teto.** Canal sem os três não
> arranca.

### 6.1. Dia 1–90 (fundação + 1.ª prova)

| Canal | Ação concreta | Métrica | Teto € |
|---|---|---|---|
| **Landing `maouse.app`** | Demo hero + copy acessibilidade + desconto 50% visível + download Free/Pro | Conversão visita→download ≥ 5% | €200 |
| **Vídeos demo** (4 peças-mestras) | PT-BR + EN | Views + CTR para download | €0–200 |
| **PR onda 1 (origem)** | "Startup angolana constrói com IA o rato sem hardware" → tech press PT/BR/AO | 3 menções na imprensa | €0 |
| **Open-core GitHub** | Núcleo gestos/IA publicado | Stars + issues + SEO | €0 |
| **Descobertas institucionais** | 10–15 conversas (5.1) | 15 conversas com WTP registada | €0 |
| **Lista de espera beta** | Formulário na landing | ≥ 200 endereços (p/ lançamento) | €0 |

### 6.2. Y1 (prova + segmento 1)

| Canal | Ação | Métrica-alvo |
|---|---|---|
| **Criadores tech/accessibilidade** | 5 criadores com demo paga/parceria | 1 vírus ≥ 1M views OU ≥ 30k downloads |
| **Shorts TikTok/YouTube/IG** | Clip "a tua webcam já é um rato" | ≥ 100k views/crescimento semana |
| **3 terapeutas ocupacionais** | Como "prescribes" (indicam o Mãouse) | 3 parceiros com comissão |
| **Conferências de reabilitação** (eAccessibility, TEAMs) | Presença/vídeos | 10 contactos institucionais por evento |
| **SEO + conteúdo** | Guias "como usar teclado sem rato", "LER no escritório" | 5 palavras-chave no top 10 |

### 6.3. Y2 (escala)

| Canal | Ação | Métrica-alvo |
|---|---|---|
| **Lojas** | Play Store + Microsoft Store + Steam | 30k downloads/mês, conversão 2% |
| **Programa de afiliados** | Comissão por venda Pro | 10% das vendas via afiliados |
| **Caso de estudo âncora** | 1 instituição publicada | PDF + 3 referências |
| **Licitações públicas** | UE compliance tenders | 1 win / ano |

> **Anti-erro de canal (escala prematura):** nenhum canal novo abre antes de o anterior ter
> 2 semanas de métricas favoráveis — exceto os obrigatórios por data (EN, lojas, PR).

---

## 7. Precificação como Arma de Marketing

> O preço **é** marketing. As decisões D1/D3/D7 tornam-se alavancas de conversão, não só
> financeiras.

### 7.1. A arquitetura mental do preço

| Tier | Preço | Papel psicológico |
|---|---|---|
| **Free** | €0 + watermark | "Experimentar" = sem atrito; o watermark anuncia |
| **Pro Lifetime** | €39,90 (âncora emocional "para sempre") | Compra por valor, caixa imediata |
| **Pro Sub** | €4,99/mês · €3,49/mês anual | Decisão pequena, receita recorrente |
| **Familiar** | €59,90 (3 dispositivos) | Upsell e viralização C2C |
| **Desconto acessibilidade** | −50% com comprovativo | PR "acessível para quem precisa" + bom motivo |

### 7.2. As 3 manobras de preço

1. **Âncora contra hardware:** "UltraLeap custa €100+. Isto é €39,90 e usa a webcam que já
   tens." — **Sempre** que houver espaço para mostrar alternativa física.
2. **O "combo PC+móvel" (€49,90 lifetime):** aumenta ticket médio e cria ecossistema que
   ninguém tem (modo remoto PC↔móvel).
3. **Refund raro = conversão protegida:** a política D7 ("Free tier = experimentação") está na
   config de reembolsos Paddle, para o "entusiasta que devolve" não corroer a receita.

### 7.3. Erros de preço a evitar (a partir de ANTIPADROES)

- ❌ Free demasiado bom (sem watermark, com snap/voz) → canibaliza Pro.
- ❌ Preço zero ancorado (grátis o desconto) → desvaloriza a categoria.
- ❌ Cobrar em moeda frágil → EUR/USD sempre (D5).
- ❌ Esquecer ~3% + €0,30 + VAT UE no custo das vendas (L6).

---

## 8. Radar de Métricas — o painel semanal

> O coração da "infalibilidade". Toda a sexta-feira, 20 min: ler, comparar, **acionar gatilhos**.
> Nenhuma decisão de marketing é tomada fora do painel.

### 8.1. As 8 métricas de vida (uma por alavanca)

| # | Métrica | Alvo | Frequência de leitura |
|---|---|---|---|
| 1 | Downloads Free | 30k/mês no Y2 | Semanal |
| 2 | Conversão Free→pago | 2–4% | Semanal |
| 3 | CAC | < €8 orgânico · < €30 pago | Mensal |
| 4 | LTV ÷ CAC | > 3 | Mensal |
| 5 | Churn (subs mobile) | < 3%/mês | Mensal |
| 6 | Pipeline institucional (€ potencial em aberto) | ≥ €50k em 3 meses | Semanal |
| 7 | Contrato institucional médio | €15–30k/ano | Trimestral |
| 8 | NPS (segmento acessibilidade) | > 60 | Trimestral |

### 8.2. Métricas de produto que alimentam marketing (do `MODELO_DE_NEGOCIO` §21.2)

Tempo ao "primeiro wow" < 3 min · FPS ≥ 25 · latência gesto→ação < 80 ms · crash-free > 99,5%.

> Sem estas três últimas verdadeiras, o marketing só acelera um produto imaturo. **Verificar
> antes de escalar.**

### 8.3. Formato do painel (uma tabela que se preenche toda a semana)

```
| Métrica | Alvo | Esta semana | Δ vs alvo | Gatilho acionado? |
```

> Se o valor "Δ vs alvo" falha em qualquer linha durante 2 semanas seguidas → passa ao §9.

---

## 9. Gatilhos de Decisão — Kill / Pivot / Scale

> Pré-decisões escritas **antes** do problema existir. Evita o erro emocional de prolongar o
> que falha ou abortar cedo demais o que cresce.

| # | Sinal (2 semanas seguidas fora do alvo) | Decisão pré-programada |
|---|---|---|
| 1 | Conversão Free→pago < 1% | **Pivot de copy/pricing:** testar ângulos da §3.2 em A/B (1 semana, 2 variantes) antes de tocar no produto |
| 2 | CAC > €30 em qualquer canal pago | **Kill do canal:** parar ads na hora; voltar a 100% orgânico/criadores |
| 3 | Demo/PR sem tração (< 50k views, 0 menções) | **Pivot de ângulo:** trocar para acessibilidade/humano (ângulo 1 da §3.2), não investir mais em viral genérico |
| 4 | 0 pilotos pagos aos 90 dias | **Pivot institucional:** rever oferta do pacote, baixar preço do piloto para €1,5k, alargar lista a 25 centros + 2 países; revalidar procura com 10 novas conversas |
| 5 | Churn subs > 5%/mês | **Pivot de produto:** investigar reembolsos/tickets (root cause) antes de qualquer aquisição nova |
| 6 | NPS acessibilidade < 40 | **Pause institucional:** parar novos contratos até resolver; é o segmento que não se arrisca |
| 7 | Replicação chegou à loja (clonador) | **Scale PR + velocidade:** anunciar 1 caso de estudo + reforçar marca + EN (nunca baixar preço por medo) |
| 8 | Procura institucional não confirmada (descobertas < WTP) | **Pivot de tese (ferimento €7k):** rebaixar institucional a prova e acelerar consumer + OEM como caixa primária |

> **Regra do gatilho:** decidir com 2 semanas de dados, exceto gatilhos de segurança (2, 6)
> que são imediatos. Indecisão > decisão errada.

---

## 10. Checklists Anti-Erro — pré-lançamento por canal

> Nada se publica sem passar a checklist do seu canal. Feito em `AGENTS.md` da equipa para
> não depender de memória.

### 10.1. Checklist universal (qualquer peça)

- [ ] Tem CTA único e acionável no fim
- [ ] PT-BR e EN (ou deliberadamente só 1 língua decidida)
- [ ] Sem promessa de universalidade de hardware
- [ ] Sem promessa médica/terapêutica (palavra "acesso", não "cura/independência garantida")
- [ ] Números verdadeiros e datados ou nenhum número
- [ ] Link/conteúdo aberto em mobile (maioria do tráfego)

### 10.2. Checklist landing page

- [ ] Demo hero ≤ 30 s no topo, auto-play muted
- [ ] Posicionamento acessibilidade primeiro (segmento nº1)
- [ ] Desconto 50% visível + política de reembolso clara (D3/D7)
- [ ] Download Free + upgrade Pro em 2 cliques
- [ ] Matriz de dispositivos validada visível (logo que existir)
- [ ] Privacy: "a câmara e a voz nunca saem do teu dispositivo" (D6)

### 10.3. Checklist institucional (antes de cada chamada de venda)

- [ ] Matriz de dispositivos do parque do cliente disponível
- [ ] Pacote compliance dentro do que é audito (roadmap, não promessa de relatório)
- [ ] SLA definido (N1 < 8h · N2 < 48h)
- [ ] DPA (ART. 28 GDPR) pronto para enviar
- [ ] Disclaimer clínico e cláusula "ferramenta, não tratamento" no contrato
- [ ] Seguro RC ativo
- [ ] Proposta com pagamento antecipado integral (etapa 4 §5.1)

### 10.4. Checklist de lançamento público (dia 1)

- [ ] Desktop vendável: licença + gate + `.exe` assinado + instalador (bloqueadores 1–3)
- [ ] Mobile na Play, posicionado acessibilidade, com ações nativas (bloqueadores 4–5)
- [ ] Paddle ativo com política D7 configurada
- [ ] Marca + domínios registados (moat nº1)
- [ ] Entidade UE em ordem (VAT) — p/ Paddle e B2B (D5)
- [ ] Landing + 4 vídeos + open-core GitHub no ar
- [ ] 15 descobertas institucionais feitas com WTP registada

---

## 11. Orçamento e Alocação

> Regra de ouro: **teto por teste antes de gastar** — decide-se o montante máximo de cada
> teste, depois avalia-se com a métrica do painel. Gastar "para ver" é o único erro
> financeiro irreversível neste modelo.

### 11.1. Dias 1–90 (dentro do total de €1.900–3.700 do plano)

| Rubrica | Teto | Decisão se falhar |
|---|---|---|
| Domínios + marca | €400–650 | Mandatório; sem gatilho |
| Landing + 4 vídeos | €200–500 (DIY/IA) | Refazer copy com §3.2 |
| 5 criadores (S3) | €300 | Parar criadores até Y2 se < 1M views |
| Conferências/deslocações | €200 | Ver §6.2 |
| Ferramentas (Paddle, EAS, CI) | €100–300 | — |

### 11.2. Regra de alocação Y1 (quando houver receita)

**Fórmula: reinvestir ≤ 30% da receita mensal em aquisição, e só no canal com melhor CAC do mês.**
Os restantes 70% mantêm o custo fixo e protegem o break-even (mês 14–18).

---

## 12. Contingências — o que fazer se X falhar

> Respostas pré-escritas, curtas, acionáveis. Serve também de "plano B antes da crise".

| Se... | Então... (nas primeiras 48h) |
|---|---|
| SmartScreen/AV bloquear o `.exe` | 1. Re-verificar assinatura EV; 2. submeter ao Microsoft; 3. comunicar "instalação via Microsoft Store" alternativo |
| Varredura da Apple/Play rejeita listing | Preparar documentação de acessibilidade + vídeo de conformidade; abrir recurso formal; fallback: lojas alternativas + APK direto |
| Falha numa webcam comum (fora da matriz) | Adicionar à matriz ❌/⚠️; atualizar copy; NUNCA prometer universalidade; canal institucional só com parque validado |
| Clonador publica antes | Accelerar caso de estudo + PR onda 4 + marca; manter preço (nunca baixar por reação) |
| Sem tração nos primeiros 30 dias | Voltar ao 3.2 interplay de ângulos (testar 2); rever se posicionamento está em acessibilidade; nunca "esperar mais um mês" sem ação |
| € em caixa baixo antes do break-even | Pausar não-obrigatórios (criadores, conferências); priorizar institucional + subsídios (Startup Portugal, Compete, EIT); manter custo fixo ≤ €2k/mês |

---

## 13. OKRs de Marketing — 90 dias

> Alinhados ao `PLANO_DE_EXECUCAO_90_DIAS.md`. Feitos = verificáveis, nunca intenção.

### S1 (dias 1–30) — Fundação
- **O1.1** Landing + 4 vídeos + open-core publicados (PT-BR + EN).
- **O1.2** Marca + domínios registados; entidade UE em constituição.
- **O1.3** 15 descobertas institucionais com WTP registada (veredito: tese confirmada/não).
- **O1.4** Lista de espera beta ≥ 200 endereços.

### S2 (dias 31–60) — Produto vendável + 1.º piloto
- **O2.1** Desktop vendável (licença + gate + assinatura) com Paddle ativo e D7 configurado.
- **O2.2** Mobile na Play (ações nativas + IAP + listing acessibilidade) ou submissão feita.
- **O2.3** 1 piloto institucional **pago** assinado (pagamento antecipado na conta).
- **O2.4** Matriz de dispositivos com ≥ 5 dispositivos classificado (✅/🟡/❌/⚠️).

### S3 (dias 61–90) — Fúnel a converter
- **O3.1** 30k downloads/mês (Y1) ou ≥ 10x crescimento semanal vs baseline.
- **O3.2** Conversão Free→pago ≥ 1,5% em qualquer segmento.
- **O3.3** 1 vírus de criador ≥ 100k views OU 2 menções de imprensa tech PT/BR/AO.
- **O3.4** Painel de métricas a reportar semanalmente com 0 gatilhos críticos abertos.

---

## Nota de honestidade (porque é que falhar está no modelo)

Este documento **assume que algo vai falhar** e divide a resposta em: deteção ≤ 7 dias +
decisão pré-escrita + verificação da decisão. É essa arquitetura — não um horóscopo — que
torna o marketing "infalível": **não porque nunca erra, mas porque nenhum erro sobrevive
mais de uma semana sem correção**.

> *"A mão é o novo mouse." — E o marketing é o sistema que nunca esquece de verificar as mãos.*

---

*Modelo de marketing e vendas — Luar Studio Angola · 2026. Complementa MODELO_DE_NEGOCIO.md, ESTRATEGIA_GLOBAL.md, DECISOES.md, ANTIPADROES_E_RISCOS.md e PLANO_DE_EXECUCAO_90_DIAS.md.*