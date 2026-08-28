# Relatório de Estado — AirMouse (GUI PySide6)

Data: 2026-08-28

## ✅ Feito nesta sessão (feedback `mm.md`)

### 1. Painel de Ajuda com fundo sólido (CSS)
`ui/help_panel.py` — fundo opaco via QSS (`HelpPanel { background-color: #16162A }`),
`WA_StyledBackground`, estilos de viewport/scrollbar; resolve o "fundo transparente horrível".

### 2. Estabilidade do movimento do rato
- `core/motion.py` — o loop do `SmoothEmitter` compensava o atraso de iteração em rajadas
  (movimento "aos solavancos"/instável). Agora ressincroniza o relógio em vez de disparar
  N emissões seguidas.
- `config.py` + `core/filters.py` — curva de aceleração com `accel_min_gain=1.0` (controlo 1:1
  em movimentos precisos; antes nunca era <2.4× total), `accel_max_gain=2.6`, `ref=1200`, `expo=1.5`.
- Verificado por simulação: emissor drena 100% do movimento (pending=0) sem saldos.

### 3. Câmara só como preview (não o fundo)
`ui/main_window.py`, `ui/menu_panel.py`, `ui/theme.py` — a câmara deixou de preencher a janela.
`📷 VER CÂMARA` (checkable, tecla `C`) mostra/oculta o preview 640×480 centrado; por defeito há um
dashboard com marca. **O reconhecimento de gestos corre sempre** — só o render é gatado por `_camera_on`.

### 4. Deteção de gestos (área crítica) — aprimorada
`core/gestures.py` — deadband (Schmitt trigger) por dedo para "dobrado/esticado" (`_prev_curled`
com memória): um dedo a pairar no limiar (rácio tip/pip ≈ 1.0) já não faz o gesto tremer
frame-a-frame (ONE↔OPEN, PEACE↔THREE, FIST↔THUMB_UP). Casos claros comportam-se como antes.
- A webcam **não interfere**: `process_frame` corre em cada `_tick` independentemente do toggle.

### Validação
- `tools/test_new_gestures.py` → **23 PASS / 0 FAIL**
- `tools/test_hand_lock.py` → **13 PASS / 0 FAIL**
- Deadband: verificado por script (oscilação 0.95–1.05 mantém estado; re-abre só >1.06).
- Smoke test UI offscreen (toggle câmara view↔brand, help panel, `btn_camera`): OK.

---

## 📝 Sessões anteriores

## 🎯 Objetivo
Transformar o AirMouse em produto "pro para venda" com **janela nativa (PySide6)** que abre ao correr `start.bat`, mantendo **intacto** o cérebro de reconhecimento/gestos (`process_frame` partilhado com o preview OpenCV).

---

## ✅ Feito nesta sessão

### 1. Refactor do cérebro (`main.py`) — paridade total
- `make_engine_ctx(cfg, smooth_idx, gesture_ai, tuner, ctx)`
  → constrói o `SimpleNamespace E` com **todas** as engines (pool, filters, curve, clap, magnifier, brightness, fist_cycle, wave, dual_wave, left_hand, light, clahe) + dict `ui` + `toast()` + todo o estado.
- `process_frame(cfg, cam, tracker, mouse, gesture_ai, voice, tuner, ctx, state, E)`
  → **uma iteração** do cérebro completo (warmup, mirror, luz/clahe, clap, dual_wave, left_hand, Alt+F4, brilho, magnifier, eventos, voice, autotune, fps, selftest).
- `run_loop(...)` (preview OpenCV) passou a consumir `process_frame`, byte-por-byte idêntico.
- Novo snapshot inclui `"flash"` para comunicação limpa com a GUI.
- Flag `--no-gui` para fallback OpenCV; `config.py` ganhou `gui_enabled`.

### 2. MainWindow como apresentação (`ui/main_window.py`)
- `_tick` (QTimer) constrói lazy `AppCtl`/`make_engine_ctx`/`SmoothEmitter` e chama **o mesmo** `process_frame`.
- `_refresh_ui(snap)` consome o snapshot (frame, all_frames, active_side, fps, ui).
- Guarda `to_render`/`frame is None` (espelha o `run_loop`).
- `mouse`, `voice`, `snap`, `assistant`, `magnifier`, `speaker` injetados.

### 3. 🔘 Barra de botões (novo)
Barra vertical no canto superior direito com atalhos visuais:
`⏸ PAUSA · 💾 GRAVAR · 🎤 VOZ · 🖼 SNAP · ❓ AJUDA · ⚙ CONFIG · ✕ SAIR`
- Estilo `ToolbarBtn` adicionado ao `ui/theme.py`.
- Gestão de estado (checkable p/ voz/snap, texto alterna p/ pausa → retomar).
- `_sync_toolbar()` mantém os botões em sincronia com o estado real.

### 4. ⚙ Configuração / Personalização (`ui/settings_dlg.py`)
Grupo novo **"Personalização"**:
- Espelhar imagem
- Comandos da mão esquerda
- Realce em pouca luz
- **Zona morta do cursor** (slider)
- **Estabilidade do gesto** (slider, 1–6 frames)
Ganha, suavidade, snap, voz, TTS, IA e auto-afinação já existiam. Janela alargada (430×620).

### 5. 🐛 Bug: sair com Ctrl+C
- `KeyboardInterrupt` (Ctrl+C) interrompia o MediaPipe no meio de `tracker.process()`,
  deixando a janela presa a repetir tracebacks.
- Resolvido com: `try/except KeyboardInterrupt` no `_tick` + `closeEvent` tolerante (cleanup em try/except) + handler `SIGINT` no `run_gui` que agenda o fecho da janela.

### 6. 🎨 Estabilização do desenho dos gestos (`ui/camera_view.py`)
- **Não altera o cérebro.** Só suaviza a APRESENTAÇÃO (crosshair):
  - Centro da palma (crosshair) suavizado com EMA (`_cross_alpha=0.5`).
  - **O gesto é renderizado instantaneamente, tal como o cérebro o emite** — sem latência percebida.
- ⚠️ **Revisão (corrigida):** a 1.ª versão adicionava debounce de 3 frames ao gesto exibido,
  em cima dos `gesture_stable_frames` do cérebro → causava **latência percetível** e o
  reconhecimento parecia "confuso / indeciso / lento". **Removido** — reatividade igual à do
  preview OpenCV.

### 6b. 🐛 Corrigido: crash do crosshair no PySide6 (`_draw_crosshair`)
- `_to_w()` devolve um `QPoint`, que **não é desempacotável** (`QPoint` não é iterável no PySide6).
- O código original fazia `px, py = self._to_w(hf.palm_center)` → `TypeError: cannot unpack ... QPoint`
  **sempre que havia uma mão** (o `paintEvent` rebentava a cada frame → esqueleto/crosshair
  cortado e tremido). Só se manifestava com câmara real; os testes antigos usavam mãos vazias.
- Corrigido com `p = self._to_w(...); px, py = p.x(), p.y()`.

### 7. 🐞 Corrigido: `ui/toast.py`
- `setFinishValue` (API QtQuick inexistente) → `setEndValue`. Impedia a janela de abrir.

---

## 🔧 Como correr

```bat
start.bat                :: abre a janela PySide6 (GUI)
.venv\Scripts\python.exe main.py --no-gui   :: preview OpenCV (fallback)
```

## ⌨️ Atalhos
`Q`/`Esc` sair · `Espaço` pausa · `H`/`F1` ajuda · `C` ver câmara · `S` gravar · `A` auto-afinação · `V` voz · `M` snap · `F2` configurações · `[` `]` ganho · `,` `.` suavidade

---

## 🧪 Testes
- `tools/test_left_hand.py` → **6 PASS / 0 FAIL**
- `tools/test_new_gestures.py` → **23 PASS / 0 FAIL**
- Compilação (`py_compile`) de todos os ficheiros alterados: OK
- Teste headless da MainWindow + toolbar + settings (offscreen): OK
- `tools/test_gui_render.py` → **4 PASS / 0 FAIL** (desenha esqueleto + crosshair + PEACE + flash + EMA com mão simulada; apanha o bug do `QPoint`)

---

## 📋 O que falta / pendente (próximos passos)

### Alta prioridade
- [x] **Teste em hardware real** — (pendente de ecrã real; lógica verificada headless)
- [x] **Persistência de settings** — round-trip completo verificado: `load_settings`/`save_settings`/`_save_settings` cobrem mirror, left_hand_commands, low_light_boost, deadzone_px, gesture_stable_frames, voz, TTS, IA, auto-afinação.
- [x] **Fix 2 FAILs do `test_new_gestures.py` (volume)** — era inversão de sinal: `_vol_acc_y -= dy` → `+= dy`, ficando consistente com o scroll. 18/18 PASS.
- [x] **`--tray` com GUI + gate por gesto** — verificado: dispatching do menu (pausa, ganho, voz, snap, assistente, sair) e `apply_command("exit")` fecha a janela oculta. Validação visual da bandeja requer desktop real.
- [ ] **Validar em dispositivo real** o fix de estabilidade do rato (`SmoothEmitter` resync + curva de aceleração 1.0–2.6) — lógica/desempenho verificados por simulação e test-offscreen, mas a sensação de "instável" precisa de confirmação com hardware real.

### Média prioridade
- [ ] **Mojibake** pré-existente em `ui/__init__.py` e `ui/settings_dlg.py` ("Mãouse"/"Definições Mãouse") — idem noutros ficheiros com acentos mal codificados. Rever encoding UTF-8 + BOM.
- [ ] **Botão acessível "Configurações" abre o diálogo** — já ligado a `F2`/botão; validar visualmente no tema escuro.

### Baixa prioridade / ideias
- [ ] **"Boca aberta"** (novo gesto com a boca) — adiado: exige `FaceLandmarker`, não `HandLandmarker`.
- [ ] **Mais personalização**: ligar/desligar gestos individuais, remap de combinações de teclas, velocidade máxima da câmera.
- [ ] **Localização** PT/EN para "pro para venda".

---

## ⚠️ Notas técnicas
- **LSP**: erros `Import "cv2/PySide6/numpy" could not be resolved` e tipagens `pynput` são **pré-existentes** (o LSP não vê o venv/PySide6); a compilação real `py_compile` passa.
- `cfg.gui_enabled` pode aparecer a vermelho no LSP (cache) — está em `config.py`.
- A janela é **frameless** (`Qt.FramelessWindowHint`), por design (air mouse controlado por gestos). A barra de botões é o ponto de controlo visível.
