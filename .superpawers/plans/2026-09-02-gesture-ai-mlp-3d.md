# Gesture AI — MLP com features 3D e classes ROCK/SHAKA (#2)

Data: 2026-09-02
Branch: `feature/gesture-ai-3d`

## Contexto / decisão de negócio

O utilizador aprovou 4 melhorias de IA com execução **escalonada**; esta é a **#2** (menor risco, melhor ROI). Objetivos:

1. Alimentar o MLP com features **3D** (x, y, z normalizados) em vez de só 2D — hoje `_normalize` trunca `[:, :2]` e o `GestureEngine` passa `pts` 2D à IA.
2. Acrescentar as classes **ROCK** e **SHAKA** ao MLP (já existem como `Gesture.ROCK`/"interface" e `Gesture.SHAKA`/"colar" no enum e na geometria).

O z do MediaPipe é ruidoso (nota documentada em `core/gestures.py:98`). Por isso o desenho usa **z relativo ao pulso, escalado pela escala 2D da mão** (normalizador robusto à distância/tamanho), mantendo x,y com a invariância à rotação já existente.

## Estado atual verificado (código lido)

- `core/gesture_ai.py`: `CLASSES` = 7 (OPEN, PINCH, PINCH_MID, FIST, PEACE, THREE, THUMB_UP); `FEATURES = 40`; `_normalize` trunca 2D; `__init__` valida só `b3.shape[0] == N_CLASSES`.
- `core/gestures.py:74` `update`: `pts` 2D em px (`lm[0]*w, lm[1]*h`); linha 82 já tem `p3` 3D normalizado (não usado para IA); **linha 250** `self.ai.classify(pts)` manda 2D.
- `core/gestures.py:255-267` `ml_ok`: já inclui `ml_g == Gesture.SHAKA and thumb_pinky` (linha 266) mas **falta ROCK**.
- `tools/train_gesture_ai.py`: synth 2D (skeletons `(N,2)`), `augment` 2D, `_to_feature` 2D→40, `load_real` exige `(21,2)`, `evaluate_runtime` reconstrói `px (21,2)`. MLP: `w1 (40,96)`, `w3 (48,N_CLASSES)`.
- `tools/test_retrain_smoke.py`: shapes `(21,2)`, dummy `w1 (40,96)`, `_to_feature(...) == (40,)`.
- `tools/collect_gestures.py:190`: guarda `(p[0]*w, p[1]*h)` → descarta z; `CLASS_KEYS`/`CLASS_NAMES` só até THUMB_UP (7). Falta ROCK/SHAKA.
- Runtime: o MediaPipe devolve `(x, y, z)` (usa-se `lm[2]` em `gestures.py:85`); `config.py` tem `ai_confidence_min = 0.72`.

## Não alterar neste plano

- `core/gestures.py` engine geométrico (não mexer nas heurísticas/hysterese) exceto os pontos de integração mínimos (passar 3D à IA + adicionar ROCK ao `ml_ok`).
- `i18n`/UI, licenciamento, voz (Piper/Vosk), trackers LeftHand/TwoHand.
- #1 (LSTM/GRU temporal), #3 (GestureRecognizer v2), #4 (Pose) — ficam para depois.

## Design das features 3D (60)

`_normalize(points)` recebe `(N,3)` (x,y em px; z relativo). Na ausência de z (`len(points[0]) < 3`, testes antigos) calcula-se como 0 (fallback compatível).

```
pts  = asarray(points, float64)         # N x 3
wrist = pts[0]
scale  = hypot(pts[9,0]-wrist[0], pts[9,1]-wrist[1])   # escala 2D wrist->mid-mcp (>=1e-6)
theta  = -atan2(wrist->mid-mcp)                        # invariância à rotação
rot  = [[cos, -sin],[sin, cos]]
rel_xy = (pts[1:] - wrist) @ rot.T                     # rotação plana
z_rel = pts[1:,2] - wrist[2]                           # z relativo ao pulso
feat  = concat([ rel_xy[:,0]/scale, rel_xy[:,1]/scale, z_rel/scale ])   # 60
```

Classificação: `r = feat @ w1` com `w1.shape[0] == FEATURES` (60).

## Fases de implementação (TDD, commits frequentes)

### Fase 1 — `core/gesture_ai.py`: classes + features 60 + validação
1. Adicionar `Gesture.ROCK`, `Gesture.SHAKA` a `CLASSES` (9 classes). `FEATURES = 60`.
2. Reescrever `_normalize` para 60 features 3D com fallback z=0.
3. `__init__`: além de `b3.shape[0]`, validar `w1.shape[0] == FEATURES` (mensagem a pedir retreino).
4. Teste (pytest novo `tests/test_gesture_ai.py`):
   - `_normalize` devolve shape `(60,)` para entrada `(21,3)` e `(40,)`→ agora `(60,)` para `(21,2)` (fallback z=0).
   - invariância à rotação: rodar entrada → features idênticas (x,y) com z relativo igual.
   - invariância à escala: multiplicar `(x,y,z)` → features iguais.
   - `GestureAI` com modelo dummy `(60,96,96,48,48,9)` carrega; dummy `(40,96,...)` → `FileNotFoundError`.
   - `classify` com fake `(21,2)` → retorna classe + conf; com entrada degenerada (scale < 1e-6) → `(None, 0.0)`.
5. Correr `pytest tests -q` (28 esperados no total) + `py_compile`.

### Fase 2 — `tools/train_gesture_ai.py`: synth/augment/to_feature 3D + ROCK/SHAKA
1. `synthesize`: acrescentar casos `Gesture.ROCK` (indicador+mindinho esticados; médio+anelar+polegar dobrados sobre a palma) e `Gesture.SHAKA` (polegar+mindinho esticados; indicador+médio+anelar dobrados) — seguindo o desenho 2D dos dedos já existente e padrões da geometria (`gestures.py:157`, `:184`).
2. Gerar **z sintético plausível**: dedos dobrados → `z` mais próximo da câmara (negativo em relação ao wrist), esticados → ~0, com ruído `~N(0, 0.05)`. Ex.: `z_fold = -0.35 * (0.4 + 0.6*curl)` ao longo do eixo da palma para dedos dobrados; `z ~ 0` para esticados; thumb conforme orientação. Guardar skeletons como `(21,3)`.
   - Precisão: o z real do MediaPipe é aproximado; o erro mais grave seria features não-criptéticas. O algoritmo: para cada landmark, `z += -0.25*curls_do_dedo*prox_ao_pulso` + jitter. Manter simples e determinista por classe.
3. `augment`: rotação 3D leve (tilt/pitch `~N(0,0.15 rad)`) sobre z, escala px só em (x,y), ruído isotrópico `(x,y,z)`, `z` jitter extra `~N(0, 0.02*scale)`.
4. `_to_feature`: replicar o `_normalize` 3D (60) de `gesture_ai.py` (extrair para função partilhada se preferível — mas atenção a imports circulares; `train_gesture_ai.py` já importa de `core.gesture_ai`, por isso pode importar `_normalize`).
   - Simplificar: `_to_feature(raw_skel_px)` = `_normalize(raw_skel_px)` (idêntico). Garante paridade treino/runtime.
5. `load_real`: aceitar `(21,3)` e também `(21,2)` (converter para 3D com z=0) — compatibilidade com datasets antigos.
6. `evaluate_runtime` (linha 310): `px = np.zeros((21,3))` e reconstruir `[x,y,z]` das 60 features.
7. MLP: `w1` passa a `(FEATURES,96)` (auto via constante). Sem mais mudanças.

### Fase 3 — `core/gestures.py`: passar 3D à IA + ROCK no ml_ok
1. Na `update`, criar `pts3 = [(lm[0]*width, lm[1]*height, lm[2]) for lm in landmarks]` (quando `len(landmarks[0]) > 2`; senão `pts3 = pts`).
2. Linha 250: `ml_g, conf = self.ai.classify(pts3)`.
3. `ml_ok`: adicionar `or (ml_g == Gesture.ROCK and geo == Gesture.ROCK)`.
4. Teste (pytest `tests/test_gesture_ai_integration.py` mínimo):
   - `GestureEngine` com `ai=None` inalterado (prova que o caminho 2D continua a funcionar).
   - Com stub de IA que responde `(Gesture.ROCK, 0.9)` e geometria ROCK → `raw` vira ROCK.
   - Sem z (landmarks `(x,y)`) → classificação ainda corre (fallback `pts3 = pts`).

### Fase 4 — `tools/collect_gestures.py`: 3D + ROCK/SHAKA
1. `pts = np.array([(p[0]*w, p[1]*h, p[2]) for p in lm])` (usar o z do MediaPipe; `lm` é tuple `(x,y,z)`).
2. `CLASS_KEYS`/`CLASS_NAMES`: adicionar `8: ROCK`, `9: SHAKA`.
3. `counts()` devolve lista de tamanho `len(CLASS_NAMES)` (hoje `range(5)` — corrigir para `len(CLASS_NAMES)`).
4. Smoke: `--frames 5 --class ROCK` compila/sem camera pode falhar (sem hardware) — validar apenas com py_compile e execução sem camera controlada.

### Fase 5 — atualizar `tools/test_retrain_smoke.py`
1. Shapes: `Xr.shape` → `(60 * N_CLASSES, 21, 3)` (fazer o synth 3D); dummy `w1 (60,96)`; `_to_feature(...) == (60,)`.
2. `collect` real fake também 3D (z=0 ou com jitter).
3. `load_real` com ficheiro antigo `(21,2)` → aceite (converte para 3D).

### Fase 6 — retreinar modelo + verificação
1. Correr `.venv\Scripts\python.exe tools\train_gesture_ai.py` (6000/classe, 24 épocas). Guarda `gesture_mlp_prev.npz` automaticamente.
2. Critérios de aceitação:
   - `val sint acc >= 0.97`; `evaluate_runtime` ~100% (erros com `conf < 0.72` baixos).
   - `pytest tests -q` verde (28+).
   - `tools\test_retrain_smoke.py` PASS (adaptado).
   - `tools\test_left_hand.py` (22) verde — smoke runtime com IA 9 classes.
   - Smoke app: app abre, IA carrega (sem erro de classes), gestos OPEN/PINCH/FIST/THREE/PEACE/THUMB_UP continuam a funcionar; ROCK/SHAKA detetáveis.
3. Se val REAL (se houver dados) < 0.90 → reverter para `gesture_mlp_prev.npz`.

## Riscos / mitigação

- **z-noise do MediaPipe**: mitigado por z relativo ao pulso / escala da mão e confiança mínima (0.72) já exigida no runtime; a geometria continua a ser o juiz principal (`ml_ok` limita a IA ao que a geometria também vê).
- **Regressão em gestos atuais**: `ml_ok` só deixa a IA confirmar o que a geometria confirma; synth mantém os 7 gestos antigos; modelo anterior guardado em `gesture_mlp_prev.npz` para rollback.
- **Datasets reais antigos 2D**: `load_real` converte `(21,2)`→`(21,3)` com z=0; perde-se informação 3D mas mantém-se funcionalidade.
- **Dummy shapes em testes antigos** (`(40,96)`): serão atualizados na Fase 5.

## Verificação final

`pytest tests -q`, `tools\test_retrain_smoke.py`, `tools\test_left_hand.py`, compilação de todos os ficheiros alterados, e smoke manual da app (se hardware disponível).