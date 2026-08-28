import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config
from core.twohand import LeftHandDetector

passed, failed = 0, 0


def check(name, cond, extra=""):
    global passed, failed
    print(("PASS " if cond else "FAIL ") + name + (f" {extra}" if extra else ""))
    passed, failed = passed + int(cond), failed + int(not cond)


def feed(det, path, dt=0.05):
    """path: lista de (x, y). Cada passo avanca dt."""
    out = []
    now = 0.0
    prev = None
    for pt in path:
        if prev is not None:
            now += dt
        ev, val = det.update(pt, now)
        if ev is not None:
            out.append((ev, val))
        prev = pt
    return out


cfg = Config()

# 1. Swipe para a direita -> alt_tab_forward (avan~a)
der = LeftHandDetector(cfg)
swipe_right = [
    (100.0, 200.0), (110.0, 201.0), (120.0, 202.0),
    (140.0, 200.0), (170.0, 199.0), (200.0, 201.0),
]
evs = feed(der, swipe_right)
check("swipe direita -> alt_tab_forward", ("alt_tab_forward", None) in evs, str(evs))

# 2. Swipe para a esquerda -> alt_tab_back (retrocede)
der = LeftHandDetector(cfg)
swipe_left = [
    (300.0, 200.0), (290.0, 201.0), (275.0, 202.0),
    (250.0, 200.0), (215.0, 199.0), (180.0, 201.0),
]
evs = feed(der, swipe_left)
check("swipe esquerda -> alt_tab_back", ("alt_tab_back", None) in evs, str(evs))

# 3. Movimento vertical continuo -> scroll (deslizar cima/baixo)
der = LeftHandDetector(cfg)
scroll_up = [(200.0, 300.0), (200.0, 280.0), (200.0, 250.0),
             (200.0, 210.0), (200.0, 170.0), (200.0, 130.0)]
evs = feed(der, scroll_up)
scrolls = [v for e, v in evs if e == "scroll"]
check("deslizar p/ cima -> scroll positivo", len(scrolls) >= 1 and all(v > 0 for v in scrolls), str(evs))

der = LeftHandDetector(cfg)
scroll_down = [(200.0, 130.0), (200.0, 170.0), (200.0, 210.0),
               (200.0, 250.0), (200.0, 290.0), (200.0, 330.0)]
evs = feed(der, scroll_down)
scrolls = [v for e, v in evs if e == "scroll"]
check("deslizar p/ baixo -> scroll negativo", len(scrolls) >= 1 and all(v < 0 for v in scrolls), str(evs))

# 4. Mao esquerda ausente -> reset, nada emite
der = LeftHandDetector(cfg)
der.update((200.0, 200.0), 0.0)
evs = feed(der, [None, None, None])
check("mao ausente nao emite", evs == [], str(evs))

# 5. Nanhuma acao em movimento pequeno/diagonal suave
der = LeftHandDetector(cfg)
small = [(200.0, 200.0)] * 3
evs = feed(der, small)
check("mao parada nao emite", evs == [], str(evs))

print(f"\n{passed} PASS / {failed} FAIL")
sys.exit(1 if failed else 0)
