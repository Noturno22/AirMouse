"""Testes de latencia/confiabilidade do CLIQUE (pinca de corte).

Cobre:
  * commit do PINCH/PINCH_MID no primeiro frame quando
    cfg.pinch_stable_frames == 1 (clique reativo, sem toques perdidos);
  * taps ultrarrápidos de 1 frame produzem exatamente down+up;
  * regressões: OPEN não clica, FIST+polegar não dá clique fantasma,
    a IA não cancela a pinca geométrica, pinça de frente com z-ruído
    continua a ser detetada;
  * os outros gestos mantêm a estabilidade cfg.gesture_stable_frames;
  * a opção responde à configuração (pinch_stable_frames=2 => frame 2);
  * construtores SendInput (core.mouse_ctl) com flags correctas;
  * persistência das novas definições em settings.json.
"""
import json
import os
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import config as cfg_mod  # noqa: E402
from config import Config  # noqa: E402
from core.gestures import Gesture, GestureEngine  # noqa: E402
from tools.train_gesture_ai import synthesize  # noqa: E402

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


def feed(engine, skel, frames):
    events = []
    for _ in range(frames):
        _, ev, _ = engine.update(to_lm(skel), W, H)
        events.append(ev)
    return events


def skel(gesture, seed):
    return synthesize(gesture, np.random.default_rng(seed)) * PX_SCALE


OPEN = skel(Gesture.OPEN, 7)
# Pinca NAO profunda (ratio ~0.32, acima do deep_click 0.315): discrimina a
# aceleracao por pinch_stable_frames vs o atalho deep_click ja existente.
PINCH = skel(Gesture.PINCH, 1234)
PINCH_DEEP = skel(Gesture.PINCH, 42)
PINCH_MID = skel(Gesture.PINCH_MID, 43)
THUMB_UP = skel(Gesture.THUMB_UP, 200)


class FakeAI:
    def __init__(self, g, c):
        self.g, self.c = g, c

    def classify(self, pts):
        return self.g, self.c


def mark_cfg(**kw):
    c = Config()
    for k, v in kw.items():
        setattr(c, k, v)
    return c


# 1. Com pinch_stable_frames=1 o left_down dispara na PRIMEIRA frame de pinca.
cfg = mark_cfg(pinch_stable_frames=1)
eng = GestureEngine(cfg, None)
feed(eng, OPEN, 4)
ev = feed(eng, PINCH, 1)[0]
check("PINCH commit na frame 1 (clique reativo)", ev == "left_down", str(ev))

# 2. Tap ultrarrápido: só 1 frame de pinca entre OPENs => down+up exactos.
eng = GestureEngine(cfg, None)
seq = [to_lm(OPEN)] * 4 + [to_lm(PINCH)] + [to_lm(OPEN)] * 4
got = []
for lm in seq:
    _, ev, _ = eng.update(lm, W, H)
    got.append(ev)
check(
    "tap de 1 frame nao se perde (down+up)",
    got.count("left_down") == 1 and got.count("left_up") == 1,
    str([g for g in got if g]),
)

# 2b. Tap "normal" (2 frames de pinca) continua a dar exatamente down+up.
eng = GestureEngine(cfg, None)
seq = [to_lm(OPEN)] * 4 + [to_lm(PINCH)] * 2 + [to_lm(OPEN)] * 4
got = []
for lm in seq:
    _, ev, _ = eng.update(lm, W, H)
    got.append(ev)
check(
    "tap de 2 frames = down+up",
    got.count("left_down") == 1 and got.count("left_up") == 1,
    str([g for g in got if g]),
)

# 3. PINCH_MID (clique direito) também reage na primeira frame.
eng = GestureEngine(cfg, None)
feed(eng, OPEN, 4)
ev = feed(eng, PINCH_MID, 1)[0]
check("PINCH_MID right_click na frame 1", ev == "right_click", str(ev))

# 4. OPEN em movimento nunca produz cliques.
eng = GestureEngine(cfg, None)
evs = feed(eng, OPEN, 10)
ok = all(e not in ("left_down", "left_up", "right_click") for e in evs)
check("OPEN nunca clica", ok, str([e for e in evs if e]))

# 5. FIST com polegar curvado nunca dá clique fantasma.
def fist_thumb_curled():
    lm = to_lm(skel(Gesture.FIST, 7))
    lm[4] = [lm[9][0], lm[9][1]]
    return lm


eng = GestureEngine(cfg, None)
last = None
for _ in range(6):
    _, ev, _ = eng.update(fist_thumb_curled(), W, H)
    last = ev
check(
    "punho + polegar nunca clica",
    last not in ("right_click", "left_down", "left_up"),
    f"ev={last}",
)

# 6. A IA (a dizer OPEN com confidencia alta) não mata uma pinca geométrica ativa.
eng = GestureEngine(cfg, FakeAI(Gesture.OPEN, 0.99))
feed(eng, OPEN, 4)
ev = feed(eng, PINCH, 1)[0]
check("IA nao cancela pinca geometrica", ev == "left_down" or ev is None, str(ev))
committed = eng._committed
check("commit PINCH com IA contraria", committed == Gesture.PINCH, str(committed))


# 7. Pinça de frente para a câmara (z-ruído) continua detetada (min 2D/3D).
def with_z(skel_px, z_delta, tip_idx=4):
    lm = to_lm(skel_px)
    return [([p[0], p[1], z_delta if i == tip_idx else 0.0]) for i, p in enumerate(lm)]


eng = GestureEngine(cfg, FakeAI(Gesture.OPEN, 0.99))
got = []
for _ in range(6):
    _, ev, _ = eng.update(with_z(PINCH, 0.4), W, H)
    got.append(ev)
check(
    "pinça de frente com z-ruido detetada",
    any(e == "left_down" for e in got),
    str([g for g in got if g]),
)

# 8. Outros gestos mantêm gesture_stable_frames (não acelerei tudo).
cfg8 = mark_cfg(pinch_stable_frames=1, gesture_stable_frames=2)
eng = GestureEngine(cfg8, None)
pp = []
for i in range(8):
    _, ev, _ = eng.update(to_lm(THUMB_UP), W, H)
    if ev == "play_pause":
        pp.append(i)
check(
    "THUMB_UP mantem estabilidade original",
    pp == [cfg8.gesture_stable_frames - 1],
    f"pp={pp}",
)

# 9. Configurabilidade: pinch_stable_frames=2 => clique na 2ª frame.
cfg = mark_cfg(pinch_stable_frames=2)
eng = GestureEngine(cfg, None)
feed(eng, OPEN, 4)
evs = feed(eng, PINCH, 3)
check(
    "pinch_stable_frames=2 cumprido",
    evs[0] is None and evs[1] == "left_down",
    str(evs),
)


# 10. Construtores SendInput (core.mouse_ctl) — puros, sem enviar eventos.
def t_mouse_builders():
    try:
        from core.mouse_ctl import (
            INPUT_MOUSE,
            MOUSEEVENTF_LEFTDOWN,
            MOUSEEVENTF_LEFTUP,
            MOUSEEVENTF_RIGHTDOWN,
            MOUSEEVENTF_RIGHTUP,
            build_mouse_input,
        )
    except ImportError as exc:
        check("mouse builders disponiveis", False, str(exc))
        return
    ld = build_mouse_input(MOUSEEVENTF_LEFTDOWN)
    check("build leftdown tipo INPUT_MOUSE", ld.type == INPUT_MOUSE)
    check("build leftdown flags correctas", ld.union.mi.dwFlags == MOUSEEVENTF_LEFTDOWN,
          hex(ld.union.mi.dwFlags))
    lu = build_mouse_input(MOUSEEVENTF_LEFTUP)
    check("build leftup flags correctas", lu.union.mi.dwFlags == MOUSEEVENTF_LEFTUP)
    rd = build_mouse_input(MOUSEEVENTF_RIGHTDOWN)
    check("build rightdown flags correctas", rd.union.mi.dwFlags == MOUSEEVENTF_RIGHTDOWN)
    ru = build_mouse_input(MOUSEEVENTF_RIGHTUP)
    check("build rightup flags correctas", ru.union.mi.dwFlags == MOUSEEVENTF_RIGHTUP)
    mi = build_mouse_input(0x0002, data=300)
    check("mouseData propagado", mi.union.mi.mouseData == 300)


t_mouse_builders()


# 11. As novas definições persistem em settings.json (round-trip).
def t_settings_roundtrip():
    cfg = Config()
    cfg.pinch_stable_frames = 3
    cfg.click_release_grace_s = 0.15
    cfg.tracker_threads = 4
    tmp = tempfile.mktemp(suffix=".json")
    orig = cfg_mod.SETTINGS_FILE
    try:
        cfg_mod.SETTINGS_FILE = tmp
        cfg_mod.save_settings(cfg, "NORMAL")
        fresh = Config()
        with open(tmp, encoding="utf-8") as fh:
            data = json.load(fh)
        in_saved = all(
            k in data for k in ("pinch_stable_frames", "click_release_grace_s", "tracker_threads")
        )
        check("novas chaves gravadas", in_saved, str(data))
        cfg_mod.load_settings(fresh)
        check("roundtrip pinch_stable_frames",
              fresh.pinch_stable_frames == 3, str(fresh.pinch_stable_frames))
        check("roundtrip click_release_grace_s",
              abs(fresh.click_release_grace_s - 0.15) < 1e-9,
              str(fresh.click_release_grace_s))
        check("roundtrip tracker_threads",
              fresh.tracker_threads == 4, str(fresh.tracker_threads))
    finally:
        cfg_mod.SETTINGS_FILE = orig
        try:
            os.remove(tmp)
        except OSError:
            pass


t_settings_roundtrip()

print(f"\n{passed} PASS / {failed} FAIL")
sys.exit(1 if failed else 0)
