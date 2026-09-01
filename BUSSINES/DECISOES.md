# Decisões de Negócio — Mãouse (AirMouse)

> Registo oficial das decisões tomadas para fechar as 6 decisões em aberto (D1–D6)
> sinalizadas em `REVISAO_E_VALIDACAO.md`. **Data:** 2026-09-01.
> Autor: Luar Studio Angola · Estado: **FECHADO — pronto para executar.**

---

## D1 — Modelo da licença Pro (desktop)

**Decisão:** Oferecer **dois modelos em simultâneo — Lifetime e Subscrição.**

| Modelo | Preço | Papel estratégico |
|---|---|---|
| **Pro Lifetime** | €39,90 (uma vez) | Âncora de valor; compra emocional "para sempre"; receita imediata em caixa |
| **Pro Subscrição** | €4,99/mês · €3,49/mês (anual) | Receita recorrente previsível; múltiplo de empresa atraente |
| **Licença familiar** | €59,90 (3 dispositivos) | Upsell por agregado; acelera viralização C2C |

**Racional:** o lifetime financia o arranque em caixa; a subscrição constrói o LTV e a
avaliação da empresa. Não canibalizar: o lifetime é posicionado como "unidade", a sub como
"extensível a 3 dispositivos + suporte prioritário".

**Implicação financeira:** a média ~€30/ano do cenário base pressupõe ~65% a escolher
subscrição e ~35% lifetime ao longo do tempo — coerente com o mix mobile-first do Y5.

---

## D2 — Gateway de pagamento (desktop)

**Decisão:** **Paddle (Merchant of Record)** como gateway primário do desktop.

- Paddle trata **IVA/VAT da UE** e **MRR + moedas locais** — reduz drasticamente a carga
  de contabilidade (Wise integrado, invoices locais).
- Alternativa Stripe fica como fallback/recuperação se Paddle não aprovar o tipo de produto.
- Cobrança de lojas (Play/App Store) fica sempre via IAP nativo (regra imutável das lojas).

**Porquê agora:** a decisão de gateway afeta a estrutura societária (ver D5) e o custo
variável (taxa ~3% + VAT). Fechar D2 antes de codificar o checkout.

**Custo de processamento a modelar:** ~3% + €0,30 por transação + VAT UE (Paddle gere).
Adicionar ao modelo como custo variável (lacuna L6).

---

## D3 — Política de desconto de acessibilidade (50%)

**Decisão:** Desconto de 50% **mediante comprovativo**, nunca automático por categoria.

- Comprovativo aceite: atestado médico, cartão de deficiência, documento de unidade de
  saúde, ou certificado de associação de acessibilidade.
- Fluxo: pedido por formulário → verificação manual/refeita por humano → cupão gerado.
- **Nunca ancorar preço zero:** o desconto é 50% (não grátis) para não desvalorizar a
  categoria.

**Fonte de boa PR:** publicar a política de forma visível ("Acessibilidade a 50% — acessível
para quem precisa"). Gera confiança e cobertura mediática no segmento nº1.

---

## D4 — Língua base de lançamento

**Decisão:** Base **PT-BR** (português do Brasil), com **EN como 2.ª língua** logo no arranque.

| Língua | Prioridade | Porquê |
|---|---|---|
| **PT-BR** | Base | Maior mercado lusófono; voz Piper **pt_BR já pronta** (zero custo de integração) |
| **EN** | 2.ª imediata | Necessária para vendas B2B/OEM/institucionais internacionais e para o open-core |
| PT-PT | Curto prazo | Portugal é alvo da EU EAA; voz/Whisper/NLU pt_PT ainda a construir |
| PT-AO (Angola) | Médio prazo | Casa do fundador; diferenciação e narrativa "local p/ o mundo" |
| ES/FR/outras | Y4+ | Internacionalização (roadmap) |

**Nota (lacuna L1):** **não prometer "português genérico"** — o TTS/Whisper/NLU hoje é pt_BR.
Portugal e Angola usam vocabulário/vozes diferentes. O roadmap de localização deve listar
pt_BR → pt_PT → pt_AO separadamente.

---

## D5 — Estrutura societária definitiva

**Decisão:** **Holding dupla — Angola (raiz) + entidade leve na UE (Portugal).**

| Entidade | Papel | Detalhe |
|---|---|---|
| **Luar Studio (Angola)** | Raiz/propriedade intelectual | Marca, domínio, contratos de licença de IP |
| **Entidade UE (PT) — Sociedade Unipessoal Lda** | Operação/vendas UE | Para cobrar subsídios EU/EAA, cartão de VAT, receber pagamentos Paddle, loja |

**Próximos passos (a executar no plano 90 dias):**
1. Consultar contabilista PT para forma exata (Soc. Unipessoal vs Unipessoal por quotas) e
   registo de VAT.
2. Documento de licença de IP Angola → PT (cessão/licença de uso) para separar riscos.
3. Contas multi-moeda (EUR principal; USD/SOF iniciais conforme necessário).

**Implicação:** sem entidade UE, Paddle/lojas/subsídios EU ficam bloqueados. Esta é uma
decisão **bloqueadora** de vendas B2G/B2B — prioridade alta no plano.

---

## D6 — Dados de telemetria

**Decisão:** **Opt-in, ANÓNIMA, OFF por defeito.**

- Telemetria **desligada por defeito**; ativação explícita pelo utilizador no onboarding.
- Só dados anónimos de desempenho/precisão (fps, latência, gestos usados) — **nunca** frames
  de câmara nem áudio; **nunca** conteúdo.
- Reforça o posicionamento premium "privacidade total — a câmara e a voz nunca saem do
  dispositivo".
- Compatível com GDPR/LGPD; opt-in claro documentado na política de privacidade.

**Implicação:** o corpus de dados reais de afinação (moat `e` da sec. 10) é construído
**só** com quem opta in. Ajustar as métricas de produto: não assumir dados de 100% dos
utilizadores; assumir uma fração opt-in.

---

## D7 — Política de reembolso (receita-first)

**Decisão:** **Sem reembolso em aberto.** O "experimentar" é a **Free tier**, não a devolução.
Reembolso **apenas** em falha técnica real em hardware **Validado** (matriz ✅) ou falha de SLA
institucional. **"Não gostar" → não devolve** (o Free tier cobria a experimentação).

- Texto oficial pronto a colar em Paddle/landing/termos/mobile: `POLITICA_DE_REEMBOLSO.md`.
- Garantia de compatibilidade: reembolso em 14 dias **só** em dispositivo da lista Validado —
  o que torna o reembolso legítimo **raro por desenho** (a matriz previne o abuso).
- Protege a receita do "entusiasta só a experimentar" que compra e devolve.

---

## Resumo executivo das decisões

| Decisão | Resposta | Bloqueador de venda? |
|---|---|---|
| D1 Licença Pro | Lifetime + Subscrição | Não |
| D2 Gateway desktop | Paddle (Merchant of Record) | Sim (código) |
| D3 Desconto acessibilidade | 50% mediante comprovativo | Não |
| D4 Língua base | PT-BR + EN imediato | Sim (localização) |
| D5 Sociedade | Angola + PT (2 entidades) | **Sim (B2G/B2B)** |
| D6 Telemetria | Opt-in OFF por defeito | Não |
| D7 Reembolso | Sem refund em aberto; só falha real em Validado/SLA | Não (texto pronto) |

---

*Registo de decisões — Luar Studio Angola · 2026. Complementa MODELO_DE_NEGOCIO.md.*
