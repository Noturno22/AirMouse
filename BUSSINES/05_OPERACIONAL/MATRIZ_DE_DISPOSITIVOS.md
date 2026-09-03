# Matriz de Compatibilidade de Dispositivos — Mãouse (AirMouse)

> Ficheiro **operacional** de recolha de dados. Preencher **uma linha por dispositivo testado**,
> em hardware real, **durante o beta fechado e o arranque**. A matriz é a base comercial da regra
> "Validado / Aceite / Não-validado" de `ANTIPADROES_E_RISCOS.md` §2, e a arma de prova para
> vendas B2B ("validámos no teu parque antes de te prometer").
> **Data:** 2026-09-01 · Autor: Luar Studio Angola · Estado: **EM RECOLHA — começar a testar.**
>
> **Área dedicada ao gargalo de hardware:** o procedimento de teste está na pasta **`HARDWARE/`**
> (`LAB.md` = protocolo, `PROBLEMAS_KNOWN.md` = registo de falhas, `CHECKLIST_VALIDACAO.md` =
> checklist por dispositivo). Esta matriz guarda os **resultados**; o LAB explica **como** testar.

---

## 0. Escala de veredito (usar só estes rótulos)

| Rótulo | Significado | Uso comercial |
|---|---|---|
| ✅ **Validado** | Experiência profissional (fps≥25, latência<80ms, sem cliques fantasma, gestos+snap OK) | Vender com confiança; base de contratos |
| 🟡 **Aceite** | Funciona com ressalvas documentadas | Vender com aviso; contrato com condição |
| ❌ **Não-validado** | Falha ou experiência inaceitável | Só trial free; nunca prometer |
| ⚠️ **Bloqueado** | Hardware/driver/perm impede o uso | Fora de contratos |

---

## 1. Desktop (Windows) — webcam

| Data | Device / Modelo | Webcam (res/fps) | CPU / GPU | Luz | FPS real | Latência | Cliques fantasma | Gestos (x/12+) | Snap | Veredito | Notas |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-01 | HP Notebook · Intel i3-5005U 2.0GHz · 8GB RAM · Win10 Home 64 | 640×480 / 30 | i3-5005U (sem GPU) | boa | **14.6** | inferência 48.3 ms | 0 | (selftest) | off | 🟡 **Aceite** | `main.py --frames 60 --no-preview --no-gui` · 0 glitches · FPS<25 (CPU fraco) — ver `§2` notebook CPU fraco |
| 2026-09-01 | HP Notebook · i3-5005U · HD 5500 (re-teste noite + `--gpu`) | 640×480 / 30 | i3-5005U + Intel HD 5500 (iGPU antiga) | fraca/noite | **11.9** (13.4 c/`--gpu`) | 78.5 / 67.3 ms | 0 | (selftest) | off | 🟡 **Aceite** | `--gpu` **indisponível** (cai para CPU: `NotImplementedError`) — HD 5500 não expõe OpenCL ao MediaPipe; ver `HARDWARE/PROBLEMAS_KNOWN.md` §1.3 · 0 glitches |
|  |  |  |  |  |  |  |  |  |  |  |  |  |

**Como testar (passo a passo):**
1. Instalar o build assinado (ou `python main.py --no-gui` para sm freezing).
2. Ambiente: luz normal (e repetir com luz baixa → ativa CLAHE).
3. Medir FPS mostrado no overlay/barra de estado.
4. Fazer os 12+ gestos; contar cliques fantasma em 2 min.
5. Testar snap (tecla `m`) sobre botões de uma app real.
6. Registar a linha com data + modelo + build version usado.

---

## 2. Desktop (Windows) — sem GUI/CPU fraco (fallback)

| Data | Device / Modelo | Webcam | CPU | Sem GPU (`--no-gui`)? | FPS | Veredito | Notas |
|---|---|---|---|---|---|---|---|
| 2026-09-01 | HP Notebook · i3-5005U · 8GB · Win10 | 640×480/30 | i3-5005U (sem GPU, sem NPU) | sim (`--no-gui`) | 14.6 | 🟡 **Aceite** | Funciona, mas abaixo do alvo 25 fps — **exige maior cuidado na venda a parques 100% sem GPU/NPU** |
|  |  |  |  |  |  |  |  |  |

---

## 3. Mobile (Android) — câmara frontal + ações nativas

| Data | Device / Modelo | Andr. versão | Câmara frontal | FPS | Gestos (x/12+) | Tap | Drag | Back/Home | Scroll | Veredito | Notas |
|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |  |  |

**Alvo: 5+ dispositivos low-end/médio** (risco de tela preta e performance — `PROGRESSO.md`).

---

## 4. Mobile (Android) — dispositivo com permissões invulgares (ex.: fabricantes asiáticos/chinês)

| Data | Device / Modelo | OEM Skin | Perms concedidas? | AccessibilityService ativo? | Veredito | Notas |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

---

## 5. Telemóvel → PC (modo remoto, companheiro)

| Data | Device móvel | PC alvo | WiFi ok? | Gesto→cursor PC | Veredito | Notas |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

---

## 6. Síntese (atualizar após cada 10 testes)

> *Atualizado 2026-09-01 — primeiro dispositivo testado (HP Notebook i3-5005U). Ainda muito
> longe do "go" institucional (≥5 ✅ por categoria). Contar ⚠️ "Bloqueado" e ❌ "Não-validado"
> como não comercializáveis.*

| Categoria | # Validado | # Aceite | # Não-validado | # Bloqueado | Cobertura p/ institucional? |
|---|---|---|---|---|---|
| Desktop webcam | 0 | 1 | 0 | 0 | ❌ Não (1 🟡 não chega) |
| Desktop CPU fraco | 0 | 1 | 0 | 0 | ❌ Não |
| Mobile low-end | 0 | 0 | 0 | 0 | ❌ Não (nada testado) |
| Mobile OEM invulgar | 0 | 0 | 0 | 0 | ❌ Não |
| Modo remoto | 0 | 0 | 0 | 0 | ❌ Não |

**Leitura imediata:** o produto **funciona num desktop fraco (i3, sem GPU)** — boa notícia de
robustez — mas **só a 11.9–14.6 fps** nessa classe (varia com luz/carga), e a iGPU antiga
(HD 5500) **não** acelera via `--gpu`. Para marketing institucional falta **muito
teste**. Próximos passos de recolha: (1) 1 dispositivo com GPU dedicada/NPU (medir se sobe a
25+ fps); (2) 5 telemóveis low-end Android; (3) 1 parque real em piloto.

**Regra de "go" institucional:** considerar o produto pronto para contratos B2B quando houver
≥ 5 dispositivos ✅ em cada categoria crítica (desktop webcam + mobile low-end), e um piloto
técnico validado num parque real.

### 6.1. Veredito "Go / Stop" institucional (atualizado com os dados de hoje)

> **Veredito atual: 🟥 STOP para contratos B2B/B2G institucionais. 🟢 GO para consumer**
> **(desktop/mobile) — mas SEM "trial com reembolso aberto": o experimento é a Free tier,
> não a devolução.** (Ver `ANTIPADROES_E_RISCOS.md` §5.)

| Decisão comercial | Estado | Base na matriz |
|---|---|---|
| 🟢 **Consumer desktop** (Pro €39,90) | **PODE vender** — sem reembolso em aberto | Funciona num desktop fraco |
| 🟢 **Consumer mobile** (IAP) | **PODE** beta/soft-launch | Aviso de performance; nada valida em low-end ainda |
| 🟡 **Piloto institucional TÉCNICO** (2–4 semanas no parque) | **PODE oferecer** — é exatamente o que falta | Usa o parque real do cliente como validação |
| 🔴 **Contrato institucional ANUAL** (€5–50k) | **NÃO pode assinar ainda** | Só 0-1 🟡 por categoria; <5 ✅; sem parque validado |
| ⚠️ **OEM/white-label** | **NÃO** | Requer prova de escala e parque estável |

**Por que "STOP institucional" é a decisão certa (não pessimismo):**
- O argumento comercial do Mãouse para institucional é *"validámos no teu parque antes de te
  prometer"* (`ANTIPADROES` §2.B). Hoje só temos 1 🟡 — não há parque validado.
- Um contrato institucional prometido a 500 computadores, com muitos sem GPU/NPU a ~15 fps,
  **destruiria a confiança** — o ativo mais valioso que temos.
- O **piloto técnico** é a ponte honesta: valida o parque real, gera a prova, e só depois
  fecha o contrato. **Isto transforma a nossa falta atual de dados em arma de venda** (não
  escondemos a fragilidade; usamo-la como processo de validação profissional).

**O que desbloqueia o "GO" institucional (checklist minimamente viável):**
1. [ ] ≥5 dispositivos ✅ em "Desktop webcam" (inclui ≥2 com GPU/NPU a 25+ fps).
2. [ ] ≥5 telemóveis ✅ em "Mobile low-end".
3. [ ] ≥1 piloto técnico completado num parque real (registo no §5/§6).
4. [ ] Auditoria WCAG + seguro RC agendados/fechados (`ESTRATEGIA` §2.2).
5. [ ] SLA + DPA operacionais (L2/L3).
6. [ ] **LAB de hardware a correr** na área `HARDWARE/` (LAB.md + PROBLEMAS_KNOWN.md +
    CHECKLIST_VALIDACAO.md) a gerar/encerrar linhas da matriz — a prova de que o gargalo de
    compatibilidade é tratado como processo, não promessa.

> **Em 1 frase:** hoje vendemos **consumer sem reembolso em aberto** (o "experimentar" é a
> **Free tier**, não a devolução) e **pilotos técnicos a instituições**; ainda **não** vendemos
> **contratos institucionais de longa duração** — isso vem quando a matriz mostrar ≥5 ✅ por
> categoria.

---

*Ficheiro operacional — Luar Studio Angola · 2026. Complementa ANTIPADROES_E_RISCOS.md §2.C.*
