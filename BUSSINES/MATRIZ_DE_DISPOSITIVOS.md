# Matriz de Compatibilidade de Dispositivos — Mãouse (AirMouse)

> Ficheiro **operacional** de recolha de dados. Preencher **uma linha por dispositivo testado**,
> em hardware real, **durante o beta fechado e o arranque**. A matriz é a base comercial da regra
> "Validado / Aceite / Não-validado" de `ANTIPADROES_E_RISCOS.md` §2, e a arma de prova para
> vendas B2B ("validámos no teu parque antes de te prometer").
> **Data:** 2026-09-01 · Autor: Luar Studio Angola · Estado: **EM RECOLHA — começar a testar.**

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
| 2026-09-01 | ex.: Dell XPS 15 | 720p / 30 | i7 + integrada | boa | 28 | <80ms | 0 | 12/12 | OK | ✅ | — |
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

| Categoria | # Validado | # Aceite | # Não-validado | # Bloqueado | Cobertura p/ institucional? |
|---|---|---|---|---|---|
| Desktop webcam |  |  |  |  |  |
| Desktop CPU fraco |  |  |  |  |  |
| Mobile low-end |  |  |  |  |  |
| Mobile OEM invulgar |  |  |  |  |  |
| Modo remoto |  |  |  |  |  |

**Regra de "go" institucional:** considerar o produto pronto para contratos B2B quando houver
≥ 5 dispositivos ✅ em cada categoria crítica (desktop webcam + mobile low-end), e um piloto
técnico validado num parque real.

---

*Ficheiro operacional — Luar Studio Angola · 2026. Complementa ANTIPADROES_E_RISCOS.md §2.C.*
