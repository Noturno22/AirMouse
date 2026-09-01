# LAB de Compatibilidade de Hardware — Mãouse (AirMouse)

> **Área dedicada ao gargalo de compatibilidade.** O Mãouse depende de hardware alheio
> (webcams, CPUs, GPUs/NPUs, câmaras de telemóvel) que varia muito. Este `HARDWARE/` é o
> "laboratório" — procedimento, registo de falhas e checklists para resolver o pormenor com
> rigor. Base comercial em `BUSSINES/MATRIZ_DE_DISPOSITIVOS.md` e
> `BUSSINES/ANTIPADROES_E_RISCOS.md` §2.
> **Data:** 2026-09-01 · Autor: Luar Studio Angola · Estado: **ATIVO — em recolha.**

---

## 0. Objetivo do LAB

Gerar **dados reais de compatibilidade** que sustentem:
- a **matriz Validado/Aceite/Não-validado** (`MATRIZ_DE_DISPOSITIVOS.md`) — base das vendas;
- os **5 bloqueadores técnicos** (`PRONTIDAO_PARA_VENDA`) — especialmente o nº4 (mobile
  low-end) e a performance em CPUs sem GPU/NPU;
- o **piloto técnico** institucional ("validámos no teu parque antes de te prometer").

> **Resultado prático:** mais dispositivos testados = mais ✅ na matriz = mais contratos B2B
> legitimamente vendidos e menos reembolsos (política D7).

---

## 1. O que o LAB mede (métricas-padrão)

| Métrica | Objetivo | Como medir | Alvo |
|---|---|---|---|
| **FPS real** | Fluxo de inferência | Overlay/barra de estado; ou `main.py --frames N --no-preview --no-gui` → relatório selftest | ≥25 (Validado) · ≥15 (Aceite) |
| **Latência gesto→ação** | Capacidade de resposta | `tools/test_click_latency.py` + cronómetro | <80 ms |
| **Cliques fantasma** | Fiabilidade das pinças | 2 min de gestos; contar falsos cliques | 0 |
| **Gestos (x/12+)** | Suporte completo | Percorrer todos os gestos | 12/12 |
| **Snap** | UI Automation | Tecla `m` sobre botões reais de apps | OK |
| **Luz baixa** | Robustez ambiental | Acender/escurecer; ver CLAHE ("LUZ BAIXA") | funcional |
| **Áudio/voz** | Wake word + TTS | Dizer "Jarvis"; ver se responde | ok |
| **Mobile FPS** | Performance low-end | App mostra FPS (debug) | ≥30 ideal · ≥15 baixo |
| **Mobile ações nativas** | Tap/drag/back/scroll | Executar em device real | todos a funcionar |

---

## 2. Procedimento-padrão por dispositivo (SOP)

> Fazer **uma volta completa** por dispositivo (30–40 min). NUNCA marcar ✅ sem a volta completa.

1. **Registar o hardware** — `dxdiag` (CPU/GPU/Webcam/RAM/OS) ou `Get-CimInstance` no mobile; anotar modelo exato.
2. **Ambiente de luz** — testar com luz normal e depois fraca.
3. **Arranque** — abrir a app/`.exe`; confirmar que a câmara abre e o motor entra (0 glitches).
4. **Medir FPS** — deixar estabilizar 30s antes de anotar.
5. **Percorrer os 12+ gestos** — mover, clicar, arrastar, scroll, volume, 2 mãos, snap.
6. **Contar cliques fantasma** — 2 min de uso intenso.
7. **Testar voz** (se desktop) — wake word + comando.
8. **Mobile** — validar ações nativas (tap/drag/back/home/scroll) uma a uma.
9. **Registar na matriz** (`BUSSINES/MATRIZ_DE_DISPOSITIVOS.md`) com data + build version.
10. **Registar falhas/observações** em `PROBLEMAS_KNOWN.md` (se houver).

---

## 3. Estrutura do LAB

| Ficheiro | Função |
|---|---|
| **`LAB.md`** (este) | Metodologia-SOP do teste |
| **`PROBLEMAS_KNOWN.md`** | Registo de falhas por dispositivo/driver/perm — conhecimento acumulado que evita re-testar |
| **`CHECKLIST_VALIDACAO.md`** | Checklist por dispositivo (desktop/mobile) p/ marcar a volta completa |
| `BUSSINES/MATRIZ_DE_DISPOSITIVOS.md` | Onde os resultados são **registados** (matriz comercial) |

---

## 4. Prioridade de teste (a ordem que desbloqueia venda)

| Prioridade | Perfil | Porquê |
|---|---|---|
| 🔴 1 | **Desktop com GPU dedicada/NPU** | Confirmar se sobe a 25+ fps → desbloqueia ✅ em marketing/contratos |
| 🔴 2 | **Telemóveis Android low-end/médio (5+)** | Bloqueador nº4; risco de tela preta; base do volume mobile |
| 🟠 3 | **Desktop CPU fraco (sem GPU)** | Já sabemos: ~15 fps (🟡) — confirmar em mais 1–2 modelos |
| 🟠 4 | **Android OEM invulgar (chinês)** | Permissões/perm invulgares; Ass. Service varia |
| 🟡 5 | **Modo remoto telemóvel→PC** | Diferencial PC↔móvel; validar o fluxo |

> **Regra de teste:** cada resultado de teste **conta para a matriz e para o known-issues**.
> Sempre em hardware real, nunca simulado.

---

*LAB — Luar Studio Angola · 2026. Área dedicada ao gargalo de compatibilidade.*
