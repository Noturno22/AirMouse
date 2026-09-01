# Problemas Conhecidos de Hardware — Mãouse (AirMouse)

> **Registo de conhecimento acumulado** do `HARDWARE/` LAB. Cada linha é uma falha,
> limitação ou comportamento observado em dispositivo real — para **não re-testar** e para
> **informar a matriz** (Validado/Aceite/Não-validado) e os bloqueadores técnicos.
> **Data:** 2026-09-01 · Autor: Luar Studio Angola · Estado: **EM REGISTO.**

---

## 0. Legenda

| Marcador | Significado |
|---|---|
| 🔴 Bloqueador | Impede a venda numa categoria |
| 🟠 Limitação | Funciona, mas com ressalvas documentadas |
| ✅ Resolvido | Corrigido em build; registar o build fix |
| ❓ A investigar | Observado, causa ainda por determinar |

---

## 1. Desktop (Windows)

### 1.1. CPU sem GPU/NPU → FPS abaixo do alvo 🟠 Limitação

| Campo | Valor |
|---|---|
| **Sintoma** | FPS ≤15 em CPU de baixo custo sem acelerador de IA |
| **Dispositivo (confirmado)** | HP Notebook · Intel Core i3-5005U (2.0 GHz) · sem GPU dedicada · 8GB · Win10 Home |
| **Dados** | 14.6 fps · inferência 48.3 ms · 0 glitches · câmara 640×480@30 (teste real 2026-09-01) |
| **Impacto matriz** | 🟡 **Aceite** (funciona, mas abaixo dos 25 fps) |
| **Causa provável** | Inferência MediaPipe em CPU (TFLite XNNPACK sem GPU) + pipeline de frame |
| **Mitigação** | `--no-gui` (liberta CPU do render); reduzir resolução da câmara; futuro: usar NPU/GPU se disponível |
| **Ação comercial** | Vender com aviso "requer bom CPU"; **não** ✅ em parcos 100% sem GPU |
| **Para validar** | Repetir em outro CPU fraco; testar com `--gpu` | ❓ a investigar |

### 1.2. Nenhum dispositivo de GPU dedicada/NPU testado ainda 🔴 A investigar

- Falta medir se **desktop com GPU/NPU dedicada** sobe aos 25+ fps (categoria ✅ para
  marketing/contratos). Prioridade nº1 do LAB (`LAB.md` §4).

---

## 2. Mobile (Android)

### 2.1. Ações nativas NÃO funcionam em device real 🔴 Bloqueador

| Campo | Valor |
|---|---|
| **Sintoma** | `NativeModules.TouchController?.tap()` faz **no-op silencioso** (via optional chaining) |
| **Causa** | Falta implementar módulos Touch/Keyboard/System + `AccessibilityService` no Manifest (`mobile/android`) |
| **Estado** | Auditar: bloquear nº4 de `PRONTIDAO_PARA_VENDA` — **por implementar** |
| **Impacto** | O core valor "controlar o telemóvel com a mão" não funciona em device real |
| **Plano** | Implementar no S2 do `PLANO_DE_EXECUCAO_90_DIAS` |

### 2.2. Permissões sensíveis declaradas sem uso ⚠️ Risco de rejeição Play

| Campo | Valor |
|---|---|
| **Sintoma** | `WRITE_SETTINGS` / `SYSTEM_ALERT_WINDOW` declaradas em `app.json`, sem código que as justifique |
| **Impacto** | Risco de rejeição Google Play (policy) |
| **Ação** | Remover se não usadas, ou justificar/documentar quando servirem |

### 2.3. Low-end: risco de tela preta/performance ❓ a investigar

- Já foram corrigidos múltiplos crashes do frame processor (`PROGRESSO.md`). **Otimização em
  low-end ainda pendente.** Falta testar em 5+ telemóveis low/mid-end (LAB prioridade 🔴 2).

---

## 3. Registo para novas observações

> Ao registar uma nova falha: copiar o template, preencher, e **etiquetar com a prioridade do
> impacto em vendas** (bloqueador/limitação/resolvido). Depois atualizar a
> `BUSSINES/MATRIZ_DE_DISPOSITIVOS.md` e, se afetar contratos, o `ANTIPADROES_E_RISCOS.md`.

```
### X.Y. <Título> <marcador>
| Campo | Valor |
|---|---|
| **Sintoma** |  |
| **Dispositivo** |  |
| **Dados** |  |
| **Impacto matriz** | ✅/🟡/❌/⚠️ |
| **Causa** |  |
| **Mitigação** |  |
| **Ação comercial** |  |
| **Para validar** |  |
```

---

*Registo de conhecimento — Luar Studio Angola · 2026. Área dedicada ao gargalo de compatibilidade.*
