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

# 4. Regressao: PEACE continua scroll
skel_peace = synthesize(Gesture.PEACE, rng) * PX_SCALE
eng = GestureEngine(cfg, None)
feed(eng, skel_peace, 5)
sc_events, _ = feed(eng, skel_peace, 8, dy_per_frame=6.0)
check("PEACE continua scroll", any(e == "scroll" and v > 0 for e, v in sc_events), str(sc_events))

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

print(f"\n{passed} PASS / {failed} FAIL")
sys.exit(1 if failed else 0)
