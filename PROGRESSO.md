# AirMouse — Estado do Projeto

> **Continuar daqui mais tarde.** Este ficheiro guarda tudo o que foi decidido e feito, e o que falta.

## O que é

Projeto novo dentro de `DEV\JARVIS\airmouse` — controla o rato do PC com a mão via webcam.
Criado porque o barehands parece amador; este usa técnicas profissionais para precisão:

1. **One Euro Filter** — elimina tremor sem lag perceptível
2. **Gesto de ativação** — mão aberta = modo mover; mão longe/ausente = rato físico normal
3. **Histerese na pinça** — dois limiares (liga aos 0.38, desliga aos 0.55) evitam cliques duplos acidentais
4. **Freeze nos cliques** — cursor congelado ~130 ms durante cliques/transições
5. **Controlo relativo tipo touchpad** (não espelho absoluto) — menos cansativo, mais preciso

## Decisões tomadas

| Ponto | Escolha |
|---|---|
| Stack | Python 3.14 + MediaPipe 1.0.1 + OpenCV + pynput |
| Controlo | Relativo (touchpad) com ganho ajustável (`move_gain`) |
| Gestos | Básico: pinça=clique esq., punho=arrastar, 2 dedos (index+médio)=clique dir. |
| Local | `C:\Users\Luar Studio Angola\Desktop\DEV\JARVIS\airmouse` |
| Modelo | `hand_landmarker.task` (MediaPipe Tasks API), download automático na 1ª execução |

### Mapeamento de gestos (implementado em `core/gestures.py`)

- Prioridade de classificação: **punho > pinça > 2 dedos > mão aberta**
- Punho = 4 dedos encolhidos (comparação distância ponta-vs-PIP ao pulso, invariante à rotação)
- Pinça = distância polegar-index normalizada pela escala da mão (invariante à distância)
- Gesto precisa estabilizar **3 frames** antes de mudar de estado
- Mão demasiado longe (`min_hand_scale_px = 55`) → gesto NONE → cursor não mexe
- Perder a mão durante arrasto → **solta o botão automaticamente**

## Ficheiros já criados (CÓDIGO COMPLETO)

```
airmouse/
├── config.py            ← TODOS os parâmetros de afinação estão aqui
├── main.py              ← loop tempo real, câmara, overlay, voz/IA/auto-afinação, selftest (--frames N)
├── requirements.txt     ← mediapipe==1.0.1, opencv-python, numpy, pynput, vosk, sounddevice
├── setup.bat            ← instalação única (cria .venv + instala deps)
├── start.bat            ← arranque rápido (passa argumentos ao main.py)
├── README.md
├── PROGRESSO.md
├── core/
│   ├── __init__.py
│   ├── filters.py       ← One Euro Filter + FilterPair2D
│   ├── tracker.py       ← HandLandmarker (VIDEO mode) + download modelo
│   ├── gestures.py      ← máquina de estados de gestos + eventos (híbrido com IA)
│   ├── gesture_ai.py    ← MLP numpy de classificação de gestos
│   ├── voice.py         ← Vosk offline PT + wake word + grammar restrita
│   ├── nlu.py           ← intenções em português + fallback Ollama
│   ├── autotune.py      ← auto-afinação adaptativa de filtros/ganho
│   └── mouse_ctl.py     ← pynput + DPI awareness + limites do ecrã
├── tools/
│   └── train_gesture_ai.py  ← gera dados sintéticos, treina e valida o MLP
└── models/              ← hand_landmarker.task ✓ | gesture_mlp.npz ✓ | vosk-model-small-pt-0.3 ✓
```

## ✅ Estado atual (2026-08-25)

### V3 PROFISSIONAL (implementado e testado)
1. **Movimento profissional**: `core/motion.py` — emissor a 180 Hz com acumulador
   sub-pixel + predição lead (`predict_ms=40`) · aceleração exponencial (`accel_expo=1.7`)
   · mouse_ctl com acumuladores fracionários.
2. **Snap magnético**: `core/snap.py` — UI Automation (4 Hz) deteta clicáveis reais;
   atrai o cursor perto de botões/campos; clique assistido usa o ponto exato do alvo.
   Tecla **m** / voz "ativa/desativa o snap".
3. **Duas mãos**: `core/twohand.py` — HandPool (redundância: troca de mão dominante sem
   salto, reset de filtros) · ClapDetector (palmas → abre/fecha assistente 3D barehands,
   Chrome app-mode; fecha por WM_CLOSE) · MagnifierCtl (2 mãos abertas = Lupa do Windows,
   afastar amplia, juntar reduz, sair = tirar mãos, Win+Esc força).
4. **Voz híbrida**: Vosk só wake word ("jarvis"/"jarbas") + **faster-whisper small int8**
   transcreve comandos naturais (lazy load após 1º wake) + NLU estendida
   (assistente/lupa/snap) + respostas faladas.
5. **TTS neural**: `core/tts.py` — Piper pt_BR-faber-medium (~60 MB descarrega na 1ª vez),
   fallback SAPI5; fila de fala.
6. **Arranque automático**: `install_startup.bat`/`uninstall_startup.bat` (schtasks
   ONLOGON, pythonw --tray) + `core/tray.py` (ícone pystray: pausar/voz/preview/sair)
   + mutex single-instance.
7. **Luz baixa**: `core/light.py` histerese <40/>60 → CLAHE LAB no frame +
   tentativa de exposição da câmara.
8. **Gestos novos integrados**: três dedos = volume (media keys), polegar cima =
   play/pausa; IA retrainada para **7 classes** (100% val sintética); config ganhou
   `volume_deadzone_px`.
9. **Testes**: `tools/test_v3.py` **17/17 PASS**. Selftest com câmara pendente
   (câmara indisponível nesta sessão — correr `start.bat` ao vivo).

### TRAVA DE MAO (intent detection lite, estilo AirTouch)
1. **`core/hand_lock.py`** (`HandLock`) — com 2+ maos em cena segue sempre a mao do
   controlador (a mais proxima do ultimo ponto controlado); intrusos longe desse ponto
   nao roubam o controlo; apos `hand_lost_grace_frames` (10) qualquer mao pode adquirir.
   Com 1 mao: comportamento anterior intacto.
2. Tracker agora com `num_hands=2` (config `num_hands`; flag `--single-hand` reverte).
3. Testes `tools/test_hand_lock.py`: **13/13 PASS** (inclui caso apanhado pelo teste:
   unica mao intrusa respeita a graca antes de assumir).

### COLETA DE DADOS REAIS + RETREINO DA IA
4. **`tools/collect_gestures.py`** — janela interativa: teclas 1-5 escolhem gesto
   (OPEN/PINCH/PINCH_MID/FIST/PEACE), gravacao por frames com gate de qualidade,
   z/c/s/Q; modo automatico `--frames N --class X --no-preview` para testes.
   Grava `data/real_landmarks.npz` (X=Nx21x2 px, y=classe).
5. **`tools/train_gesture_ai.py`** estendido:
   - `--real <npz>` mistura sintetico+reais; split estratificado 85/15;
     validacao REAL reportada epoca a epoca + matriz de confusao real.
   - Backup automatico do modelo anterior → `models/gesture_mlp_prev.npz`
     (reverter = copiar de volta); aviso se acc real <90%.
   - Parametrizado `--per-class/--epochs/--real-copies/--out`.
   - Corrigidos 2 bugs apanhados no smoke test: `epochs` ignorado (hardcoded 24) e
     copia para core/ sobrescrita quando `--out` temporario (agora so na default).
   - Smoke test `tools/test_retrain_smoke.py`: **6/6 PASS** (pipeline completo com
     "reais" falsos: split, treino, backup, inferencia 5/5).

### EXECUTAVEL (.exe)
6. **`build.bat`** + `airmouse.spec` + `requirements-build.txt` (PyInstaller onedir).
   - Paths congelados: `_base_dir()/_abs_path()` em main.py — settings.json e modelos
     junto ao exe (dist\AirMouse\models copiado pelo build.bat).
   - NOTA: `matplotlib` e dependencia declarada do mediapipe; o primeiro build falhou
     porque a spec a excluia. Ja nao excluida; nada a instalar a mais.
   - Build OK (~395 MB). Exe congelado testado sem camara: importa mediapipe/vosk,
     carrega IA e modelos ao lado do exe, sai com erro limpo de camara
     (camara indisponivel nesta sessao — validar ao vivo com start.bat).

## Estado anterior (2026-08-24)

### Motor de precisão V2 + garantia de qualidade por pipeline de agentes
1. **Implementador sénior** construiu o motor V2:
   - **Palm-center** como ponto de controlo (média lm 0,5,9,13,17) — zero saltos ao clicar/arrastar
   - **Curva de aceleração** smoothstep (1.2→3.0 @ 1400 px/s): preciso devagar, rápido a varrer
   - **Pinça index = botão touchpad** (toque=clique · segurar+mover=arrastar); **pinça médio = clique direito**; paz = **scroll** com acumulador fracionário; punho = drag alternativo
   - **Câmara em thread dedicada (MJPG) + sequenciador** — inferência só sobre frames novos
   - **Anti-glitch "modo rápido confirmado"** — rejeita teletransportes sem travar varrimentos
2. **Verificador independente**: 7 verificações → PASS total (settings corrompido tolerado, acumulador de scroll provado conservativo)
3. **Revisor sénior**: encontrou **1 crítico + 4 importantes** — botão preso se pausa durante drag; corrida na thread da câmara; anti-glitch travava varrimentos rápidos; voz dessincronizava drag; frames duplicados processados
4. **Implementador (TDD)**: 16 testes reproduziram os defeitos (RED), corrigiu os 11 pontos, GREEN 16/16
5. Verificação final própria: `--frames 120 --no-preview` → OK · fps honestos pós-dedup · inferência ~39 ms · 0 glitches

### INTEGRAÇÃO IA COMPLETA (100% local/offline)
1. **IA de gestos** (`core/gesture_ai.py` + `tools/train_gesture_ai.py`)
   - MLP numpy (40→96→48→5 softmax, ~35 KB), treino com 30k mãos sintéticas paramétricas
   - Normalização invariante a rotação/escala; augmentação com ruído até σ=0.05 e outliers
   - Validação: **100% accuracy** sintética; integração testada 5/5 gestos com conf 1.000
   - Híbrido: conf < `ai_confidence_min` (0.72) → fallback para regras geométricas
   - Modelo em `models/gesture_mlp.npz` + cópia em `core/`
2. **Comandos de voz offline** (`core/voice.py`) — Vosk small-pt + sounddevice
   - Wake word "jarvis" com alias "jarbas" (jarvis não está no vocabulário do modelo PT!)
   - Grammar restrita (mais preciso); variantes acentuadas incluídas (rápido/botão...)
   - Janela de escuta de 8 s após wake word; tecla V liga/desliga; `--voice-always` opcional
   - Modelo descarregado automaticamente (~49 MB) na 1ª execução
3. **NLU** (`core/nlu.py`) — parser de intenções PT (regex + difflib fuzzy), 11/11 testes
   - Fallback opcional para Ollama local (localhost:11434, `llama3.2:3b`, timeout 2.5 s) — sem dependências novas (urllib)
4. **Auto-afinação adaptativa** (`core/autotune.py`)
   - Observa tremor (EMA velocidade vs jitter) → ajusta `filter_min_cutoff`/`beta` dentro de limites seguros
   - Trim de ganho ±20% baseado em reversões/twitch; tecla A liga/desliga; persiste ao sair
5. **main.py integrado** — overlay mostra IA conf%, estado da voz, toasts de comandos; flags `--no-ai --no-voice --no-autotune --voice-always`

### Testes executados
- Sintaxe OK em todos os ficheiros novos/editados
- NLU: 11/11 intenções corretas (inclui casos negativos)
- Selftest completo: `main.py --frames 90` → 17.3 fps, inferência 53.5 ms, 0 glitches, IA ativa, voz ativa (mic Realtek detetado)
- Integração gestos: 5/5 classes classificadas com conf 1.000; eventos left_down/left_up OK

### Estado anterior (pré-IA)
- Dependências instaladas no `.venv` (Python 3.14.6): mediapipe 1.0.1, opencv 5.0.0.93, numpy 2.5.2, pynput 1.8.2, vosk, sounddevice 0.5.6
- API MediaPipe 1.0 verificada — `HandLandmarker`, `RunningMode.VIDEO`, `detect_for_video` OK
- Thresholds de confiança baixados para 0.5 (mais tolerante a câmaras de má qualidade)

## Falta fazer

1. **Teste real com o utilizador (v3):** `start.bat` — validar: movimento sedoso + snap
   (aproximar cursor de um botão), palmas → assistente 3D, duas mãos abertas → lupa,
   "Jarvis" + comando natural, voz Piper a responder, ícone na bandeja.
2. **Arranque automático:** correr `install_startup.bat` e reiniciar sessão para confirmar.
3. Coletar dados reais + retreinar IA com 7 gestos: `tools\collect_gestures.py`
   (agora suporta 1-7) → `tools\train_gesture_ai.py --real data\real_landmarks.npz`.
4. Testar o exe ao vivo (reconstruir com build.bat para incluir módulos v3).
5. Opcional: instalar Ollama para linguagem natural completa (fallback do NLU).

## Afinação (tudo em `config.py` + hotkeys em tempo real)

| Parâmetro | Default | Efeito |
|---|---|---|
| `move_gain` | 2.0 | ↑ = cursor mais rápido (teclas `[` `]`) |
| `accel_min_gain` / `accel_max_gain` | 1.2 / 3.0 | curva de aceleração (preciso devagar, rápido a varrer) |
| `accel_ref_speed` | 1400 | velocidade da mão (px/s) que atinge ganho máximo |
| `filter_min_cutoff` / `filter_beta` | presets SUAVE/NORMAL/REACTIVO | suavidade (teclas `,` `.`) |
| `pinch_on_ratio` / `pinch_off_ratio` | 0.38 / 0.55 | sensibilidade das pinças |
| `scroll_gain_factor` | 0.06 | velocidade do scroll |
| `deadzone_px` | 1.0 | mata micro-deriva com a mão parada |
| `min_hand_scale_px` | 55.0 | distância mínima da mão à câmara |
| `click_freeze_ms` | 60 | congela cursor durante cliques (baixo: palm-center não salta) |

`s` grava tudo em `settings.json` (auto-carrega no arranque) · auto-afinação adaptativa também ajusta sozinha.

## Comandos úteis

```powershell
.venv\Scripts\python.exe main.py                  # normal (janela de preview)
.venv\Scripts\python.exe main.py --no-preview     # invisível
.venv\Scripts\python.exe main.py --gain 1.6       # cursor mais lento
.venv\Scripts\python.exe main.py --camera 1       # outra câmara
.venv\Scripts\python.exe main.py --frames 90      # teste rápido
.venv\Scripts\python.exe main.py --no-voice       # sem voz/mic
.venv\Scripts\python.exe main.py --no-ai          # só regras geométricas
.venv\Scripts\python.exe main.py --gpu            # tenta GPU no tracker
```

Na janela de preview: **Q/ESC** sai · **espaço** pausa · **[ ]** ganho · **, .** suavidade · **s** grava · **h** ajuda · **v** voz · **a** IA.
Voz: diz **"jarvis"** (ou "jarbas") + pausa/continua/clica/clique direito/scroll cima/scroll baixo.

até mesmo com pouca qualidade de imagem da camera deve funcionar 