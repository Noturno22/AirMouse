# Custos de Lançamento — Mãouse (AirMouse)

> Todos os valores aproximados e em USD/EUR, 2026. Verificar sempre o preço final no
> site oficial/vendedor no momento da compra. Este documento cobre os custos de
> **arranque comercial** (assinatura digital, domínio, infraestrutura, loja).

---

## 1. Assinatura Digital (Code-Signing) — o mais importante

Sem assinatura, o Windows mostra **"Publisher desconhecido" / SmartScreen / AV a bloquear** —
o que impede a venda. É o primeiro grande custo.

> **Podes comprar estando em Angola**: os fornecedores abaixo emitem para qualquer país
> desde que passes a validação de identidade. Só países sob sanções (Rússia, Bielorrússia,
> Coreia do Norte) estão excluídos. Angola não está nessa lista.

### Opções (para app de desktop normal, tu só precisas de OV ou Individual)

| Fornecedor | Tipo | Preço/ano | Requer empresa? | Chave |
|---|---|---|---|---|
| **SSL.com — IV** | Individual | **$129/ano** | Não (nome pessoal) | token/eSigner |
| **Certum Cloud — Individual** | Individual | **€139/$139/ano** | Não (nome pessoal) | cloud (SimplySign) |
| **SSL.com — OV** | Organização | **$129/ano** (1a), $96.75/ano (5a) | Sim (nome da empresa) | token/eSigner |
| **Sectigo — OV** | Organização | $211–288/ano | Sim | token |
| **Certum — Standard Cloud** | Organização | ~€209/ano | Sim | cloud |
| **DigiCert — OV** | Organização | $369–438/ano | Sim | KeyLocker |

> **Recomendação para ti** (nome do estúdio = "Luar Studio Angola"):
> - Se **tiveres empresa registada** → **SSL.com OV** (nome da empresa no instalador, $129 no 1º ano).
> - Se **não tiveres** → **SSL.com IV ou Certum Individual** (nome pessoal, ~$129–139/ano).
>
> Todos "constroem reputação SmartScreen ao longo do tempo" (desde Março 2024 o EV já não
> dá reputação imediata, por isso o OV/IV é suficiente — não precisas de pagar EV caro).

### Custos escondidos a considerar
- **Token USB físico** (desde Junho 2023 a CA/B exige chave FIPS): **+$50–150** se não usares cloud.
- **Cloud signing** (SSL.com eSigner / Certum SimplySign): evita o token; pode ter subscrição (+~$10–100/ano) mas é mais simples e barato a longo prazo.
- **Validade máxima ~1 ano** (regra nova da CA/B, 2026): multi-anos precisam de **re-emissão** — normal em certificados de 2-3 anos, sem custo extra, mas atenção ao processo.

---

## 2. Domínio

| Item | Custo | Notas |
|---|---|---|
| `.com` / `.pt` / `.eu` | **~$10–15/ano** | Obrigatório para página de produto e "App Publisher URL" |
| `.com` premium | $50–several 100s | Só se quiser nome curto |
| Privacidade WHOIS | geralmente grátis | incluída na maioria dos registrars |

Recomendado: comprar o domínio da marca (ex. `maouse.pt` / `maouse.app`) ~$12/ano.

---

## 3. Infraestrutura mínima (para vender)

| Item | Custo | Fase |
|---|---|---|
| Página/landing page (GitHub Pages/Netlify/Vercel free tier) | **$0** | Início |
| Página/landing page profesional (Vercel Pro / hosting) | $20/ano | Opcional |
| **Processador de pagamentos / Merchant of Record** | — | Ver abaixo |

### Pagamentos — a decisão mais importante do modelo
O modelo de negócio atual (BUSSINES) usa **Paddle como Merchant of Record** (trata IVA/VAT da UE
por ti — importante porque vendes para a UE).

| Item | Custo | Notas |
|---|---|---|
| **Paddle** | **$0** (toma % por venda, ~5% + $0.50) | Eles tratam do VAT legalmente por ti; sem subscrição |
| **Stripe** | $0/mês (+2.9% p/ transação) | Tu tens de tratar o VAT; mais complexo na UE |
| Custos de payout/bank | variável | depende do banco em Angola |

> **Recomendação:** **Paddle como MoR** — resolve o IVA da UE sem contabilidade complexa e o teu
> `core/licensing.py` já tem `PADDLE_PRODUCT_URLS` preparado para isto. Custo inicial $0.

---

## 4. Loja / Distribuição

| Item | Custo | Notas |
|---|---|---|
| **Google Play** (mobile) | **$25** (pago 1 vez, conta dev) | Para a versão mobile |
| **Apple Developer** | **$99/ano** | Só se lançares iOS |
| **Microsoft Store** | $19 (1 vez, developer account) | Opcional; o installer standalone já serve |
| Instalador próprio | $0 | Já feito (Inno Setup) |

---

## 5. Detalhes / marcas / ícones

| Item | Custo | Notas |
|---|---|---|
| Ícones/marca | **$0** | Já tens em `assets/brand` (logo, ícone, slogans) |
| Kit de imprensa | $0 | Já feito (`BUSSINES/KIT_DE_IMPRENSA.md`) |
| Listings loja | $0 | Já feito (`BUSSINES/LISTINGS_DE_LOJA.md`) |
| NIF / entidade legal (Angola) | dep. do país | Necessário para faturação se venderes B2B |

---

## 6. Resumo — "Custo de arranque" total (cenário recomendado)

### Cenário A — Individual (sem empresa, caminho mais rápido/barato)
| Item | Custo |
|---|---|
| Assinatura (SSL.com IV ou Certum Individual) | ~$129–139/ano |
| Domínio (.com ou .pt) | ~$12/ano |
| Landing (free tier) | $0 |
| Paddle (MoR) | $0 + % por venda |
| Ícones/marca | $0 |
| **Total 1º ano** | **~$141–151** |
| **Total renovação (anos seguintes)** | **~$141–151/ano** |

### Cenário B — Com empresa registada (nome do estúdio no instalador)
| Item | Custo |
|---|---|
| Assinatura (SSL.com OV) | $129 (1º ano; $96.75/ano em contrato 5 anos) |
| Domínio | ~$12/ano |
| Landing | $0 |
| Paddle (MoR) | $0 + % por venda |
| Ícones/marca | $0 |
| **Total 1º ano** | **~$141** |
| **Total 5 anos (se OV multi-ano)** | **~$484 + domínios** (~$97–109/ano) |

### Cenário C — Com loja mobile incluída
- Cenário A/B + **$25 Google Play** (pago 1 vez) e, se iOS, **$99/ano Apple**.

---

## 7. Lembrete importante

- O custo da assinatura é **anual** (máx. ~1 ano de validade por emissão em 2026).
- Guarda o `.pfx`/chave em local seguro — perder a chave órfã a assinatura.
- Usa **timestamping** no build (já configurado em `installer.iss`) para a assinatura
  continuar válida após expirar o certificado.
- **Nunca** comites a password do certificado nem o `.pfx` para o git (o `.gitignore` já
  protege `.env`, certificado deve ficar fora do repo).

---

*Documento gerado a partir de pesquisa de preços de fornecedores oficiais (SSL.com, Certum, Sectigo, DigiCert, Paddle) em 2026. Preços podem variar — confirmar no checkout.*
