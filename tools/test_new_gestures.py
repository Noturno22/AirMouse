import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config
from core.gestures import Gesture, GestureEngine
from tools.train_gesture_ai import synthesize

W, H = 640, 480
ORIGIN = np.array([0.55 * W, 0.55 * H])
PX_SCALE = 120.0

passed, failed = 0, 0


def check(name, cond, extra=""):
    global passed, failed
    print(("PASS " if cond else "FAIL ") + name + (f" {extra}" if extra else ""))
    passed, failed = passed + int(cond), failed + int(not cond)


def to_lm(skel_px):
    return ((skel_px + [ORIGIN[0], ORIGIN[1]]) / [W, H]).tolist()


def feed(engine, skel, frames, dy_per_frame=0.0):
    events = []
    cur = skel.copy()
    last = None
    for _ in range(frames):
        lm = to_lm(cur)
        _, ev, val = engine.update(lm, W, H)
        if ev is not None:
            events.append((ev, val))
        last = engine._committed
        if dy_per_frame:
            cur = cur + np.array([0.0, dy_per_frame])
    return events, last


cfg = Config()
rng = np.random.default_rng(11)

# 1. THREE classifica por geometria (sem IA) e emite volume ao descer
skel_three = synthesize(Gesture.THREE, rng) * PX_SCALE
eng = GestureEngine(cfg, None)
events, committed = feed(eng, skel_three, 6)
check("THREE classifica", committed == Gesture.THREE, str(committed))
check("THREE sem eventos na entrada", all(e[0] != "play_pause" for e in events))

eng = GestureEngine(cfg, None)
feed(eng, skel_three, 5)
down_events, _ = feed(eng, skel_three, 8, dy_per_frame=6.0)
vols = [v for e, v in down_events if e == "volume"]
check("volume emite ao descer", len(vols) >= 1 and all(v > 0 for v in vols), str(down_events))

eng = GestureEngine(cfg, None)
feed(eng, skel_three, 5)
up_events, _ = feed(eng, skel_three, 8, dy_per_frame=-6.0)
vols_up = [v for e, v in up_events if e == "volume"]
check("volume negativo ao subir", len(vols_up) >= 1 and all(v < 0 for v in vols_up))

# movimento pequeno nao cruza a deadzone
eng = GestureEngine(cfg, None)
feed(eng, skel_three, 5)
small, _ = feed(eng, skel_three, 2, dy_per_frame=2.0)
check("deadzone segura micro-movimentos", all(e != "volume" for e, _ in small))

# 2. THUMB_UP classifica e emite play_pause UMA vez
ok_tu = True
for t in range(12):
    r = np.random.default_rng(200 + t)
    skel_tu = synthesize(Gesture.THUMB_UP, r) * PX_SCALE
    eng = GestureEngine(cfg, None)
    pp = []
    last = None
    for i in range(8):
        _, ev, _ = eng.update(to_lm(skel_tu), W, H)
        if ev == "play_pause":
            pp.append(i)
        last = eng._committed
    if last != Gesture.THUMB_UP or pp != [cfg.gesture_stable_frames - 1]:
        ok_tu = False
        print(f"  amostra {t}: committed={last} play_pause={pp}")
check("THUMB_UP classifica + play_pause uma vez (12 seeds)", ok_tu)
skel_hold = synthesize(Gesture.THUMB_UP, np.random.default_rng(300)) * PX_SCALE
eng = GestureEngine(cfg, None)
feed(eng, skel_hold, 5)
held, _ = feed(eng, skel_hold, 12)
check("segurar nao repete play_pause", all(e != "play_pause" for e, _ in held))

# 2b. THUMB_DOWN ("deslike") classifica e nunca emite play_pause
ok_td = True
for t in range(12):
    r = np.random.default_rng(400 + t)
    skel_td = synthesize(Gesture.THUMB_DOWN, r) * PX_SCALE
    eng = GestureEngine(cfg, None)
    evs, committed = feed(eng, skel_td, 8)
    if committed != Gesture.THUMB_DOWN or any(e == "play_pause" for e, _ in evs):
        ok_td = False
        print(f"  deslike virou {committed} na amostra {t}")
check("THUMB_DOWN classifica + nao toca play_pause (12 seeds)", ok_td)
skel_tu5 = synthesize(Gesture.THUMB_UP, np.random.default_rng(9)) * PX_SCALE
eng = GestureEngine(cfg, None)
feed(eng, skel_tu5, 5)
up_evs, up_last = feed(eng, skel_tu5, 4)
check("THUMB_UP nao confundido com deslike", up_last == Gesture.THUMB_UP, str(up_last))

# 3. FIST nunca e confundido com THUMB_UP (polegar junto ao punho)
ok_fist = True
for t in range(12):
    r = np.random.default_rng(100 + t)
    skel_fist = synthesize(Gesture.FIST, r) * PX_SCALE
    eng = GestureEngine(cfg, None)
    _, committed = feed(eng, skel_fist, 6)
    if committed != Gesture.FIST:
        ok_fist = False
        print(f"  fist virou {committed} na amostra {t}")
check("FIST mantem-se FIST (sem play_pause)", ok_fist)

# 4. Regressao: PEACE (dois dedos) ja NAO faz scroll
skel_peace = synthesize(Gesture.PEACE, rng) * PX_SCALE
eng = GestureEngine(cfg, None)
feed(eng, skel_peace, 5)
peace_evs, _ = feed(eng, skel_peace, 8, dy_per_frame=6.0)
check("PEACE ja nao faz scroll", all(e != "scroll" for e, _ in peace_evs), str(peace_evs))

# 4b. FIST (punho fechado) e agora quem faz scroll: deslizar para baixo -> positivo
skel_fist = synthesize(Gesture.FIST, np.random.default_rng(51)) * PX_SCALE
eng = GestureEngine(cfg, None)
feed(eng, skel_fist, 4)
fist_evs, _ = feed(eng, skel_fist, 8, dy_per_frame=6.0)
scrolls = [v for e, v in fist_evs if e == "scroll"]
check("FIST faz scroll ao descer", len(scrolls) >= 1 and all(v > 0 for v in scrolls), str(fist_evs))
eng = GestureEngine(cfg, None)
feed(eng, skel_fist, 4)
fist_up, _ = feed(eng, skel_fist, 8, dy_per_frame=-6.0)
scrolls_up = [v for e, v in fist_up if e == "scroll"]
check("FIST scroll negativo ao subir", len(scrolls_up) >= 1 and all(v < 0 for v in scrolls_up))
check("FIST nao da clique (sem arrastar)",
      all(e not in ("left_down", "left_up", "right_click") for e, _ in fist_evs) and
      all(e not in ("left_down", "left_up", "right_click") for e, _ in fist_up))

# 5. OPEN nao emite eventos
skel_open = synthesize(Gesture.OPEN, rng) * PX_SCALE
eng = GestureEngine(cfg, None)
evs, committed = feed(eng, skel_open, 8, dy_per_frame=4.0)
check(
    "OPEN move sem eventos",
    committed == Gesture.OPEN and all(e in ("left_down", "left_up") for e, _ in evs),
    f"{committed} {evs}",
)

class FakeAI:
    def __init__(self, g, c):
        self.g, self.c = g, c

    def classify(self, pts):
        return self.g, self.c


# 6. A IA nunca inventa modos sobre uma mao aberta (movimento nao congela)
skel_open2 = synthesize(Gesture.OPEN, np.random.default_rng(41)) * PX_SCALE
for ml in (
    Gesture.THREE, Gesture.FIST, Gesture.PEACE,
    Gesture.THUMB_UP, Gesture.PINCH, Gesture.PINCH_MID,
):
    eng = GestureEngine(cfg, FakeAI(ml, 0.99))
    _, committed = feed(eng, skel_open2, 8)
    check(f"IA {ml.name} nao rouba OPEN", committed == Gesture.OPEN, str(committed))

# 7. A IA nao mata um clique geometrico ativo
skel_pinch = synthesize(Gesture.PINCH, np.random.default_rng(42)) * PX_SCALE
eng = GestureEngine(cfg, FakeAI(Gesture.OPEN, 0.99))
evs, committed = feed(eng, skel_pinch, 6)
check(
    "IA nao cancela pinca",
    committed == Gesture.PINCH and any(e == "left_down" for e, _ in evs),
    f"{committed} {evs}",
)

# 8. Toque rapido de pinca funda registra exatamente down+up
eng = GestureEngine(cfg, None)
seq = [to_lm(skel_open)] * 4 + [to_lm(skel_pinch)] * 2 + [to_lm(skel_open)] * 4
got = []
for lm in seq:
    _, ev, _ = eng.update(lm, W, H)
    got.append(ev)
check(
    "toque rapido down+up",
    got.count("left_down") == 1 and got.count("left_up") == 1,
    str([g for g in got if g]),
)

# 9. Regressao pinça de FRENTE para a camara (dedos apontam para a camara).
# A partir de uma pinça geometrica valida, separamos polegar/indicador em z (z-ruido
# do MediaPipe): o racio 3D sozinho dispara acima do limiar, mas o minimo(2D,3D) mantem.
def with_z(skel_px, z_delta, tip_idx=4):
    lm = to_lm(skel_px)
    return [([l[0], l[1], z_delta if i == tip_idx else 0.0]) for i, l in enumerate(lm)]


skel_pinch2 = synthesize(Gesture.PINCH, np.random.default_rng(1234)) * PX_SCALE
eng = GestureEngine(cfg, FakeAI(Gesture.OPEN, 0.99))
got = []
for _ in range(6):
    _, ev, _ = eng.update(with_z(skel_pinch2, 0.4), W, H)
    got.append(ev)
check(
    "pinça de frente detetada (min 2D/3D)",
    any(e == "left_down" for e in got),
    str([g for g in got if g]),
)

# 10. Regressao: agarrar (FIST, polegar dobrado) nunca e roubado por uma pinça.
def fist_with_thumb_curled():
    skel = synthesize(Gesture.FIST, np.random.default_rng(7)) * PX_SCALE
    lm = to_lm(skel)
    # aproxima o polegar da regiao do medio, como quando se fecha o punho
    lm[4] = [lm[9][0], lm[9][1]]
    return lm


eng = GestureEngine(cfg, None)
last = None
for _ in range(6):
    _, ev, _ = eng.update(fist_with_thumb_curled(), W, H)
    last = ev
check(
    "punho/pinca nunca da clique direito fantasma",
    last not in ("right_click", "left_down", "left_up"),
    f"ev={last}",
)

print(f"\n{passed} PASS / {failed} FAIL")
sys.exit(1 if failed else 0)
