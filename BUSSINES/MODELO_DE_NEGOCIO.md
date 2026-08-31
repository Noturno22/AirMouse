# Modelo de Negócio — Mãouse (AirMouse)

> **Nome comercial:** Mãouse ("a mão é o novo mouse")
> **Nome técnico/repositório:** AirMouse
> **Autor:** Luar Studio Angola · 2026
> **Plataformas:** Desktop (Windows) + Mobile (Android/iOS)
> **Lema:** *"A mão é o novo mouse. Sem cauda. Sem fio. Sem limites."*

---

## Índice

1. [Sumário Executivo](#1-sumário-executivo)
2. [O Produto](#2-o-produto)
3. [Proposta de Valor](#3-proposta-de-valor)
4. [Business Model Canvas — Completo](#4-business-model-canvas--completo)
5. [Análise de Mercado (TAM / SAM / SOM)](#5-análise-de-mercado-tam--sam--som)
6. [Público-Alvo — Segmentação e Ordem de Ataque](#6-público-alvo--segmentação-e-ordem-de-ataque)
7. [Personas](#7-personas)
8. [Inovação](#8-inovação)
9. [A Oportunidade](#9-a-oportunidade)
10. [A Realidade: "Qualquer um pode construir isto com IA"](#10-a-realidade-qualquer-um-pode-construir-isto-com-ia)
11. [Modelo de Receitas e Precificação](#11-modelo-de-receitas-e-precificação)
12. [Estrutura de Custos](#12-estrutura-de-custos)
13. [Projeções Financeiras (5 anos, 3 cenários)](#13-projeções-financeiras-5-anos-3-cenários)
14. [Break-even](#14-break-even)
15. [Concorrência](#15-concorrência)
16. [Matriz Competitiva](#16-matriz-competitiva)
17. [Problemas e Riscos (com mitigações)](#17-problemas-e-riscos-com-mitigações)
18. [Estratégia Mobile vs Desktop](#18-estratégia-mobile-vs-desktop)
19. [Go-to-Market](#19-go-to-market)
20. [Roadmap de Negócio (5 anos)](#20-roadmap-de-negócio-5-anos)
21. [Métricas e OKRs](#21-métricas-e-okrs)
22. [Estrutura Legal e Propriedade Intelectual](#22-estrutura-legal-e-propriedade-intelectual)
23. [Conclusão e Apelo à Ação](#23-conclusão-e-apelo-à-ação)

---

## 1. Sumário Executivo

O **Mãouse** transforma a webcam de qualquer portátil — ou a câmara frontal de qualquer smartphone — num **rato aéreo controlado por gestos da mão, sem hardware extra**. Um motor de precisão profissional (filtros *One Euro*, curva de aceleração exponencial, emissor a 180 Hz, *snap* magnético via UI Automation, duas mãos com redundância, voz híbrida offline + LLM local) transforma algo que historicamente exigia hardware (ratos aéreos) ou licenças caras (UltraLeap, eyeSight) em **software puro com margem próxima de 100%**.

O negócio não é o código — o código foi (e pode ser) construído por qualquer pessoa com IA num fim de semana. **O negócio é a distribuição, a marca, a certificação, o ecossistema e a posse de segmentos de mercado onde o preço é pago por instituições, não por consumidores.**

A tese central:

1. **Primeiro público-alvo = acessibilidade e saúde** — 1 em cada 7 pessoas no mundo vive com algum tipo de deficiência; a Directiva europeia de Acessibilidade (EU EAA) está em vigor desde **28 de junho de 2025**, criando procura legal e financiamento institucional. É o segmento com **maior disposição a pagar por unidade, maior retorno social, menor sensibilidade a preço e compra por instituições/hospitais/governos**.
2. **Windows + Android são o campo de batalha** — iOS não permite injetar toques de terceiros no SO; a estratégia iOS é *modo remoto/controlador do PC* e funcionalidades de acessibilidade permitidas.
3. **A ameaça "qualquer um com IA faz isto" vira vantagem** — responde-se com distribuição, marca (`Mãouse`), dados de afinação reais (opt-in), certificações, suporte, localização PT/EN/outras e contratos B2B que o código aberto nunca consegue ganhar.
4. **Custo marginal ≈ 0** — produto 100% offline, sem servidores obrigatórios, empresa nativa de IA (1 fundador + agentes). Margens EBITDA de 60–80% a partir do 3.º ano.

**Receita a 5 anos (cenário base):** €45k → €150k → €420k → €1.05M → €2.4M com EBITDA de ~77% no 5.º ano. Break-even entre o mês 14 e 18 após o lançamento.

---

## 2. O Produto

### 2.1. Desktop (Windows 10/11)

Controlo total do cursor, cliques, arrasto, scroll, volume, multimédia e comandos de voz **apenas com a mão e a webcam**.

| Sistema | Capacidade atual | Estado |
|---|---|---|
| Motor de precisão (One Euro + aceleração + 180 Hz + predição ~40 ms + sub-pixel) | Movimento sedoso e sem tremor | ✅ Produzido e testado |
| Palma-center como ponto de controlo | Zero saltos ao clicar/arrastar | ✅ |
| Gestos (10+): abrir, 1 dedo, pinças, punho, paz, 3 dedos, polegar, mindinho, shaka | Mover, clicar, arrastar, scroll, volume, play/pause, copiar, colar | ✅ |
| Gestos de duas mãos (palmas, lupa, brilho, troca de janela) | Assistente 3D, zoom, brilho, Alt+Tab | ✅ |
| Mão de comandos (esquerda) separada da mão de controlo | Swipes, punho = Alt+F4, gestos de atalho | ✅ |
| IA de gestos (MLP treinada, híbrida com regras, 7+ classes) + auto-afinação | Desambiguação e adaptação à câmara do utilizador | ✅ |
| Snap magnético (UI Automation) | Cursor "gruda" em botões reais de qualquer app | ✅ |
| Voz híbrida Vosk (wake word "Jarvis") + Whisper local + NLU + TTS neural Piper | Controlo e resposta por voz, 100% offline | ✅ |
| LLM local (Ollama) como fallback de linguagem natural | Comandos livres | ✅ |
| Luz baixa (CLAHE + exposição) | Funciona em ambientes escuros | ✅ |
| GUI PySide6 (frameless, HUD, tema neon), bandeja, arranque com o Windows | Produto "pro" com cara de marca | ✅ |
| Instalador `.exe` (PyInstaller) sem Python | Distribuível | ✅ |

### 2.2. Mobile (Android first)

O mesmo cérebro emocional (MediaPipe HandLandmarker + One Euro + curvas + gestos) corre nativamente no telemóvel:

| Capacidade | Estado |
|---|---|
| Aplicação React Native/Expo (SDK 57, Expo Router, Zustand) | ✅ Em desenvolvimento (estrutura, hooks, engine, store) |
| Câmara frontal + deteção de mãos (arquivo `hand_landmarker.task` incluído) | ✅ |
| Filtros One Euro + AccelCurve portados para TypeScript | ✅ |
| Deteção de 12+ gestos | ✅ |
| Ações nativas Android (Touch, Keyboard, System) via módulos nativos + AccessibilityService | 🔨 Em construção |
| Controlo de voz nativo, calibração automática, modo remoto (controlar o PC via WiFi) | 🔨 Planeado |
| iOS (módulo de acessibilidade e modo remoto) | 🔨 Planeado (restrições da Apple) |
| Loja: Play Store → depois App Store (via EAS Build) | 🔨 Planeado |

### 2.3. Posicionamento

> **Categoria:** Software de interação humano-computador (IHC) sem toque.
> **Diferencial:** precisão profissional + IA embarcada + voz offline + zero hardware + privacidade total (tudo processado no dispositivo).
> **Marca:** Mãouse, por lema "a mão é o novo mouse" (mão + mouse; a til ~ é o elemento identitário).

---

## 3. Proposta de Valor

### Para cada segmento

| Segmento | Dor | Proposta de valor | Ganhos |
|---|---|---|---|
| **Pessoas com mobilidade reduzida** | Ratõs convencionais são difíceis ou impossíveis | Controlar o PC/smartphone só com a mão, por gestos intuitivos + voz | Independência digital, dignidade, trabalho, comunicação |
| **Idosos** | Curva de aprendizagem de ratos/touch/atalhos | Gestos naturais de "apontar" + comandos de voz em português | Reaprendizagem natural, menos frustração |
| **Utilizadores com LER/RSI** | Dor ao usar rato constante (síndrome do túnel cárpico, tendinite) | Alternar entre mão e rato físico para descansar tendões | Menos dor, produtividade mantida |
| **Apresentadores / professores / streamers / criadores** | Ter de andar com clicker/remoto; ficar preso à secretária | Apresentar a andar, controlar slides à distância, mão livre | Presença física, controlo contínuo do PC |
| **Entusiastas tech / PC media-center** | Ratos aéreos de hardware são caros e maus | Software pago uma vez, sem cabos, sem pilhas, funciona na TV box/PC | Futurismo funcional (estética JARVIS) |
| **Instituições (hospitais, escolas, centros de reabilitação, governo)** | Cumprir a EU EAA / 508; dar independência a utentes | Licenças institucionais, suporte, personalização terapêutica, contrato de compliance | Compliance legal + impacto social mensurável |
| **Empresas (OEM, quiosques, medicina, automação)** | Controlo touchless numa bancada/sala limpa | Licenciamento por dispositivo / white-label | Produto diferenciado, sem R&D de CV |

### Proposta de valor em 1 frase

> **"Transforma qualquer webcam ou câmara frontal num rato aéreo preciso, com IA e voz — para quem não pode, não deve ou não quer usar o rato físico."**

---

## 4. Business Model Canvas — Completo

| Bloco | Conteúdo |
|---|---|
| **Segmentos de cliente** | 1) Acessibilidade/saúde (B2C individual + B2G/B2B institucional) · 2) Apresentadores e criadores · 3) Entusiastas tech/media-center · 4) Empresas/OEM (licenciamento) · 5) Mobile-first em mercados emergentes (Android) |
| **Proposta de valor** | Rato aéreo de software com precisão profissional, IA, voz offline e privacidade total; zero hardware; instalação em 1 clique; funciona em PC e telemóvel; resolução de acessibilidade sem comprar periféricos |
| **Canais** | Site oficial (maouse.app) · Microsoft Store · Steam · Play Store · App Store · GitHub (open-core) · YouTube/TikTok (demonstrações virais) · parcerias com associações de acessibilidade · presença em conferências de reabilitação/TEAMs · OEM laptops/boxes |
| **Relação com cliente** | Self-service (freemium) + onboarding com tutorial de gestos · Wizard de calibração pessoal · suporte por ticket/e-mail · comunidade Discord/Telegram · contratos dedicados para instituições · assistente "Jarvis" como UX da marca |
| **Fontes de receita** | Licenças Pro (lifetime/subscrição) · Subscrição Mobile · Licenças institucionais/Enterprise · Licenciamento OEM por dispositivo · White-label · (futuro) pacotes de gestos/idiomas premium · doações não pretendidas |
| **Recursos-chave** | O código (motor de precisão + IA + apps) · a marca Mãouse · o modelo IA treinado e o pipeline de treino com dados reais · ferramentas de build nativas (EAS) · comunidade · propriedade intelectual (marca, domínios, contratos) |
| **Atividades-chave** | Desenvolvimento multi-plataforma (Python + React Native) · manutenção dos modelos MediaPipe/IA · testes em hardware comum · marketing de demonstração · onboarding/certificação de acessibilidade · parcerias institucionais · suporte N1/N2 · compliance de lojas (Play A11y policy) |
| **Parcerias-chave** | Associações de acessibilidade (AACD, APD, equivalentes PT/BR) · terapeutas ocupacionais · fabricantes de portáteis (OEM) · Microsoft (Windows), Google (Android) · universidades (estudos clínicos) · direções de ensino especial/governos PT·BR·AO + EU |
| **Estrutura de custos** | Dominada por **salários/desenvolvimento** (lean, nativa IA) + marketing + taxas de loja (Apple 15/30%, Google 15/30%) + certificação de código/EV · ~zero de custo variável (produto offline, sem servidores) · margens 85–95% brutas |
| **Estrutura financeira** | Bootstrapping + subsídios de inovação/startups (INOV Contacto, Compete, PRODUTECH, fundos EU de acesso digital, EIT Health) + crédito/premio de inovação se necessário · económia unitária: LTV ≫ CAC |

---

## 5. Análise de Mercado (TAM / SAM / SOM)

> Todas as estimativas são aproximadas (fontes públicas: Statista, WHO, Gartner, relatórios de analistas) e servem para ordenar decisões, não como previsão precisa.

### 5.1. Mercados de base (2025–2026)

| Dimensão | Valor | Nota |
|---|---|---|
| Dispositivos Windows ativos | ~1,4 mil milhões | Base instalada desktop |
| Portáteis enviados por ano (com webcam quase 100%) | ~250–280M/ano | Notebook dominante em vendas |
| Utilizadores de smartphones | ~4,9 mil milhões | Android ~3,6–3,8 mil milhões |
| Pessoas com deficiência significativa (OMS) | ~1,3 mil milhões (~16%) | 1 em cada 7; motor/visão são subgrupos grandes |
| Mercado de **reconhecimento de gestos** | US$13–15 mil milhões em 2030 | Diferentes análises, CAGR ~20–25% |
| Mercado de controlo por voz/IA de input | US$20+ mil milhões | Voz + gesto convergem em IHC |
| Taxa de incidência de LER/RSI em escritório (estimativas) | 30–60% dos utilizadores intensivos de rato | Dor/desconforto; rato é fator principal |

### 5.2. TAM · SAM · SOM

```
TAM  (mercado total endereçável)
     Controlo IHC sem toque (gestos + voz) em PC e mobile
     ≈ US$15 mil milhões/ano (2030) → ~€13 mil milhões

SAM  (mercado servível e obterível com a proposta atual)
     Controlo por gestos de mão em Windows + Android (consumidor,
     acessibilidade, apresentações, media-center, kiosk)
     ≈ 2–4% do TAM → ~€300–500 milhões/ano

SOM  (quota alcançável em 5 anos, capturável com execução)
     ~0,5–1% do SAM → €2–4 milhões/ano de receita recorrente
     (consistente com o cenário base de €2,4M no ano 5)
```

### 5.3. Porquê este mercado agora

1. **Webcams universais** — pós-pandemia todos os portáteis têm câmara; custo de aquisição = 0.
2. **NPUs/IA nos PCs** — portáteis Copilot+ com NPU normalizam inferência local barata e rápida.
3. **Regulação de acessibilidade** — EU Accessibility Act (28/06/2025), Section 508, leis de acessibilidade em BR/PT; hospitals & escolas precisam de software *comprovavelmente* acessível.
4. **Vazio real** — não existe hoje um produto mainstream adotado de "rato de gestos por webcam" com qualidade profissional; os concorrentes são hardware caro (UltraLeap) ou apps acessíveis de 2.ª linha (Camera Mouse).
5. **Máquina de IA barata** — este produto foi construído com IA; o custo de competir em qualidade caiu, o que beneficia quem **distribui bem**, não quem tem mais engenheiros.

---

## 6. Público-Alvo — Segmentação e Ordem de Ataque

### 6.1. Ordem de ataque (sequenciamento deliberado)

A regra é: **entrar primeiro onde a disposição a pagar é maior, a concorrência é fraca e o impacto é mensurável** — e usar essa base para financiar os segmentos de massa.

| # | Segmento | Prioridade | Razão estratégica |
|---|---|---|---|
| **1** | **Acessibilidade & saúde (individual + institucional)** | 🔴 **FIRST** | Maior disposição a pagar por utente; compra por instituições (não por consumidor individual); *financiável* por subsídios de saúde; o que torna o "maior retorno da história" atingível: cada contrato institucional vale mais que centenas de downloads gratuitos; impacto social publicável (PR ganha) |
| **2** | **Apresentadores, professores, criadores** | 🟠 2.º | Early adopters virais; demonstração impressiona em vídeo; TAM grande, conversão média |
| **3** | **Mobile Android (mercados emergentes + acessibilidade móvel)** | 🟠 2.º/3.º | Escala massiva, custo de CAC baixo via loja; fundamental para "maior retorno em volume" |
| **4** | **Entusiastas tech / media-center / gamers** | 🟡 3.º | Comunidade, feedback técnico, evangelismo; preço baixo mas baixo LTV |
| **5** | **B2B/OEM (portáteis, TV boxes, quiosques, medicina)** | 🟡 4.º | Receita por dispositivo com contrato de anos; exige maturidade do produto e provas clínicas/performance |

> **Porquê acessibilidade primeiro (o argumento do "maior retorno da história"):**
> Não é o segmento mais numeroso — é o que **mais paga por utilizador**, o que menos faz *churn* (necessidade vital), o que tem **financiamento externo** (reabilitação, seguros, estados), o que gera **provas clínicas** que abrem as portas B2B, e o que dá à marca uma **licença moral** para pedir preço premium. Um contrato de licença com um hospital/centro de reabilitação vale tipicamente €5.000–50.000/ano — o equivalente a 1.000–10.000 vendas consumer. Somado ao volume mobile, é o caminho para o maior retorno.

### 6.2. Estimativa de dimensão do segmento 1 (acessibilidade)

| Dado | Estimativa |
|---|---|
| Pessoas com limitação motora dos membros superiores (global) | 50–100 milhões |
| Dentre estas, com acesso a um PC/smartphone (não será menor que...) | 15–25% |
| Utilizadores potenciais só em PT + BR + AO + UE | ~3–6 milhões |
| Disposição a pagar (individual, uma vez) | €29,90–59,90 (ou subscrição coberta por terapêutico) |
| Disposição a pagar (instituição, por ano) | €500–5.000 (licenças) · €5k–50k (contratos) |
| Financiamento disponível (escolas/hospitais/estado, EUR no espa… PT/UE) | Programas de acesso digital, fundos de reabilitação |

---

## 7. Personas

### 1. Dona Albertina, 68, reformada (PT)
PC da família para falar com os netos. Fica frustrada com o rato. Com o Mãouse: abre a mão para mover, pinça para clicar, "Jarvis, envia mensagem". **Valor: independência digital.** Compra: Pro lifetime (€34,90) apoiada pela família.

### 2. Carlos, 41, com paralisia/lesão nos membros superiores (institucional)
Trabalhador remoto com lesão que impede uso contínuo do rato. A empresa compra 1 licença Enterprise para ele (€9,90/mês) porque é mais barato que ergonomia clínica contínua. **Valor: mantém o emprego.** Canais: terapeuta ocupacional, seguradora de trabalho, RH.

### 3. Dra. Marisa, fisiata/reabilitadora
Dirige um centro de reabilitação com 40 PC e 30 tablets. Precisa de cumprir EU EAA e dar a pacientes gesto+voz. Compra **contrato institucional** de 60 licenças + formação (€12.000/ano). **Valor: compliance + impacto + evitar procura de soluções avulsas.**

### 4. Rui, 34, professor universitário
Dá aulas com o PC na mão, a andar. Com o Mãouse controla slides à distância com a mão esquerda e aponta com a direita, sem remoto. Grava um TikTok da demo → viraliza. **Valor: presença.** Converte-se a Pro (LTV + suporte).

### 5. Fábio, 27, gamer/media-center
Tem um mini-PC na TV com Windows. Odiava os air-mice de hardware (pilhas, dongle). Compra Pro uma vez (€39,90) e usa na cama. **Valor: futurismo funcional.** É *power user* → feedback técnico grátis.

### 6. Pedro, gestor de TI numa rede hospitalar (OEM/B2B)
Equipa 500 postos com webcams; quer controlo touchless nos postos de higiene e quiosques. Compra licenciamento por dispositivo (€1,50/dispositivo/ano). **Valor: higiene + operação.**

---

## 8. Inovação

### 8.1. Inovação de produto (o que já existe e ninguém juntou)

| Dimensão | Inovação |
|---|---|
| Precisão | Emissor a 180 Hz com sub-pixel + predição ~40 ms + curve de aceleração exponencial → movimento "hardware-like" numa webcam a 15–30 fps |
| Estabilidade | Filtro One Euro + palm-center + histerese/pins + deadband Schmitt por dedo → zero tremor, zero cliques fantasmas |
| "Interface magnética" | Snap magnético via UI Automation: o cursor atrai-se aos alvos clicáveis reais de qualquer app nativa/Chrome |
| Convívio com o rato | Travamento de mão (controlador dominante), mão de comandos separada da mão que move, palmas/lupa/brilho com 2 mãos |
| IA híbrida | Classificador neural (MLP, ~35 KB) em fallback com regras geométricas; treino pessoal do utilizador (coleta + retreino local) |
| Voz completa offline | Wake word instantânea (Vosk) + Whisper local + NLU PT + TTS neural Piper — o assistente "Jarvis" é a UX da marca |
| Adaptação ambiental | Auto-afinação contínua dos filtros/ganho; realce em luz baixa (CLAHE + exposição) |
| Multi-plataforma | Mesmo motor de precisão em Python (desktop) e TypeScript (mobile) |

### 8.2. Inovação de processo (a vantagem escondida)

- **Empresa nativa de IA:** 1 fundador + pipeline de agentes construiu produto que historicamente exigia 3–5 engenheiros de CV/ML durante 1–2 anos.
- **Iteração documentada:** PROGRESSO.md, mm.md, re.md mostram ciclo *feedback→implementação→verificação* com subagentes (implementer/reviewer/verifier) — execução com qualidade industrial a custo de startup.
- **Testes por automação:** suítes de gestos/handlock/motion (ex. 23/23 PASS) em vez de QA manual.

### 8.3. Inovação de modelo de negócio

- **Open-core inteligente:** núcleo gestos/IA gratuito para gerar adoção e *provas*, monetizar precisão avançada, snap, voz, duas mãos, multi-dispositivo e institucional.
- **Custo marginal zero:** produto 100% local/offline → escalar de 100 para 1 milhão de utilizadores não aumenta custo servidor.
- **Privacidade como venda:** "a câmara e a voz nunca saem do teu dispositivo" — argumento premium impossível para apps cloud.

---

## 9. A Oportunidade

### 9.1. Janelas que se abriram (e porquê agora)

1. **EU Accessibility Act (28/06/2025)** — obriga serviços/software (incl. computadores e sistemas operativos) a serem acessíveis. Municípios, hospitais e empresas da UE precisam de *comprar* conformidade → procura institucional imediata.
2. **Cultura de vídeo/apresentação dominante** — reuniões híbridas, salas de aula e estúdios procuraram movimento físico; o orador quer a mão livre.
3. **Webcam + NPU em todo o lado** — infraestrutura de inferência local já instalada, sem investimento.
4. **Cansaço do hardware** — ratos aéreos (Logitech MX Air, Rii, Minix) são caros/maus/carregam pilhas; "software-only" vence por preço e distribuição.
5. **Mercados emergentes** — smartphone é o *primeiro* computador de milhões; gesto+voz em Android responde a alfabetização e mobilidade.
6. **Redução do custo de construir (IA)** — a barreira deixou de ser o código; passou a ser captura de ecossistema → **quem agir primeiro no segmento institucional captura o prémio.**

### 9.2. Sinal de produto-mercado (early evidence)

- Este repositório já produziu 17+ commits de polish de produto (estabilidade, GUI PySide6, ajuda, voz, mobile) — sinais de investimento de SÓCIO-função no produto.
- Existência de GESTOS.md, IDENTIDADE_VISUAL com posicionamento "pro para venda" — decisão já tomada de **comercializar**, não só libertar código.

---

## 10. A Realidade: "Qualquer um pode construir isto com IA"

> Este documento reconhece frontalmente: **este produto, como está, pode ser replicado em semanas por outro desenvolvedor + IA.** Esta secção transforma essa ameaça na espinha dorsal da estratégia.

### 10.1. O grau de replicabilidade, item a item

| Componente | Dificuldade de replicar | Porquê |
|---|---|---|
| Deteção de mãos (MediaPipe) | ★☆☆ (trivial) | API pública gratuita |
| Gestos básicos (pinça, punho, paz) | ★★☆ | Heurísticas conhecidas |
| Motor de precisão (One Euro, aceleração, sub-pixel) | ★★★ | Conhecimento fino combinado; mas encontrável na literatura |
| Snap magnético (UI Automation) | ★★★ | Detailed Windows API + tuning |
| IA de gestos treinada + coleta+retreino 100% local | ★★★ | Pipeline de dados reais, não só modelo pronto |
| Voz + TTS offline integrada | ★★☆ | Modelos públicos, integração chata |
| GUI "pro", marca, identidade, mobile RN | ★★☆ | Tempo de obra de design/polish |
| **Distribuição, marca, certificação, contratos** | **★★★★★ (quase impossível de replicar num fim de semana)** | Leva anos, relações, confiança |

### 10.2. Conclusão estratégica

- **A moat NÃO é o código.** A moat é: **a —** marca e identidade (`Mãouse`), **b —** distribuição (lojas, site, criadores), **c —** provas (testes, estudos clínicos, certificações de acessibilidade WCAG), **d —** ecossistema (comunidade de utentes, terapeutas, OEM), **e —** corpus de dados reais de afinação (opt-in, anonimizado) que melhora o produto enquanto os clones ficam com modelos sintéticos, **f —** contratos B2B/B2G com ciclos de venda longos que clones recém-nascidos não conseguem vencer.
- **Estratégia-cópia:** assumir que alguém faz fork/clone amanhã. Respostas: (1) velocidade de integração com o SO que clones não têm; (2) open-core gera *goodwill* e comunidade antes do fork; (3) manter camadas premium (snap, duas mãos, institucional) fora do open-core.
- **Apostar no que a IA não dá:** suporte humano, formação a terapeutas, presença em conferências de reabilitação, e **licenças institucionais** — o dinheiro gordo está nestes canais, onde um clonador de fim de semana não compete.

---

## 11. Modelo de Receitas e Precificação

### 11.1. Desktop (Windows)

| Tier | Preço | O que inclui |
|---|---|---|
| **Mãouse Free** | €0 | Abrir a mão/cursor, pinça clique, 1 mão, sem snap, sem voz, com watermark subtil em demo; **com objetivo de adotar e provar** |
| **Mãouse Pro** | €39,90 vitalício **ou** €4,99/mês (ou €3,49/mês anual) | Todos os gestos, duas mãos, snap magnético, voz "Jarvis", TTS neural, auto-afinação, IA avançada, luz baixa, arranque automático, personalização |
| **Mãouse Business** | €9,90/utilizador/mês (min. 5) | Tudo do Pro + gestão, ativação central, SUPPORTO SLA, relatório de compliance acessibilidade, onboarding |
| **Licença vitalícia familiar** | €59,90 | 3 dispositivos |

### 11.2. Mobile (Android first; iOS = modo remoto)

| Tier | Preço | O que inclui |
|---|---|---|
| **Mobile Free** | €0 | Mover/tap/2 gestos em 1 app; limite de gestos avançados |
| **Mobile Pro** | €2,99/mês · €19,90/ano · €49,90 vitalício | Todos os gestos, ações de sistema, voz, calibração, modo remoto PC (telefone controla o PC pela rede via companion) |
| **Institucional (instituições/terapia)** | €0,99/utente/mês com mínimo anual | Faturação, gestão de prof., dados locais |

### 11.3. B2B / OEM / White-label

| Pacote | Preço indicativo |
|---|---|
| OEM por dispositivo (portáteis/TV boxes) | €0,50–2,50/dispositivo/ano (volume-dependente) |
| Quiosques/postos médicos | €99–249/posto/ano |
| White-label (integração + marca) | Projeto €15–40k + royalties 10–20% |
| Contrato de acessibilidade institucional (hospital/escola/rede) | €5.000–50.000/ano (licenças + formação) |

### 11.4. Regras de pricing

- **Âncora por valor vs proteção de custo:** o preço ancora no custo de hardware alternativo (UltraLeap €100+; air-mouse €25–60; sessão de ergonomia €80+) — o Pro a €39,90 é 40–60% mais barato que qualquer solução física com 10× mais funcionalidade.
- **Desconto acessibilidade de 50%** mediante comprovativo (boa publicidade + segmento sensível) — nunca grátis (para não ancorar zero).
- **Regional pricing** para PT/BR/AO/África: preços locais (ex. ●R$ 39,90 · Kz 8.000) para maximizar volume mobile.

### 11.5. Fontes de receita (mix-alvo a 5 anos)

| Fonte | Peso-alvo 5.º ano |
|---|---|
| Subscrições mobile (IAP) | 25% |
| Licenças Pro desktop (lifetime/subs) | 20% |
| Contratos institucionais de acessibilidade (B2G/B2B) | 30% |
| OEM / white-label | 20% |
| Long tail (formação, pacotes de gestos, doações pós-conteúdo) | 5% |

---

## 12. Estrutura de Custos

**Produto 100% offline → custo marginal ≈ 0.** As despesas são quase todas fixas e altamente flexíveis.

| Categoria | €/mês (Y1) | €/mês (Y3) | Notas |
|---|---|---|---|
| Fundador (salário de subsistência) | 1.500 | 3.500 | Em Luanda/remoto, permitido por produto distribuível globalmente |
| Marketing/conteúdo (criadores, ads orgânicos) | 300 | 2.500 | Demo viral é o CAC principal |
| Taxas de loja (15/30% mobile) | variável | 15% da receita mobile | Custável na conta de resultados |
| Ferramentas (EAS, firma, domínios, CI) | 80 | 250 | Near-zero |
| Certificação/assinatura de código Windows | — | 300/ano | EV code signing |
| Suporte (terceirizado/fundador) | 0 | 500 | Tickets + comunidade |
| Contabilidade/legal (Angola + PT/UE) | 100 | 400 | Estrutura societária e contratos |
| Total fixo médio | **~1.980/mês** | **~7.100/mês** | |

**Ponto importante:** a maior vantagem da empresa nativa de IA é que **o custo de desenvolvimento já foi ~€0** (construído com agentes). O que normalmente custava €80–150k de engenharia é agora uma despesa de eletricidade + noite da founder. Isso coloca o break-even muito baixo e o múltiplo de margem muito alto.

---

## 13. Projeções Financeiras (5 anos, 3 cenários)

> Pressupostos: conversão free→pago 1,5–4% (acessibilidade converte mais); receita média por pagante consumer ~€30/ano (mix lifetime+lifetime+subs); contratos institucionais começam Y2/Y3; OEM entra Y4/Y5; margem bruta 90%+.

### 13.1. Cenário Base (execução boa, sem golpe de sorte)

| Ano | Free users (cum.) | Pagantes | Receita consumer | Institucional | OEM/B2B | **Receita total** | Custos | **EBITDA** | Margem |
|---|---|---|---|---|---|---|---|---|---|
| 0 (2026) | — | — | — | — | — | **€0** | €4k | −€4k | — |
| 1 | 45.000 | 1.100 | €33k | €5k | €7k (1º piloto) | **€45k** | €38k | **€7k** | 16% |
| 2 | 180.000 | 4.200 | €115k | €25k | €10k | **€150k** | €70k | **€80k** | 53% |
| 3 | 550.000 | 12.000 | €270k | €90k | €60k | **€420k** | €140k | **€280k** | 67% |
| 4 | 1.300.000 | 28.000 | €560k | €260k | €230k | **€1.050k** | €300k | **€750k** | 71% |
| 5 | 2.600.000 | 62.000 | €1.100k | €600k | €700k | **€2.400k** | €560k | **€1.840k** | 77% |

### 13.2. Cenário Conservador (venda lenta, sem B2B)

| Ano | Receita total |
|---|---|
| 1 | €15k |
| 2 | €45k |
| 3 | €110k |
| 4 | €260k |
| 5 | €520k |

### 13.3. Cenário Otimista (contrato regional + 1 OEM + viralização)

| Ano | Receita total |
|---|---|
| 1 | €90k |
| 2 | €320k |
| 3 | €1.1M |
| 4 | €3.2M |
| 5 | €9.0M |

### 13.4. Leitura dos cenários

- O custo fixo baixo torna **até o cenário conservador sustentável** a partir do Y2.
- O valor está concentrado no **capítulo institucional/OEM**, que depende de velocidade de entrada em acessibilidade (Y1→Y2) e provas clínicas.
- Cada contrato institucional médio de €15k/ano ≈ 375 subscrições mobile — a alavanca financeira mais eficiente do modelo.

---

## 14. Break-even

- **Cenário base:** break-even entre **mês 14 e 18** após o primeiro lançamento pago (Mãouse Pro em loja Windows/web) — dado que Y1 termina com EBITDA positivo.
- **Cenário conservador:** mês 26–30.
- **Cenário otimista:** mês 9–12.
- Ponto de break-even em receita recorr.— simples: custos fixos ≈ €2k/mês → é preciso ≈ 60 subscrições Pro/ano-equivalente (€4,99) OU 1 contrato institucional pequeno/ano. **Número alcançável com um único contrato de acessibilidade.**

---

## 15. Concorrência

### 15.1. Mapa concorrencial

| Tipo | Concorrentes | Força | Fraqueza vs Mãouse |
|---|---|---|---|
| **Hardware air-mouse** (preço baixo) | Rii M01/Mini X8/i8, Minix NEO A2/A3/A4, Logitech MX Air (legado), LG Magic Remote | Baratos ($10–30), mainstream em media-center TV | Precisam de pilhas/dongle/USB; precisão básica; sem IA/voz; um objeto a mais |
| **Hardware premium gestos** | UltraLeap (Leap Motion), Intel RealSense, Sony PS Eye | Precisão real de CV (IR stereo) | €100–250 + dongle + SDK; setup técnico; não resolvem "rato do dia-a-dia" simples |
| **Software acessibilidade gratuita** | Camera Mouse (Boston College), Enable Viacam, eViacam, Pointerware, Nouse (TRACE) | Grátis, usadas há 20 anos em reabilitação | Movimento absoluto tosco, latência, zero gestos de clique fieis, UI envelhecida, sem voz/IA, sem build mobile |
| **Controlo por voz** | Windows Speech, Cortana (legado), assis/plugins, apps de ditado | Voz resolve parte | Não move cursor nem clica com precisão; não substitui rato |
| **Apps de acesso remoto (controle telemóvel→PC)** | Unified Remote, PC Remote, TeamViewer, AnyDesk | Controlo via toque no telefone | O telefone fica ocupado a servir de rato; não é gestos/voz; UX de "tocar" |
| **Big Tech (ameaça futura)** | Microsoft (Windows Copilot gestures), Apple (eye/hand track em visionOS), Google (Android/ChromeOS hand sens.), Qualcomm/ eyeSight (licença OEM) | Recursos ilimitados, OS bundling | Foco em hardware/ecosistema próprio; raramente generalizam para Windows-toaster / acessibilidade PT; lentos; Mãouse apanha OEM antes |
| **Open source / forks (replicadores)** | Qualquer dev+IA (ver sec. 10) | Novos entrantes rápidos | Sem distribuição, marca, provas nem contratos |

### 15.2. Leitura competitiva

- **Ninguém ocupa o cruzamento "precisão profissional + IA + voz offline + zero hardware + multiplataforma + PT/BR".** Cada concorrente isolado domina apenas uma dimensão.
- O **espaço de acessibilidade institucional** (Camera Mouse e afins) é abandonado em qualidade/design → substituição fácil com produto 10× mais capaz.
- O maior risco **não é o concorrente atual, é o tempo até a big tech entrar** — daí o foco em capturar contratos B2B/OEM e marca antes disso.

---

## 16. Matriz Competitiva

| Critério (0–5) | Mãouse | UltraLeap | Rii/Air-mice HW | Camera Mouse | Voice dictation | Remoto-app |
|---|---|---|---|---|---|---|
| Preço-benefício | **5** | 2 | 4 | 4 | 4 | 4 |
| Precisão | **5** | 5 | 3 | 2 | 1 | 3 |
| Zero hardware | **5** | 1 | 1 | 5 | 5 | 4 |
| IA + voz offline | **5** | 1 | 0 | 0 | 3 | 1 |
| Acessibilidade | **5** | 2 | 2 | 4 | 3 | 2 |
| Multiplataforma (PC+móvel) | **5** | 2 | 3 | 1 | 2 | 4 |
| Qualidade de produto / UI polish | **4** | 3 | 2 | 1 | 3 | 3 |
| Privacidade offline | **5** | 4 | 5 | 5 | 3 | 2 |
| **Total** | **39** | 20 | 20 | 22 | 24 | 23 |

---

## 17. Problemas e Riscos (com mitigações)

### 17.1. Riscos técnicos/produto

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Latência/erro em webcams fracas ou pouca luz | Alta | Médio | Chegou de propósito: luz baixa (CLAHE), auto-afinação, tolerância de confiança 0.5, testes em câmara real |
| Fadiga do utilizador (braço no ar) | Média | Médio | Gesto 1-dedo menos cansativo, alternância mão/rato, pausas; aconselhar uso intermitente (não 8h) |
| Cliques acidentais durante apresentação | Média | Alto | Histerese de pinça, estabilidade de frames, congelação em transições, tecla de emergência (espaço) |
| Antivírus/assinatura .exe | Alta | Alto | Code-signing EV, presença no SmartScreen, distribuir via Microsoft Store (signed), evitar heurísticas falsas |
| iOS impossibilita injeção de toques | **Certa** | Médio | Estratégia: Android = controlo total; iOS = *modo remoto* (telefone controla o PC pela rede) + acessibilidade permitida pelos APIs (Switch Control, Voice Control não técnico-Mãouse) — nunca prometer injeção iOS |

### 17.2. Riscos de plataforma

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Google Play policy de Accessibility API | Média | Alto | Posicionar o **propósito primário = acessibilidade** (documentação, vídeo de conformidade, teste de política); manter funcionalidades dentro do scope permitido; fallback: lojas alternativas + APK direto |
| Mudanças no MediaPipe/OpenCV/PySide6 | Média | Médio | Pin de versões, modelos locais, abstração do tracker (já existe `core/tracker.py`) |
| Microsoft muda Win32/UI Automation | Baixa | Médio | Camada `core/snap.py` isolada; fallback geométrico |

### 17.3. Riscos de negócio

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| **Replicação por "dev + IA"** | **Alta** | Alto | Ver sec. 10: moat em distribuição/marca/provas/contratos; open-core gera comunidade; velocidade |
| Fragmentação de preço (grátis mata venda) | Média | Médio | Free = núcleo limitado SEM snap/voz/duas mãos/mobile avançado; âncoras de valor em hardware |
| Segmento acessibilidade sensível a custo | Média | Médio | Descontos 50% + licenças institucionais financiadas (fundos de reabilitação); foco em instituições que pagam |
| Mercado emergente paga pouco | Alta | Baixo | Volume (€1–3/mês) + regional pricing; acessibilidade não é o dinheiro nos emergentes |
| Dependência de um único canal (ex. viral TikTok) | Média | Médio | Diversificar: lojas, OEM, institucional, conferências, SEO site |

### 17.4. Riscos legais/compliance

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| GDPR/LGPD (câmara em uso) | Média | Alto | Tudo on-device, sem dados; política de privacidade explícita; telemetria opt-in anónima só para melhorar precisão |
| EU EAA / WCAG compliance do próprio produto | Média | Alto | Documentar conformidade (WCAG 2.2 AA, contraste 18.2:1 já desenhado), auditoria independente para venda B2G |
| Direitos de marca (`Mãouse`) | Baixa | Médio | Registar marca CTM/EUIPO + USPTO + edição PT/BR; registar domínios maouse.*; trademark do slogan |
| Reivindicações médicas imprudentes | Média | Alto | Não prometer "curar LER"; vender como ferramenta de ergonomia, não dispositivo médico (evitar classificação MD) |

### 17.5. Riscos financeiros

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Runway curto no pré-receita | Alta | Médio | Custo fixo ~€2k/mês; subsídios (INOV, Compete, EIT, fundos de acesso digital); freelance/bootstrapping |
| Flutuação cambial (EUR/ao-kz / dólar) | Média | Baixo | Cobrar em EUR/USD; contas multi-moeda |
| Fraude/chargeback em IAP | Baixa | Baixo | Loja gere; política standard |

---

## 18. Estratégia Mobile vs Desktop

### 18.1. Desktop — a "arca do ouro" institucional

- Vento grátis: acessibilidade + apresentações + media-center.
- Canais de cauda longa: Site + Microsoft Store + Steam (gaming em vez disso) + GitHub (open-core).
- **Prioridade:** converter o protótipo `.exe` com PyInstaller em produto instalável polido (EV signing, uninstaller, telemetria opt-in, licenciamento robusto).

### 18.2. Mobile — a máquina de escala e de catcher de markets emergentes

- **Android primeiro** (controle total via AccessibilityService nativo + módulos).
- iPhone → **modo remoto**: o iPhone torna-se o *controlador* do Mãouse Desktop (por WiFi, gesto+voz no ecrã → comanda o PC). Racional: evita a restrição OS; cria ecossistema "PC+móvel" que ninguém tem.
- Monetização mobile em subscrição → receita recorrente previsível; regional pricing.

### 18.3. Sinergia PC↔móvel (única no mercado)

- O mesmo utilizador compra Pro desktop + Pro mobile com desconto de pack (combo €69,90).
- Modo remoto integra: "a mão no telefone controla o rato do PC" — cenário perfeito para salas de aula e reuniões.
- Calibração/gestos sincronizados por QR (sem conta obrigatória).

---

## 19. Go-to-Market

### 19.1. Funil

```
Descoberta → Demo viral (10–30s) → Download Free → Ativação (wizard gestos, 2 min)
→ Substituição da câmara pelo teclado → Primeiro "wow" (mover + clicar)
→ Upgrade Pro (snap, voz, duas mãos) → Renovação/Comunidade → Upsell Institucional
```

### 19.2. Canais (por fase)

| Fase | Canais |
|---|---|
| **Y1 (prova & segmento 1)** | Landing page + vídeos de demonstração (PT/BR/EN); contactar 10 centros de reabilitação PT/BR/AO + 5 universidades; presença em conferências de tecnologia assistiva (eAccessibility, TEAMs); publicar open-core no GitHub (SEO + dev-brass); primeiras licenças Pro |
| **Y2 (escala consumer)** | Play Store + Microsoft Store + Steam; TikTok/YouTube/Instagram Shorts com criadores de tech/acessibilidade; parceria com terapeutas ocupacionais como "prescribes do Mãouse"; grupos de suporte a LER; caso de estudo com 1 instituição-âncora |
| **Y3 (B2B)** | Roadmap OEM (portáteis com webcam, TV boxes), white-label para fabricantes; contratos com redes hospitalares/escolas; participar em licitações públicas de acessibilidade; programa de afiliados |
| **Y4–Y5** | Internacionalização EN/ES/FR; OEM internacional; possível linha de hardware opcional (dongle Cov)* — *decisão deliberada: manter **software-first**, hardware apenas se OEM pedir* |

### 19.3. Mensagens-chave

- "A tua webcam já é um rato. Nós só precisamos do software."
- "Sem hardware. Sem fios. Sem subscrição obrigatória. 100% privado."
- "Feito em PT. Da Luar Studio Angola para o mundo."

### 19.4. Financiamento não-dilutivo (ordem de tentativa)

1. Subsídios de inovação PT/UE (Startup Portugal, Compete, Horizonte Europa Acessibilidade, INOV).
2. Prémios internacionais de tecnologia assistiva.
3. Parcerias institucionais pagas (pilotos financiados).
4. Como último recurso — equity.

---

## 20. Roadmap de Negócio (5 anos)

| Ano | Marcos de produto | Marcos de negócio | KPIs-chave |
|---|---|---|---|
| **Y0 (2026)** | Desktop Pro pronto (.exe + licenciamento) · Wizard de onboarding · página de vendas · open-core publicado | Legal: sociedade, marca, domínios · prefixos preço | 100 beta users; 1º piloto institucional |
| **Y1** | Mobile Android na Play Store (controle total) · telemetria opt-in · suporte EN | 1º contrato institucional · subsídio aprovado | 45k free; 1.1k pagantes; €45k Rev |
| **Y2** | iOS modo remoto · Steam/Microsoft Store · localização EN/ES | 3 instituições-âncora · criadores ativos · ROI CAC<6 meses | 180k free; €150k Rev |
| **Y3** | Estudo clínico de ergonomia (universidade) · API OEM · white-label docs | 1 piloto OEM · programa de afiliados · licitação pública 1º win | €420k Rev; margem 67% |
| **Y4** | Suporte a outras línguas · modo kiosk/medicina · compliance WCAG auditoria | 2 OEMs · mercados FR · linha educativa (escolas) | €1,05M Rev; 71% |
| **Y5** | Plataforma de gestos/idiomas premium · parcerias globais de acessibilidade | OEMA internacional · possível M&A de empresa assistiva ou licença master | €2,4M Rev; 77%; 2,6M free |

---

## 21. Métricas e OKRs

### 21.1. Economicas de unidade a monitorizar

| Métrica | Alvo | Porquê |
|---|---|---|
| Conversão free→pago | 1,5–4% | Governa a máquina |
| LTV pro ÷ CAC | > 3 | Sustentabilidade |
| CAC | < €8 (orgânico/criadores) · < €30 (pago) | Vendas por herbalismo |
| Churn mensal | < 3% (só mobile subs) | Receita recorrente |
| Contrato institucional médio | €15k–€30k/ano | Alavanca financeira nº1 |
| NPS acessibilidade | > 60 | Prova de impacto |

### 21.2. Métricas de produto

| Métrica | Alvo |
|---|---|
| Tempo até "primeiro wow" (down→mover+clicar) | < 3 min de instalação, < 30 s |
| FPS médio em webcam normal | 25–30+ |
| Latência gesto→ação | < 80 ms percebida |
| Crash-free sessions | > 99,5% |
| Problemas detetados (suporte ticket/1000 users) | < 5 |

### 21.3. OKR trimestral (exemplo de modelo)

- **O1 — Provar o segmento 1:** 3 contratos/pilotos institucionais assinados · NPS>60 · 1 estudo de caso publicado.
- **O2 — Máquina de funnel:** 30k downloads/mês com conversão 2% · vídeo de demo com >1M views herdado via criador.
- **O3 — Fundação técnica:** mobile Android produz rutura ≥30 fps em 5 dispositivos low-end · retenção D7 > 40%.

---

## 22. Estrutura Legal e Propriedade Intelectual

### 22.1. Sociedade

- Recomendação: **sociedade-holding dupla** — entidade raiz em Angola (Luar Studio) + **nil/de entrada leve na UE (Portugal)** para cobrança de subsídios UE/EAA, cartões de VAT e loja de app. Decidir com contabilista (Sociedade Unipessoal Lda ou Unipessoal por quotas).
- Contas multi-moeda (EUR principal), cobrança via lojas + gateway (Stripe/Paddle para desktop).

### 22.2. Proteção

| Item | Ação |
|---|---|
| Marca `Mãouse` | EUIPO + USPTO + propriedade PT/BR (ng registos); depositar logótipo + slogan |
| Domínios | maouse.app/.io/.pt; arpox barbatos de typosquatting |
| Código | Open-core liberto (MIT/AGPL no núcleo) com camadas premium closed; garantir **copyright clean** (AI-assisted code — documentar autoria; sem violar licenças de modelos: MediaPipe Apache 2.0, Vosk Apache, Piper MIT, Whisper MIT — todos permissivos ✅) |
| Dados | Telemetria opt-in apenas, anónima, GDPR/LGPD; DPA para institucional |

### 22.3. Compliance comercial

- Política de privacidade + termos em PT/BR/EN; consentimento de câmara explícito.
- Declaração de conformidade de acessibilidade para licitações.
- **Não** posicionar como dispositivo médico (evitar regulamentação MDR).

---

## 23. Conclusão e Apelo à Ação

O Mãouse é, simultaneamente:

1. Um **produto de precisão** raro (motor que ninguém comercializou em software puro);
2. uma **máquina de recambio de hardware** que torna um periférico de €25–100 obsoleto;
3. uma **resposta regulatória** à EU EAA que transforma obrigação legal em receita;
4. uma **empresa nativa de IA** com custo de construção ~0 e margens de 80%;
5. e um **reconhecimento honesto** de que o código é réplicável — o que obriga a correr para a única moat que sobrevive à IA: **distribuição, marca, provas, contratos e ecossistema.**

### As 5 decisões imediatas

1. **Aprovar este modelo** (fechar preços, segmentos e ordem de ataque).
2. **Registar marca + domínios Mãouse** (semana 1).
3. **Encaixar a acessibilidade como posicionamento primário** (site, Play Store, documentação).
4. **Arrancar o funil: página + 3 vídeos demo + open-core GitHub** (semana 2–4) + 10 contactos institucionais.
5. **Fechar o produto instalável desktop** (EV signing + licenciamento) e o **mobile Android** para Play Store.

> *"A mão é o novo mouse." — o mercado estava à espera que alguém o fizesse por software, em português, com IA, e que o vendesse por valor — não por hardware.*

---

*Documento de estrategia — Luar Studio Angola · 2026. Todos os valores são estimativas de planeamento sujeitas a validacao. Licenças de componentes de codigo: permissivas (Apache 2.0 / MIT).*