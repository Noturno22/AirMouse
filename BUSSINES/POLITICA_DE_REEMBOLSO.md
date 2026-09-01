# Política de Reembolso — Mãouse (AirMouse) [pronto para checkout/landing]

> Texto oficial, **receita-first**, contra o "entusiasta só a experimentar". Deve ser colado
> (traduzido) no checkout **Paddle (D2)**, na **landing page**, nos **termos** e no **mobile
> IAP**. Baseado em `ANTIPADROES_E_RISCOS.md` §4.5.
> **Data:** 2026-09-01 · Autor: Luar Studio Angola · Estado: **APROVADO para implementação.**

---

## 0. Regra-mestra

> **"Experimentar" é grátis (Free tier). Pagar é comprometer. Reembolso é exceção, não regra."**

| Situação | Ação |
|---|---|
| Quer experimentar sem risco | Usa a **Free tier** (grátis, gated, com watermark) |
| Comprou Pro e está em hardware na **matriz ✅ Validado** | Sem reembolso por "não gostar" |
| Falha técnica **real** em hardware Validado | **Reembolso** (raro por desenho) |
| Instituição | **Piloto técnico** antes do contrato; refund por falha de SLA no contrato |
| IAP mobile | Regras da loja; nunca promovemos refund |

---

## 1. Texto curto (landing / botão / checkout)

> **Política de devolução (resumo):**
> Mãouse é distribuído como **subscrição com trial embutido na Free tier** ou **licença
> vitalícia**.
> - **Experimente grátis primeiro** — a versão Free mostra todas as funções principais sem
>   custo, para não precisar de "comprar para experimentar".
> - **Licenças pagas (Pro):** não reembolsáveis por *mudança de opinião*.
> - **Exceção:** reembolso total nos primeiros **14 dias** se o software **não funcionar** num
>   dispositivo constante da nossa **lista de compatibilidade validada**.
> - **Garantia de compatibilidade:** por defeito, Mãouse **funciona nos dispositivos listados**
>   como compatíveis. Fora dessa lista, a compra é "à responsabilidade do utilizador".

---

## 2. Texto completo (termos / checkout expandido)

**2.1 Free tier = o "trial" oficial.** A Free tier inclui o essencial (mover o cursor, clicar,
gestos básicos) com marca de água, sem snap, voz, duas mãos, IA ou autotune. **Não é necessário
comprar para decidir se funciona** no teu computador. Se a Free tier funciona, a compra do Pro é
uma decisão informada do utilizador.

**2.2 Reembolso por falha real (garantia de compatibilidade).** Garantimos que Mãouse funciona
nos dispositivos listados em **MATRIZ_DE_DISPOSITIVOS.md** (categoria "✅ Validado"). Se, num
dispositivo **Validado**, o software não funcionar como descrito nas primeiras **14 dias**,
reembolsamos **100%** mediante contacto de suporte com prova do hardware (`dxdiag`/especificações).

**2.3 Sem reembolso por "não gostar" ou hardware fora da lista.** Compras em dispositivos
fora da lista Validado são **"à responsabilidade do utilizador"** — a Free tier existia para
verificar antes de pagar. Não reembolsamos *mudança de opinião*, *uso indevido* ou *hardware
não suportado*.

**2.4 Institucional/B2B.** Cada contrato define devoluções por **falha de disponibilidade/SLA**,
não por preferência. O **piloto técnico** (2–4 semanas) antecede qualquer contrato anual para
validar o parque antes de compromisso.

**2.5 IAP mobile.** Aplicam-se as regras de reembolso da Google Play/App Store. Não oferecemos
canal próprio de devolução para IAP; encaminhamos para a plataforma.

---

## 3. Como implementar no Paddle (checkout) e na loja

| Onde | Ação |
|---|---|
| **Paddle checkout** | Definir a política de devolução **não reembolsável por opinião**; para a exceção de 14 dias por falha real, **processar reembolso manualmente** (não automático) após verificação de hardware Validado. |
| **Landing page** | Colocar o §1 (resumo) junto ao botão de compra; link para esta política completa. |
| **Termos PT/BR/EN** | Colar o §2 nas cláusulas de pagamento/reembolso. |
| **Formulário de pedido de refund** | Exigir `dxdiag`/especificações + confirmação de hardware na manhã de Validado → só assim se processa. |
| **Support/DPA** | SLA N1/N2 + registo de pedidos de refund e teste de matriz (L2/L3). |

---

## 4. Antecipação de objeções

| Objeção | Resposta |
|---|---|
| "Não posso experimentar sem pagar?" | **Pode** — a Free tier é grátis e mostra as funções principais. |
| "Comprei e o meu PC não está na lista." | A adjudicação foi à vontade de compra — a lista Validado está pública antes da compra. |
| "Não funcionou no meu dispositivo Validado." | Por defeito **reembolsamos** em 14 dias (garantia de compatibilidade). |
| "Isto é má política, sem consumer protection." | É a mesma de subscrições/ferramentas de dev: o *trial* antecede a compra, o que é **mais** consumer-friendly do que trial-pago-as-devolver. |

---

*Política operacional — Luar Studio Angola · 2026. Pronto a colar em Paddle, landing, termos PT/BR/EN e mobile IAP. Base: ANTIPADROES_E_RISCOS.md §4.5.*
