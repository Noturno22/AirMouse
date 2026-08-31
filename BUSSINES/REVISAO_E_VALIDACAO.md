# Revisão e Validação do Modelo de Negócio — Mãouse

> Ficheiro de trabalho que valida o `MODELO_DE_NEGOCIO.md`, corrige inconsistências
> e sinaliza as decisões que ainda faltam tomar. **Data:** 2026-08-31.
> Autor: Luar Studio Angola · Estado: **PARCIALMENTE VALIDADO — 4 correções e 6 decisões em aberto.**

---

## 0. Veredito rápido

| Dimensão | Nota | Comentário curto |
|---|---|---|
| Tese estratégica | ✅ **Sólida** | Acessibilidade-first + open-core + moat não-código é coerente e defensável |
| Finanças (cenários) | 🟡 **Coerente** | Somas e margens batem; algumas premissas precisam de ser citadas |
| Break-even | ⚠️ **Erro de aritmética** | O número de "60 subscrições" não fecha com os custos fixos |
| Precificação | ✅ **Razoável** | Âncoras por valor corretas; falta fixar o plano de comissões/locale |
| Riscos | ✅ **Completos** | O risco nº1 (replicação) é bem tratado na sec. 10 |
| Lacunas | ⚠️ **Existem** | Canais C2C, suporte SLAs, DPA, roadmap legal de dados |

**Conclusão:** o modelo está **aprovável** com as 4 correções abaixo. Não bloqueia o arranque.
Recomendo corrigir o ficheiro de origem e fechar as 6 decisões antes da primeira venda paga.

---

## 1. Verificação aritmética dos cenários (13.1 a 13.4)

### 1.1. Cenário Base — somas internas

| Ano | Consumer | Institucional | OEM | Soma | Receita total no doc | ✅? |
|---|---|---|---|---|---|---|
| 1 | 33k | 5k | 7k | **45k** | €45k | ✅ |
| 2 | 115k | 25k | 10k | **150k** | €150k | ✅ |
| 3 | 270k | 90k | 60k | **420k** | €420k | ✅ |
| 4 | 560k | 260k | 230k | **1.050k** | €1.050k | ✅ |
| 5 | 1.100k | 600k | 700k | **2.400k** | €2.400k | ✅ |

Todas as somas fecham. Margens EBITDA conferidas: 7/45=16%, 80/150=53%, 280/420=67%,
750/1050=71%, 1840/2400=77% — **todas corretas.**

### 1.2. Conversão free→pago (consistente com os 1,5–4%)

| Ano | Free (cum.) | Pagantes | Conversão | ✅? |
|---|---|---|---|---|
| 1 | 45.000 | 1.100 | 2,4% | ✅ |
| 2 | 180.000 | 4.200 | 2,3% | ✅ |
| 3 | 550.000 | 12.000 | 2,2% | ✅ |
| 4 | 1.300.000 | 28.000 | 2,2% | ✅ |
| 5 | 2.600.000 | 62.000 | 2,4% | ✅ |

Encaixa na banda assumida. **Nota:** 2,2–2,4% é o fundo da banda; assumir ~2,3% como
"execução boa" é conservador — realça a importância da conversão institucional.

### 1.3. Receita média por pagante consumer ~€30/ano

- Y1: 33k / 1100 = **€30/ano** ✅
- Y5: 1100k / 62000 = **€17,7/ano** ⚠️

**Cuidado:** no mix lifetime (€39,90 uma vez) + subscrição (€59,88/ano) + family (€59,90/3),
a média aritmética é ~€35–45/ano no início. O valor €30/ano é defensável para Y1, mas cai para
~€18/ano no Y5 **só se** o crescimento free→pago for dominado por mobile low-price (€19,90/ano,
regional Kz/R$). Como mobile já é 25% do mix, **isto é coerente, mas deve ser explícito.**

### 1.4. Break-even — ⚠️ ERRO DE ARITMÉTICA (a corrigir)

O texto (sec. 14) diz:

> *"custos fixos ≈ €2k/mês → é preciso ≈ 60 subscrições Pro/ano-equivalente (€4,99)"*

**Cálculo correto:**
- Custos fixos ≈ €2.000/mês = **€24.000/ano**.
- Uma subscrição Pro de €4,99/mês gera **€59,88/ano**.
- €24.000 ÷ €59,88 = **~401 subscrições** (não 60).
- Se forem **licenças lifetime** (€39,90) → €24.000 ÷ 39,90 = **~602 licenças** (uma vez, e não recorrente).

**Correção proposta (substituir as duas frases):**

> "Ponto de break-even: com custos fixos ≈ €2.000/mês (≈ €24.000/ano), o equilíbrio depende do mix:
> ≈ **400 subscrições Pro** ativas (€4,99/mês) **OU** ≈ **600 licenças lifetime** vendidas (€39,90)
> **OU** **1–2 contratos institucionais pequenos** (€5.000–24.000/ano cada). A via com menos risco é
> o contrato institucional — alcançável com um único centro de reabilitação."

> ⚠️ Nota: "break-even em receita recorrente" só se aplica à via subscrição/institucional.
> A via lifetime é receita **uma vez** — não cobre os €24k/ano do ano seguinte se parar de vender.

### 1.5. Custos Y1: €38k/ano no cenário vs €1.980/mês na sec. 12

- Sec. 12: fixo médio ~€1.980/mês → **€23.760/ano**.
- Cenário Y1: custos **€38.000/ano**.
- Diferença: €14.240/ano (~€1.190/mês) — **não explicada.**
- **Recomendação:** adicionar ao cenário a linha "marketing/custos de lançamento fase 0 (domínios,
  registo de marca, landing, primeiros vídeos)" para fechar a diferença. Sem isso, o custo fixo real
  do Y1 é ~€3.200/mês, não €2k.

---

## 2. Coerência estratégica (pontos fortes que confirmar)

1. **Ordem de ataque** (sec. 6) — acessibilidade FIRST é a decisão certa: maior WTP por utente,
   compra institucional, financiamento externo, menos churn. Confirmado.
2. **"Amoat não é o código"** (sec. 10) — honesto e correto. Distribuição/marca/provas/contratos/dados
   reais são a verdadeira barreira. Um clonador de fim de semana **não** ganha uma licitação B2G.
3. **iOS = modo remoto** (sec. 17.1, 18.2) — a decisão de não prometer injeção de toques iOS é
   realista e protege a credibilidade. Confirmado.
4. **Open-core** — gera adoção e provas; mantém snap/voz/duas mãos/institucional fora. Coerente.
5. **Free = sem snap/voz/duas mãos/mobile avançado** — bom para não canibalizar a venda. Confirmado
   (mitiga o risco de "grátis mata venda" da sec. 17.3).

---

## 3. Lacunas identificadas (não estão no modelo)

| # | Lacuna | Impacto | Ação sugerida |
|---|---|---|---|
| L1 | **Português de Portugal vs Brasil** — a voz/TTS/Whisper/NLU está em pt_BR (Piper pt_BR); PT-pt (Portugal) e AO (Angola) têm vocabulário/vozes diferentes | Médio — acessibilidade em PT é público-alvo nº1 | Definir suporte multi-dialeto (pt_BR, pt_PT, pt_AO) como roadmap de localização; não prometer "PT" genérico |
| L2 | **Suporte SLA/N1/N2** — o Business promete "SUPPORT SLA" mas não há definição de tempos | Médio — contratos B2B exigem SLA escrito | Fixar: N1 < 8h úteis, N2 < 48h, disponibilidade do atendimento 5×8 |
| L3 | **DPA / regime de dados institucional** — GDPR/LGPD exigem contrato de processamento | Alto para vendas B2G/B2B | Modelo de DPA (ART. 28 GDPR) pronto; opt-in de telemetria explícito |
| L4 | **Prova clínica hipotética** — o plano depende de "provas clínicas" para abrir B2B | Alto no Y3 | Preparar protocolo de estudo com universidade desde Y1 (não esperar Y3) |
| L5 | **Canal de vendas C2C/familiar** — "licença familiar" não tem fluxo de distribuição | Baixo | Relegar para fase consumer; não bloquear |
| L6 | **Custos de processamento de pagamento** (Stripe/Paddle) e IVA/VAT UE | Médio | Incluir taxa ~3% + VAT no custo variável e nas margens |
| L7 | **Roadmap de compliance de loja** (Play Accessibility policy vídeo, Apple review) não tem datas | Alto | Já está no plano; tornar datas explícitas no EXECUCAO_90_DIAS |

---

## 4. Riscos — reavaliação e prioridade real

| Risco | Prob. | Impacto | Prioridade real |
|---|---|---|---|
| Replicação por "dev+IA" | Alta | Alto | 🔴 **#1** (bem mitigado na sec. 10 — agir já: marca, domínios, landing, open-core) |
| Google Play policy (Accessibility API) | Média | Alto | 🔴 **#2** (posicionamento como acessibilidade é crítico desde o build 1) |
| Antivírus/code-signing do `.exe` | Alta | Alto | 🔴 **#3** (EV signing e Microsoft Store — sem isto as vendas desktop morrem) |
| Fadiga de utilizador | Média | Médio | 🟠 #4 |
| Latência em webcams fracas | Alta | Médio | 🟠 #5 (já robusto — CLAHE, autotune) |
| Flutuação cambial | Média | Baixo | 🟢 #6 |
| Chargeback IAP | Baixa | Baixo | 🟢 #7 |

**Leitura:** os três primeiros riscos são **bloqueadores de receita**, não de desenvolvimento.
Têm prioridade sobre qualquer feature nova.

---

## 5. Decisões em aberto (para fechar antes da 1.ª venda)

> Sugestão: responder diretamente no `MODELO_DE_NEGOCIO.md` ou num `DECISOES.md`.

| # | Decisão | Opções | Recomendação |
|---|---|---|---|
| D1 | **Modelo da licença Pro desktop** | lifetime €39,90 · sub €4,99/mês · sub €3,49/mês anual | Oferecer **ambos** (lifetime + sub) — âncora no lifetime, recorrência na sub |
| D2 | **Gateway de pagamento desktop** | Stripe · Paddle (Merchant of Record p/ UE) | **Paddle** (trata VAT UE + Wise local) — reduz carga de contabilidade |
| D3 | **Política de desconto acessibilidade 50%** | Por comprovativo · automática por categoria | Por **comprovativo** (evita fraude e âncora zero) |
| D4 | **Língua base de lançamento** | PT-BR · PT-PT · EN | Base PT-BR (maior mercado + voz Piper pronta); EN como 2.ª logo |
| D5 | **Estrutura societária definitiva** | Angola(Une) + PT (Soc. Unipessoal) | Confirmar com contabilista; 1 entidade leve na UE para VAT/subsídios |
| D6 | **Dados de telemetria** | Opt-in anónimo por defeito OFF | **OFF por defeito**, opt-in claro — reforça a venda "privacidade" |

---

## 6. O que está pronto para executar (não bloqueia)

- Modelo financeiro 3 cenários com somas corretas (após correção 13.1.4).
- Ordem de ataque e personas definidas.
- Identidade visual (`IDENTIDADE_VISUAL.md`) e precificação esboçada.
- Risco nº1 com mitigação clara.

(O plano semanal em `PLANO_DE_EXECUCAO_90_DIAS.md` começa com os bloqueadores de receita:
marca+domínios, landing+fúnel, code-signing, e posicionamento de acessibilidade.)

---

## 7. Ações a tomar neste ficheiro de origem

1. Corrigir a aritmética do break-even (sec. 14) — ver §1.4 deste documento.
2. Explicar a diferença de custos do Y1 (sec. 13 vs sec. 12) — ver §1.5.
3. Adicionar as lacunas L1–L7 como linhas no plano de risco/roadmap.
4. Fechar D1–D6 e registá-las (criar `BUSSINES/DECISOES.md`).
5. Marcar este documento como "validado" após as correções.

---

*Documento de validação — Luar Studio Angola · 2026. Complementa MODELO_DE_NEGOCIO.md sem o substituir.*
