# AirMouse - Gestos e Atalhos

Referencia completa de todos os gestos, atalhos de teclado e comandos de voz.

---

## Gestos de Mao (1 mao)

| Gesto | Descricao | Accao |
|---|---|---|
| Mao aberta | Todos os dedos estendidos | Mover o cursor |
| 1 dedo (index) | Apenas o index levantado, restantes fechados | Mover o cursor (menos cancadito) |
| Pinca index | Polegar + index juntos | Clique esquerdo (toque rapido = clique, segurar = arrastar) |
| Pinca medio | Polegar + medio juntos | Clique direito |
| Punho | Mao fechada, deslizar cima/baixo | Scroll (punho para cima = cima, para baixo = baixo) |
| 2 dedos (peace) | Index + medio estendidos | (sem funcao ativa) |
| 3 dedos | Index + medio + anel estendidos | Volume (mao cima/baixo) |
| Polegar para cima | Punho fechado, polegar para cima | Play/Pausa multimedia |
| Dedo mindinho | Apenas o mindinho levantado | Copiar (Ctrl+C) |
| Polegar + mindinho | Shaka: polegar + mindinho estendidos | Colar (Ctrl+V) |

### Notas sobre mover o cursor

- **Mao aberta**: gesto principal, todos os dedos visiveis pela webcam.
- **1 dedo (index)**: alternativa menos cansativa. Basta ter o index levantado e os outros 4 dedos fechados. Ideal para sessoes longas de uso.
- Ambos usam o mesmo motor de filtragem One Euro + curva de aceleracao + predicao de movimento.

---

## Gestos de Duas Maos

| Gesto | Descricao | Accao |
|---|---|---|
| Palmas (x3) | 3 palmas rapidas com as duas maos | Alt+Tab (trocar janela) |
| Dois dedos direito (2 maos) | Peace com a mao direita | Aumentar brilho do ecra |
| 2 maos abertas + afastar | Abrir as maos e afastar | Lupa (zoom in/out) |
| Palma unica (clap) | Duas maos juntas rapido | Abrir/Fechar assistente 3D |

---

## Comandos da Mao Esquerda (separados da direita)

A mao que aparece no **lado esquerdo do ecra** (preview espelhada) e a
"mao de comandos"; a que aparece no **lado direito** move o cursor.
A mao de comandos nunca move o cursor; so dispara acoes.

| Gestos | Descricao | Accao |
|---|---|---|
| Swipe p/ a direita | Deslizar a mao esquerda lateralmente p/ a direita | Trocar para a proxima janela (Alt+Tab rapido) |
| Swipe p/ a esquerda | Deslizar a mao esquerda lateralmente p/ a esquerda | Trocar para a janela anterior (Alt+Shift+Tab rapido) |
| Segurar a mao aberta ~2s | Manter a mao esquerda aberta e parada | Abrir o alternador de janelas (escolher janela) |
| Punho fechado (so ela) | Fechar apenas a mao esquerda | Fechar janela (Alt+F4) |
| Dois dedos (paz) | Peace com a mao esquerda | Mostrar/ocultar a interface (GUI) |

> **Nota**: o swipe faz uma troca **rapida** — avança/retrocede uma janela e
> solta logo o Alt (ideal para mudar depressa). Se quiser **escolher** a janela,
> segure a mao esquerda **aberta** durante ~2s: abre o alternador do Windows;
> enquanto a mao continua aberta pode deslizar para a esquerda/direita para
> navegar entre as janelas, e ao soltar (fechar ou tirar a mao) confirma a janela
> selecionada. O punho fecha a janela **apenas quando e a unica mao presente**.
> O gesto de paz (PEACE) com a mao esquerda mostra/oculta a interface (GUI) de
> configuracao.

---

## Gestos de Atalhos (combinacoes)

| Gesto | Accao | Atalho enviado |
|---|---|---|
| Fechar/abrir punho x2 | Ciclo rapido de fechar e abrir o punho 2 vezes | Win+D (mostrar desktop) |
| Bye-bye (onda lateral) | Mover a mao de lado a lado 3x rapido | Minimizar janela (Win+Down) |

### Como fazer o gesto bye-bye

1. Mao aberta, palma visivel
2. Mover rapidamente para a esquerda, depois direita, depois esquerda (3 inversoes)
3. Amplitude minima: ~15 pixels
4. Janela temporal: 1.5 segundos

---

## Atalhos de Teclado (enquanto o AirMouse esta ativo)

| Tecla | Accao |
|---|---|
| `[` | Diminuir ganho (cursor mais lento) |
| `]` | Aumentar ganho (cursor mais rapido) |
| `,` | Suavidade: preset anterior |
| `.` | Suavidade: proximo preset |
| `A` | Toggle auto-afinacao |
| `V` | Toggle comandos de voz |
| `S` | Gravar definicoes em settings.json |
| `H` | Mostrar/ocultar overlay de ajuda (F1 na janela da UI) |
| `M` | Toggle snap magnetico |
| `B` | Abrir assistente 3D |
| `Espaco` | Pausar/retomar AirMouse |
| `Q` / `Esc` | Sair |

### Presets de suavidade

| Preset | Filtro (corte min) | Beta |
|---|---|---|
| SUAVE | 0.9 | 0.02 |
| NORMAL | 1.4 | 0.028 |
| REACTIVO | 2.2 | 0.05 |

---

## Comandos de Voz

Diga **"Jarvis"** (wake word) seguido de um destes comandos:

| Comando | Accao |
|---|---|
| "clica" / "clique" | Clique esquerdo |
| "clique direito" | Clique direito |
| "sobe" / "cima" | Scroll para cima |
| "desce" / "baixo" | Scroll para baixo |
| "pausa" / "para" | Pausar AirMouse |
| "continua" / "retoma" | Retomar AirMouse |
| "mais rapido" / "acelera" | Aumentar ganho |
| "mais devagar" / "desacelera" | Diminuir ganho |
| "suave" | Preset suave |
| "reactivo" | Preset reactivo |
| "normal" | Preset normal |
| "gravar" / "guardar" | Gravar definicoes |
| "ajuda" | Mostrar ajuda |
| "lupa" / "zoom" | Ativar lupa |
| "snap" / "ima" | Toggle snap magnetico |
| "assistente" | Abrir assistente 3D |
| "sai" / "termina" | Sair do AirMouse |

### LLM (Ollama)

Se o Ollama estiver a correr localmente (porta 11434), comandos naturais nao listados acima sao interpretados pelo LLM (modelo `llama3.2:3b` por defeito).

---

## Argumentos de Linha de Comandos

```
python main.py [opcoes]
```

| Opcao | Descricao |
|---|---|
| `--camera N` | Index da webcam (0, 1, 2...) |
| `--gain FLOAT` | Ganho inicial do cursor |
| `--no-preview` | Sem janela de preview |
| `--preview` | Forcar janela mesmo em modo bandeja |
| `--gpu` | Usar delegado GPU no tracker |
| `--tray` | Modo bandeja (icone na bandeja do Windows) |
| `--reset-config` | Apagar settings.json |
| `--no-voice` | Desativar comandos de voz |
| `--no-ai` | Desativar classificador IA |
| `--no-autotune` | Desativar auto-afinacao |
| `--voice-always` | Voz sempre ativa (sem wake word) |
| `--no-tts` | Sem voz falada do Jarvis |
| `--whisper-model M` | Modelo Whisper (tiny/base/small) |
| `--frames N` | Processar N frames e sair (teste) |
| `--pinch-debug` | Imprimir racios de pinca no console |

---

## Ficheiros

| Ficheiro | Descricao |
|---|---|
| `main.py` | Entry point e loop principal |
| `config.py` | Configuracao centralizada |
| `core/gestures.py` | Motor de deteccao de gestos |
| `core/tracker.py` | MediaPipe HandLandmarker |
| `core/mouse_ctl.py` | Controlo do rato |
| `core/filters.py` | Filtro One Euro + curva de aceleracao |
| `core/motion.py` | Emissor de movimento a 180 Hz |
| `core/twohand.py` | Gestos de duas maos (clap, brilho, lupa, etc.) |
| `core/voice.py` | STT com Vosk |
| `core/tts.py` | TTS com Piper (PT-BR) |
| `core/nlu.py` | Interpretacao de comandos de voz |
| `core/assistant.py` | Assistente 3D (barehands) |
| `core/snap.py` | Snap magnetico |
| `core/autotune.py` | Auto-afinacao de filtros |
| `core/tray.py` | Icone na bandeja do Windows |
| `tools/train_gesture_ai.py` | Treinar modelo MLP de gestos |
| `tools/collect_gestures.py` | Recolher dados de treino |
