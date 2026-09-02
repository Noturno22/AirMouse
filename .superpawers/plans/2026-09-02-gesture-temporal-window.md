# Gesture AI — Janela temporal (sliding window) no MLP (#1)

Data: 2026-09-02
Branch: `feature/gesture-temporal-window` (parte do #2 → `feature/gesture-ai-3d`)

## Contexto / decisão

O utilizador escolheu a opção **"Janela temporal (sliding window) no MLP"** (baixo risco):
manter o MLP atual mas alimentá-lo com informações de uma janela de frames recentes, em
vez de um único frame. Objetivo: robustez ao ruído frame-a-frame do MediaPipe sem
introduzir uma rede recorrente (LSTM/GRU).

**Desenho (stateless GestureAI, buffer por-engine):**
- Descobriu-se que em `core/twohand.py:191-192` o **mesmo `GestureAI` é partilhado por
  dois `GestureEngine`** (Left/Right). Logo o buffer temporal **NÃO pode** viver dentro do
  `GestureAI` (seria estado partilhado entre mãos → errado).
- O buffer da janela vive no **`GestureEngine`** (cada engine = uma mão). O `GestureAI`
  permanece **stateless**: recebe a lista de frames da janela e computa o agregado.
- Features = `[feat_atual (60), mean(janela) (60)]` = **120**.
  - frame atual → resposta imediata (sem atraso de transição).
  - média da janela → suaviza ruído, discrimina transições.
- Janela W = `config.ai_window = 5` frames.

## Estado atual verificado (código lido)

- `core/gesture_ai.py`: `CLASSES` 9, `FEATURES=60`, `_normalize` (stateless), `classify(points_px)`
  normaliza 1 frame e faz forward MLP (w1 (60,96)).
- `core/gestures.py:74 update`: computa `pts3` (3D px); **linha ~251** `ml_g, conf = self.ai.classify(pts3)`.
- `core/twohand.py:191`: `GestureEngine(cfg, gesture_ai)` ×2 partilham o mesmo object.
- `core/gestures.py reset()`: zera estado (onde sincronizar reset da janela).
- `tools/train_gesture_ai.py`: `synthesize` → 1 skeleton `(21,3)`; `make_dataset` gera amostras
  independentes (uma por gesto). Precisa de gerar **sequências** para a média ser informativa.
- `config.py:110-111`: `ai_enabled`, `ai_confidence_min=0.72`, `ai_model_path`.
- Testes: `tests/test_gesture_ai.py` (18), `tests/test_gesture_ai_integration.py` (3),
  `tools/test_retrain_smoke.py`, `tools/test_new_gestures.py`/`test_click_latency.py` usam `FakeAI`
  (`classify(self, pts)` devolve fixo, ignora o argumento → não quebram com lista).

## Não alterar neste plano

- Bloco `ml_ok` / geometria / hysteresis (`gestures.py`) — só o ponto de integração mínima.
- `collect_gestures.py` (fica 3D frame-a-frame; não muda com janela — a janela é do runtime).
- #3 (GestureRecognizer v2), #4 (Pose). LSTM/GRU completo fica fora.

## Design das features (120)

```
classify(frames)  onde frames = List[(21,3)]  (ou um único frame (21,3))
feats = [_normalize(f) for f in frames if ok]     # cada um (60,)
cur   = feats[-1]
mean  = np.mean(feats, axis=0)                    # média da janela
feat  = concatenate([cur, mean])                  # (120,)
MLP forward com w1 (120,96)
```

Compatibilidade: `classify` aceita um único frame `(21,3)` (numpy, `ndim==2`) → trata como
janela de 1 (`mean = cur`). Aceita lista de frames. Estateless: nada guardado internamente.

## Fases de implementação (TDD, commits frequentes)

### Fase 1 — `config.py` + `core/gesture_ai.py`: janela 120 + validação + testes
1. `config.py`: adicionar `ai_window: int = 5` (após `ai_confidence_min`).
2. `core/gesture_ai.py`:
   - `FEATURES = 120`.
   - `_is_frame_list(p)` helper: `p` é lista/tuple de frames quando `len(p)>0` e
     `np.asarray(p[0]).ndim == 2`.
   - `classify(points_px)`: se `_is_frame_list` → `frames = list(points_px)`; senão `frames=[points_px]`.
     Normaliza todos, `cur=feats[-1]`, `mean=np.mean(feats,0)`, `feat=concat([cur,mean])`.
     Se nenhum frame normalizável → `(None, 0.0)`.
   - Validação do modelo continua: `b3.shape==N_CLASSES` e `w1.shape[0]==FEATURES`.
3. Teste `tests/test_gesture_ai.py`:
   - `FEATURES == 120`.
   - `classify` com frame único devolve classe+conf (janela=1).
   - `classify` com janela de 5 frames do mesmo gesto devolve a mesma classe.
   - modelo dummy `w1 (120,96)` carrega; `w1 (60,96)` → `FileNotFoundError` (features).
4. `pytest tests -q` (46+).

### Fase 2 — `tools/train_gesture_ai.py`: sequências temporais
1. `make_dataset`/loop de treino: para cada amostra, gerar **W skeletons do mesmo gesto**
   (rng diferente por frame, jitter independente) e computar `feat = [_to_feature(f) for f in frames]`,
   `cur=feats[-1]`, `mean=np.mean(feats,0)`, `X = concat([cur,mean])`.
   - Reutilizar `_normalize` (via `_to_feature` que já o usa) por frame.
   - `evaluate_runtime`: reconstruir janela de W frames 3D das `X` (ou gerar W skeletons diretamente).
2. Nota de design: treinar com janelas **homogéneas** (mesmo gesto nos W frames) é suficiente
   para o MVP; transições são geridas pela geometria/hysteresis. Documentar como limitação.

### Fase 3 — `core/gestures.py`: buffer da janela por-engine + chamada com lista
1. `GestureEngine.__init__`: `self._ai_window = collections.deque(maxlen=cfg.ai_window)`.
   - Cuidado: `cfg` pode não ter `ai_window` em testes antigos → usar `getattr(cfg, "ai_window", 5)`.
2. `reset()`: `self._ai_window.clear()`.
3. Na `update` (junto a `pts3`): `self._ai_window.append(pts3)`; ignorar se `pts3` degenerado.
4. Linha ~251: `ml_g, conf = self.ai.classify(list(self._ai_window))`.
5. Teste `tests/test_gesture_ai_integration.py`:
   - `GestureEngine(cfg, None)` com landmark 2D/3D não quebra (janela acumula).
   - SpyIA recebe lista (non-empty) e a última entrada é o frame do frame atual.
   - `reset()` esvazia a janela (lista vazia → classify não chamado, ou trata janela vazia com graça).

### Fase 4 — `tools/test_retrain_smoke.py`: shapes sequenciais
1. Geração de dados reais fake: manter frame `(21,3)`, mas o `_to_feature` agora recebe
   um **frame único** (não a sequência) — verificar que `_to_feature(frame).shape == (60,)`.
   A conversão sequência→120 acontece no loop de treino (Fase 2).
2. dummy `w1 (120,96)`.
3. `_to_feature` continua devolvendo `(60,)` (frame único) — mantém.

### Fase 5 — retreinar modelo + verificação
1. `.venv\Scripts\python.exe tools\train_gesture_ai.py` (6000/classe, 24 épocas). Backup automático.
2. Critérios: `val sint >= 0.97`; `evaluate_runtime` ~100% (baixa conf na maioria acertada);
   `pytest -q` verde; `tools\test_retrain_smoke.py` PASS; `tools\test_left_hand.py` verde;
   modelo `GestureAI` carrega com `w1 (120,96)` de `models/` e `core/`.
3. Smoke manual (hardware) recomendado.

## Riscos / mitigação

- **Partilha do GestureAI entre mãos**: mitigado por buffer **por-engine** (stateless GestureAI).
- **Atrito nas transições**: frame atual preserva resposta imediata; W pequeno (5).
- **Regressão 7/9 classes**: synth mantém os mesmos gestos; `gesture_mlp_prev.npz` p/ rollback.
- **Dataset real antigo 2D**: `load_real` converte para 3D (z=0); janela usa média — ok.
- **FakeAI/testes com assinatura antiga**: FakeAI ignora argumento; `classify` aceita frame único.

## Verificação final

`pytest tests -q`, `tools\test_retrain_smoke.py`, `tools\test_left_hand.py`, compilação, e smoke da app.