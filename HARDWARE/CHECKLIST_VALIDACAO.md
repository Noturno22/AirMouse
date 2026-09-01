# Checklist de Validação por Dispositivo — Mãouse (AirMouse)

> Checklist operacional do `HARDWARE/` LAB. **Marcar com data + build version** a cada teste.
> Depois de completar, registar o resultado na `BUSSINES/MATRIZ_DE_DISPOSITIVOS.md` e as
> falhas em `HARDWARE/PROBLEMAS_KNOWN.md`. **NUNCA marcar ✅ sem a volta completa.**
> **Data:** 2026-09-01 · Autor: Luar Studio Angola · Estado: **pronto a usar.**

---

## A. Dados do dispositivo (preencher sempre)

- [ ] Fabricante / Modelo exato: ______
- [ ] CPU: ______ · GPU: ______ · RAM: ______
- [ ] Webcam (res/fps): ______ · OS (desktop): ______
- [ ] Android versão / OEM skin (mobile): ______
- [ ] Build version do Mãouse testado: ______ · Data: ______

---

## B. Desktop (Windows) — volta completa

- [ ] Câmara abre (sem erro)
- [ ] Motor entra (0 glitches no selftest)
- [ ] **FPS real** (estabilizado 30 s): ______ fps (alvo ✅ ≥25 · 🟡 ≥15)
- [ ] **Latência gesto→ação** <80 ms: medida ______
- [ ] **Gestos** — percorrer:
  - [ ] Mover cursor (mão aberta)
  - [ ] Clique esquerdo (pinça) e direito (pinça média)
  - [ ] Arrastar (punho / pinça segurar)
  - [ ] Scroll (2 dedos)
  - [ ] Volume (3 dedos) · Play/pausa (polegar)
  - [ ] Duas mãos (palmas/lupa)
  - [ ] Snap magnético (tecla `m`)
- [ ] **Cliques fantasma** em 2 min: contados ______ (alvo 0)
- [ ] **Luz baixa** (CLAHE) ativa e funcional
- [ ] **Voz** — wake word "Jarvis" + 1 comando responde
- [ ] **Fallback `--no-gui`/`--no-preview`** funciona (se aplicável)

**Veredito:** ✅ Validado · 🟡 Aceite · ❌ Não-validado · ⚠️ Bloqueado

---

## C. Mobile (Android) — volta completa

- [ ] App abre e câmara frontal arranca (sem tela preta)
- [ ] **FPS** (debug): ______ (alvo ≥30 ideal · ≥15 baixo)
- [ ] **Gestos 12+** detetados
- [ ] **Ações nativas** (todas, em device REAL):
  - [ ] Tap (clique) · [ ] Drag (arrastar)
  - [ ] Back / Home / Recents
  - [ ] Scroll · [ ] Copy/Paste (se aplicável)
- [ ] **AccessibilityService** ativo e concedido
- [ ] Permissões usadas justificadas (sem `WRITE_SETTINGS` morto)

**Veredito:** ✅ Validado · 🟡 Aceite · ❌ Não-validado · ⚠️ Bloqueado

---

## D. Modo remoto (telemóvel → PC, companheiro)

- [ ] Telemóvel e PC na mesma rede
- [ ] Gesto no telemóvel move o cursor PC
- [ ] Tap/clique remoto funciona
- [ ] Latência aceitável

**Veredito:** ✅ / 🟡 / ❌

---

## E. Pós-teste (obrigatório)

- [ ] Registado na `BUSSINES/MATRIZ_DE_DISPOSITIVOS.md` (Data/Modelo/Veredito)
- [ ] Falhas copiadas para `HARDWARE/PROBLEMAS_KNOWN.md`
- [ ] Síntese `MATRIZ §6` atualizada (contagens)

---

*Checklist — Luar Studio Angola · 2026. Área dedicada ao gargalo de compatibilidade.*
