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

# 6. PEACE ("paz") com a mao esquerda -> gui_toggle (rising edge)
def feed_gesture(det, seq, dt=0.05):
    out = []
    for i, g in enumerate(seq):
        ev, val = det.update((200.0, 200.0), i * dt, g)
        if ev is not None:
            out.append((ev, val))
    return out

der = LeftHandDetector(cfg)
seq_peace = [Gesture.OPEN, Gesture.PEACE]
evs = feed_gesture(der, seq_peace)
check("PEACE mao esquerda -> gui_toggle", ("gui_toggle", None) in evs, str(evs))

# 7. Segurar PEACE nao repete o toggle (disparo unico enquanto parada no gesto)
der = LeftHandDetector(cfg)
seq_hold = [Gesture.OPEN, Gesture.PEACE, Gesture.PEACE, Gesture.PEACE]
evs = feed_gesture(der, seq_hold)
toggles = [e for e, _ in evs if e == "gui_toggle"]
check("segurar PEACE dispara uma so vez", toggles == ["gui_toggle"], str(evs))

# 8. OPEN/FIST (sem PEACE) nao dispara gui_toggle
der = LeftHandDetector(cfg)
evs = feed_gesture(der, [Gesture.OPEN, Gesture.OPEN])
check("sem PEACE -> sem gui_toggle", ("gui_toggle", None) not in evs, str(evs))

# 8b. Sair do PEACE e voltar a fazer (apos o cooldown) volta a ligar/desligar
der = LeftHandDetector(cfg)
evs = []
now = 0.0
for g in (Gesture.OPEN, Gesture.PEACE, Gesture.OPEN):
    ev, val = der.update((200.0, 200.0), now, g)
    if ev is not None:
        evs.append((ev, val))
    now += 0.05
now += cfg.left_hand_cooldown_s + 0.1
ev, val = der.update((200.0, 200.0), now, Gesture.PEACE)
if ev is not None:
    evs.append((ev, val))
count = sum(1 for e, _ in evs if e == "gui_toggle")
check("novo PEACE apos cooldown volta a ligar/desligar", count == 2, str(evs))

# 9. Swipe continua a funcionar mesmo com gesture presente (sem disparo de gui_toggle)
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

# ── Modo Free (allow_commands=False): PEACE funciona, comandos nao ────
free = LeftHandDetector(cfg, allow_commands=False)

# 13. PEACE com a mao esquerda AINDA mostra/oculta a interface no Free
now = 0.0
init = free.update((200.0, 200.0), now, Gesture.FIST)
now += 0.2
evs = []
for g in (Gesture.PEACE, Gesture.PEACE, Gesture.PEACE):
    now += cfg.left_hand_cooldown_s + 0.4
    ev, val = free.update((200.0, 200.0), now, g)
    if ev is not None:
        evs.append(ev)
check("FREE: PEACE mao esquerda -> gui_toggle", ("gui_toggle", None) in evs or "gui_toggle" in evs, str(evs))

# 14. O swipe NAO dispara no Free (comandos desligados)
free2 = LeftHandDetector(cfg, allow_commands=False)
evs = feed(free2, swipe_right)
check("FREE: swipe nao dispara alt_tab", not any(e == "alt_tab_forward" for e, _ in evs), str(evs))

# 15. Segurar mao aberta NAO abre o alternador no Free
free3 = LeftHandDetector(cfg, allow_commands=False)
now = 0.0
sw_evs = []
hold_dt = 0.05
while now < cfg.left_hand_open_switch_s + 0.3:
    ev, val = free3.update((200.0, 200.0), now, Gesture.OPEN)
    if ev is not None:
        sw_evs.append(ev)
    now += hold_dt
check("FREE: segurar aberta nao abre alternador",
      "alt_switch_open" not in sw_evs, str(sw_evs))

# 16. Scroll vertical NAO dispara no Free
free4 = LeftHandDetector(cfg, allow_commands=False)
evs = feed(free4, [(100.0, 100.0), (100.0, 120.0), (100.0, 140.0),
                   (100.0, 160.0), (100.0, 180.0), (100.0, 200.0)])
check("FREE: scroll nao dispara", not any(e == "scroll" for e, _ in evs), str(evs))

# ── Fix espacial: a mao de comandos é a mais à esquerda do ecra ─────────
from core.engine import _command_hand_frame

# _command_hand_frame recebe dict {label: (HandFrame, event, value)}. HandFrame
# precisa de palm_center; criamos objetos mínimos via types.SimpleNamespace.
import types  # noqa: E402

def mk_frame(x, y):
    return types.SimpleNamespace(palm_center=(x, y))

# 17. Duas maos com o MESMO label 'Right' (falha real do MediaPipe): a de
# comandos deve ser a de menor X (mais à esquerda do ecra), independentemente
# dos labels serem iguais/instáveis.
res_both_right = {
    "Right": (mk_frame(400.0, 200.0), None, None),
    "Right2": (mk_frame(120.0, 180.0), None, None),
}
sel = _command_hand_frame(res_both_right, mirror=True, frame_w=640)
check("espacial: 2x'Right' -> escolhe menor X na metade esquerda",
      sel is not None and sel[0].palm_center[0] == 120.0,
      str(sel[0].palm_center) if sel else "None")

# 18. Com labels trocados (o MediaPipe rotulou a mao esquerda como 'Left'), a
# seleção espacial continua a apanhar a esquerda pela posição, não pelo label.
res_troca = {
    "Left": (mk_frame(600.0, 200.0), None, None),
    "Right": (mk_frame(90.0, 180.0), None, None),
}
sel2 = _command_hand_frame(res_troca, mirror=True, frame_w=640)
check("espacial: labels trocados ainda escolhe menor X",
      sel2 is not None and sel2[0].palm_center[0] == 90.0,
      str(sel2[0].palm_center) if sel2 else "None")

# 19. Mão direita SOZINHA (x no lado direito) NÃO é tratada como mão de
# comandos → evita que mover o cursor com a direita abra o alternador.
res_dir_sozinha = {"Left": (mk_frame(500.0, 200.0), None, None)}
sel3 = _command_hand_frame(res_dir_sozinha, mirror=True, frame_w=640)
check("espacial: maodireita sozinha (X>half) nao e a de comandos",
      sel3 is None, str(sel3[0].palm_center) if sel3 else "None")

print(f"\n{passed} PASS / {failed} FAIL")
sys.exit(1 if failed else 0)
