# AirMouse

Controla o rato do PC com a mão, via webcam. Sem hardware extra.
Motor de precisão profissional: filtragem One Euro + curva de aceleração + palm-center estável + emissor a 180 Hz com sub-pixel e predição de movimento.

## Requisitos
- Windows 10/11
- Python 3.12+ no PATH (`python --version`)
- Webcam

## Instalação (uma vez)
Faz duplo clique em **`setup.bat`** — cria o ambiente virtual e instala tudo.
O modelo `hand_landmarker.task` (~8 MB) descarrega automaticamente na primeira execução.

## Uso
Faz duplo clique em **`start.bat`** (ou corre `.venv\Scripts\python.exe main.py`).

### Gestos
| Gesto | Ação |
|---|---|
| ✋ Mão aberta | Mover o cursor (touchpad relativo) |
| 🤏 Pinça polegar+index | Botão esquerdo: toque rápido = clique · segurar e mover = arrastar |
| 🤏🤞 Pinça polegar+médio | Clique direito |
| ✊ Punho | Arrastar (alternativo) |
| ✌️ Index+médio estendidos | Scroll (mão cima/baixo) |
| 3️⃣ Três dedos estendidos | Volume (mão cima/baixo) |
| 👍 Polegar para cima | Play/Pausa (média) |
| Mão fora de vista / longe | Rato físico funciona normalmente |

### Duas mãos
- **Redundância**: segue a tua mão dominante; se a perder, assume a outra sem salto (reset de filtros).
- **👏 Palmas (2 mãos que se aproximam rápido)** — abre/fecha o assistente 3D barehands (janela Chrome modo app).
- **✋✋ Duas mãos abertas + afastar** — controla a **Lupa do Windows** (amplia/afasta; sair = tirar as mãos).

### Snap magnético
Perto de um botão/campo clicável de qualquer app, o cursor é atraído suavemente para o alvo
e o clique usa o ponto exato dele. Tecla **m** liga/desliga (também por voz: "ativa/desativa o snap").
Usa UI Automation do Windows — funciona no Chrome/Edge, Explorador, apps nativas.

### Luz baixa
Com pouca luz, aplica realce adaptativo (CLAHE) e tenta aumentar a exposição da câmara.
Aparece "LUZ BAIXA" no overlay quando ativo.

Na janela de preview: badge de estado colorido, crosshair na palma, barra de pinça, indicador de scroll,
badge LUPA quando amplificando, contador de mãos.

### Teclas (na janela de preview)
| Tecla | Ação |
|---|---|
| **Q/ESC** | Sair |
| **espaço** | Pausar/retomar o controlo |
| **[** / **]** | Ganho −0.2 / +0.2 (velocidade do cursor) |
| **,** / **.** | Suavidade: SUAVE → NORMAL → REACTIVO |
| **s** | Gravar definições em `settings.json` (auto-carrega no arranque) |
| **h** | Painel de ajuda |
| **v** | Voz ligada/desligada |
| **a** | Classificador IA de gestos ligado/desligado |
| **m** | Snap magnético ligado/desligado |
| **b** | Assistente 3D abrir/fechar |

### Voz profissional (híbrido)
1. Diz **"Jarvis"** (ou "jarbas") — wake word instantânea (Vosk).
2. Fala o comando naturalmente — transcrito pelo **Whisper** local (faster-whisper small int8).
3. O AirMouse responde com **voz neural Piper** (pt_BR; fallback SAPI5 do Windows).

Comandos naturais: `pausa` · `continua` · `clica` · `clique direito` · `scroll cima/baixo`
· `abre/fecha o assistente` · `lupa` · `sem lupa` · `ativa/desativa o snap`.
Primeira utilização descarrega a voz (~60 MB); o Whisper só carrega após o primeiro "Jarvis".

## Opções
```
start.bat                        # normal (janela de preview)
main.py --no-preview             # invisível
main.py --gain 1.6               # cursor mais lento
main.py --camera 1               # outra câmara
main.py --frames 90              # teste rápido (90 frames e sai)
main.py --gpu                    # tenta GPU no tracker (cai para CPU se falhar)
main.py --no-voice               # sem microfone/voz
main.py --no-ai                  # sem classificador IA de gestos
main.py --no-autotune            # sem auto-afinação
main.py --single-hand            # rastreia só 1 mão (desativa a trava de mão)
main.py --voice-always           # voz sempre ativa (sem dizer "jarvis")
main.py --reset-config           # apaga settings.json
main.py --tray                   # invisível + ícone na bandeja (usado pelo arranque automático)
```

### Arranque automático com o Windows
Faz duplo clique em **`install_startup.bat`** — cria uma tarefa agendada que arranca
o AirMouse invisível com ícone na bandeja ao iniciar sessão (`uninstall_startup.bat` remove).
Só corre uma instância (mutex). Ícone da bandeja: pausar, voz on/off, preview, sair.

### IA de gestos com dados reais (opcional, melhora a precisão)

A IA vem treinada com mãos sintéticas. Para treinar com a TUA mão:

```
.venv\Scripts\python.exe tools\collect_gestures.py     # prime 1-5 para escolher gesto e faz gestos
.venv\Scripts\python.exe tools\train_gesture_ai.py --real data\real_landmarks.npz
```

Recomendação: ~100+ amostras por gesto (o contador aparece no ecrã). O treino mistura
sintético + reais, mostra accuracy de validação REAL e guarda o modelo anterior em
`models/gesture_mlp_prev.npz` (para reverter, basta copiar de volta).

### Executável (.exe, sem Python)

Faz duplo clique em **`build.bat`** → cria `dist\AirMouse\` com `AirMouse.exe` + modelos.
Distribuível como pasta zipada; não precisa de Python instalado.

## Afinação (`config.py` ou teclas em tempo real)

| Parâmetro | Default | Efeito |
|---|---|---|
| `move_gain` | 2.0 | velocidade base do cursor (teclas `[` `]`) |
| `accel_min_gain` / `accel_max_gain` | 1.2 / 3.0 | curva de aceleração: preciso devagar, rápido a varrer |
| `accel_ref_speed` | 1400 | velocidade da mão (px/s) que atinge ganho máximo |
| `filter_min_cutoff` / `filter_beta` | presets | suavidade (teclas `,` `.`) |
| `pinch_on_ratio` / `pinch_off_ratio` | 0.42 / 0.58 | sensibilidade das pinças |
| `scroll_gain_factor` | 0.06 | velocidade do scroll |
| `volume_deadzone_px` | 3.0 | zona morta do gesto de volume |
| `snap_radius_px` / `snap_strength` | 46.0 / 0.35 | raio e força da atração magnética |
| `predict_ms` | 0.0 | antecipação do cursor (0 = desativada; ativa em `config.py`) |
| `emitter_rate_hz` | 180 | frequência do emissor de movimento |
| `clap_enabled` / `magnifier_enabled` | true | palmas→assistente · lupa 2 mãos |
| `tts_enabled` / `whisper_model` | true / "small" | voz neural · tamanho do Whisper |
| `low_light_boost` | false | realce automático com pouca luz (liga no menu/`settings.json`)|
| `deadzone_px` | 1.0 | mata micro-deriva com a mão parada |

## Engenharia incluída (porque não treme nem clica sozinho)
1. **One Euro Filter** — sem tremor parado, sem lag em movimento
2. **Curva de aceleração exponencial** — precisão sub-pixel devagar, travessia do ecrã num varrimento
3. **Emissor a 180 Hz** — interpolação entre frames da câmara com acumulador sub-pixel (movimento sedoso mesmo a 15-30 fps)
4. **Predição de movimento** — antecipa o cursor ~40 ms na direção da mão
5. **Ponto de controlo = centro da palma** — imune ao encolher de dedos: zero saltos ao clicar/arrastar
6. **Histerese nas pinças + estabilidade de 3 frames** — sem cliques duplos acidentais
7. **Anti-glitch inteligente** — rejeita teletransportes de landmarks mas nunca trava varrimentos rápidos
8. **Câmara em thread dedicada (MJPG)** — captura nunca bloqueia a inferência; frames duplicados descartados
9. **Botões como estados touchpad** — impossível ficar botão "preso", mesmo pausando a meio de um drag
10. **Scroll/volume com acumulador fracionário** — suave e conservativo (nenhum tick perdido)
11. **Snap magnético via UI Automation** — o cursor "gruda" nos alvos clicáveis reais das apps
12. **Voz híbrida Vosk+Whisper + TTS neural** — wake word instantânea, comandos naturais, respostas faladas
13. **Duas mãos com redundância** — troca de mão dominante sem salto do cursor
14. **Auto-afinação + IA de gestos (7 classes)** — adapta-se à tua câmara e desambígua gestos ambíguos
15. **Luz baixa** — CLAHE adaptativo + exposição da câmara quando o ambiente escurece

## Estrutura
```
airmouse/
├── config.py            ← todos os parâmetros
├── main.py              ← loop tempo real, overlay, hotkeys, voz, bandeja, assistente
├── setup.bat / start.bat / build.bat
├── install_startup.bat / uninstall_startup.bat  ← arranque com o Windows
├── core/
│   ├── filters.py       ← One Euro Filter + AccelCurve
│   ├── motion.py        ← SmoothEmitter (180 Hz, sub-pixel) + predição lead
│   ├── snap.py          ← SnapEngine magnético via UI Automation
│   ├── gestures.py      ← máquina de estados (botões + scroll + volume) + IA
│   ├── hand_lock.py     ← trava de mão: segue o controlador entre intrusos
│   ├── twohand.py       ← palmas→assistente · Lupa do Windows · HandPool
│   ├── assistant.py     ← assistente 3D barehands (Chrome app-mode)
│   ├── tts.py           ← voz neural Piper (+ fallback SAPI5)
│   ├── voice.py         ← Vosk wake word + Whisper comandos naturais
│   ├── nlu.py           ← intenções em português
│   ├── light.py         ← realce automático de luz baixa
│   ├── tray.py          ← ícone na bandeja (pystray)
│   ├── tracker.py       ← HandLandmarker (VIDEO mode, até 2 mãos)
│   ├── camera.py        ← CameraStream (thread + MJPG + dedup)
│   └── mouse_ctl.py     ← pynput + press/release/scroll fracionário
├── tools/
│   ├── collect_gestures.py    ← coleta landmarks reais
│   ├── train_gesture_ai.py    ← treino (sintético + --real dados reais)
│   └── test_v3.py             ← suíte de testes v3 (17 testes)
└── models/              ← hand_landmarker.task · gesture_mlp.npz · vosk · piper/
```
