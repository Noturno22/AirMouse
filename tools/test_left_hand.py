import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config
from core.gestures import Gesture
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

# 6. Abrir/fechar a mao 3x (OPEN<->FIST, 3 transicoes) -> gui_toggle
def feed_gesture(det, seq, dt=0.05):
    out = []
    for i, g in enumerate(seq):
        ev, val = det.update((200.0, 200.0), i * dt, g)
        if ev is not None:
            out.append((ev, val))
    return out

der = LeftHandDetector(cfg)
seq3 = [Gesture.OPEN, Gesture.FIST, Gesture.OPEN, Gesture.FIST]
evs = feed_gesture(der, seq3)
check("abrir/fechar 3x -> gui_toggle", ("gui_toggle", None) in evs, str(evs))

# 7. Apenas 2 transicoes nao devem disparar gui_toggle
der = LeftHandDetector(cfg)
seq2 = [Gesture.OPEN, Gesture.FIST, Gesture.OPEN]
evs = feed_gesture(der, seq2)
check("abrir/fechar 2x -> sem gui_toggle", evs == [], str(evs))

# 8. Swipe continua a funcionar mesmo com gesture presente (sem disparo de pump)
der = LeftHandDetector(cfg)
swipe_fwd_open = [
    (100.0, 200.0), (120.0, 201.0), (140.0, 202.0),
    (160.0, 200.0), (185.0, 199.0), (210.0, 201.0),
]
evs2 = []
now = 0.05
for pt in swipe_fwd_open:
    ev, val = der.update(pt, now, Gesture.OPEN)
    if ev is not None:
        evs2.append((ev, val))
    now += 0.05
check("swipe c/ gesture constante nao dispara gui_toggle e avanca",
      ("alt_tab_forward", None) in evs2 and ("gui_toggle", None) not in evs2, str(evs2))

# 9. Segurar a mao ABERTA durante o tempo configurado -> alt_switch_open
der = LeftHandDetector(cfg)
hold_evs = []
hold_dt = 0.05
now = 0.0
while now < cfg.left_hand_open_switch_s + 0.3:
    ev, val = der.update((200.0, 200.0), now, Gesture.OPEN)
    if ev is not None:
        hold_evs.append((ev, val))
    now += hold_dt
check("segurar mao aberta -> alt_switch_open",
      ("alt_switch_open", None) in hold_evs, str(hold_evs))

# 10. Segurar FIST (punho) nao abre o alternador
der = LeftHandDetector(cfg)
fist_evs = []
now = 0.0
while now < cfg.left_hand_open_switch_s + 0.3:
    ev, val = der.update((200.0, 200.0), now, Gesture.FIST)
    if ev is not None:
        fist_evs.append((ev, val))
    now += hold_dt
check("segurar punho nao abre alternador", ("alt_switch_open", None) not in fist_evs, str(fist_evs))

# 11. Abrir o alternador so dispara UMA vez (stateful) enquanto mantida aberta
der = LeftHandDetector(cfg)
once_evs = []
now = 0.0
has_open = False
while now < cfg.left_hand_open_switch_s * 2 + 0.5:
    ev, val = der.update((200.0, 200.0), now, Gesture.OPEN)
    if ev == "alt_switch_open":
        once_evs.append(now)
    now += hold_dt
check("alternador abre uma unica vez por hold",
      len(once_evs) == 1, f"tt={[round(t,2) for t in once_evs]}")

# 12. Depois de largar (nao OPEN) e voltar a segurar, abre de novo
der = LeftHandDetector(cfg)
now = 0.0
opens = 0
while now < cfg.left_hand_open_switch_s + 0.3:
    ev, val = der.update((200.0, 200.0), now, Gesture.OPEN)
    if ev == "alt_switch_open":
        opens += 1
    now += hold_dt
# largar (FIST durante 1s) e voltar a segurar
now += 1.0
der.update((200.0, 200.0), now, Gesture.FIST)
now += 0.1
end = now + cfg.left_hand_open_switch_s + 0.3
while now < end:
    ev, val = der.update((200.0, 200.0), now, Gesture.OPEN)
    if ev == "alt_switch_open":
        opens += 1
    now += hold_dt
check("segurar de novo apos largar reabre", opens == 2, f"opens={opens}")

# 13. Durante um pump (abrir/fechar 3x) o punho NÃO deve fechar a janela:
#     pumping_until fica no futuro, usado pelo main para suprimir Alt+F4.
der = LeftHandDetector(cfg)
now = 0.0
seq3 = [Gesture.OPEN, Gesture.FIST, Gesture.OPEN, Gesture.FIST]
for g in seq3:
    _, _ = der.update((200.0, 200.0), now, g)
    now += 0.05
check("pump ativo suprime punho", der.pumping_until > 0.0,
      f"until={der.pumping_until}")

# 14. Um punho solto simples (sem alternancia previa) NÃO suprime:
#     primeira frame FIST de uma mao que ja esta na vista -> pumping_until = 0
der = LeftHandDetector(cfg)
der.update((200.0, 200.0), 0.0, Gesture.FIST)
der.update((200.0, 200.0), 0.05, Gesture.FIST)
check("punho simples nao suprime (pumping_until=0)",
      der.pumping_until == 0.0, f"until={der.pumping_until}")



print(f"\n{passed} PASS / {failed} FAIL")
sys.exit(1 if failed else 0)
