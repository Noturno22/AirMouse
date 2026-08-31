import sys
import time

sys.path.insert(0, ".")

from config import Config
from core.filters import AccelCurve
from core.gestures import Gesture
from core.light import LightBoost
from core.motion import SmoothEmitter, lead_offset
from core.mouse_ctl import MouseCtl
from core.nlu import parse_local
from core.snap import SnapEngine
from core.twohand import ClapDetector, HandPool, MagnifierCtl

PASS = []
FAIL = []


def check(name, cond, extra=""):
    if cond:
        PASS.append(name)
        print(f"PASS {name}")
    else:
        FAIL.append(name)
        print(f"FAIL {name} {extra}")


class FakeMouse:
    def __init__(self):
        self.moves = []

    def move_by(self, dx, dy):
        self.moves.append((int(dx), int(dy)))


def t_emitter_conservation():
    fm = FakeMouse()
    em = SmoothEmitter(fm, rate_hz=180.0)
    em.start()
    total_x, total_y = 0.0, 0.0
    for i in range(30):
        dx, dy = 10.0, -4.0
        em.push(dx, dy, 0.02)
        total_x += dx
        total_y += dy
        time.sleep(0.006)
    # Espera terminantemente o flush do pendente. Depois do último push, o
    # ramo idle do emissor descarrega tudo de uma vez; um deadline generoso
    # apenas protege contra máquina lenta/sobrecarga sem afetar a asserção.
    deadline = time.time() + 5.0
    while time.time() < deadline and em.pending > 0.5:
        time.sleep(0.02)
    time.sleep(0.1)
    em.stop()
    ex = sum(m[0] for m in fm.moves)
    ey = sum(m[1] for m in fm.moves)
    check(
        "emitter conservacao",
        abs(ex - round(total_x)) <= 2 and abs(ey - round(total_y)) <= 2,
        f"emit=({ex},{ey}) want=({round(total_x)},{round(total_y)})",
    )


def t_emitter_clear():
    fm = FakeMouse()
    em = SmoothEmitter(fm, rate_hz=180.0)
    em.start()
    em.push(80.0, 60.0, 0.05)
    em.clear()
    time.sleep(0.08)
    em.stop()
    check("emitter clear zera budget", len(fm.moves) == 0, str(fm.moves))


def t_lead_offset():
    lx, ly = lead_offset(1000.0, -500.0, 40.0)
    check("lead offset", abs(lx - 40.0) < 1e-6 and abs(ly + 20.0) < 1e-6)


def t_accel_expo():
    c = AccelCurve(1.2, 3.0, 1400.0, expo=1.7)
    g0 = c.apply(0.0, 0.0)
    gmid = c.apply(700.0, 0.0)
    gmax = c.apply(9000.0, 0.0)
    mono = g0 <= gmid <= gmax
    check(
        "accel expo monotonic + endpoints",
        mono
        and abs(g0 - 1.2) < 1e-9
        and abs(gmax - 3.0) < 1e-9
        and gmid > 1.2,
        f"{g0:.2f},{gmid:.2f},{gmax:.2f}",
    )
    c0 = AccelCurve(1.2, 3.0, 1400.0, expo=0.0)
    gm0 = c0.apply(700.0, 0.0)
    expected = 1.2 + 1.8 * (0.5 * 0.5 * (3 - 1.0))
    check("accel smoothstep legacy", abs(gm0 - expected) < 1e-6, f"{gm0:.3f}")


def t_mouse_fractional():
    mc = MouseCtl.__new__(MouseCtl)

    class Rec:
        def __init__(self):
            self.position = (500, 500)

    mc.mouse = Rec()
    mc.screen_w, mc.screen_h = 1920, 1080
    mc._scroll_acc = 0.0
    mc._frac_x = 0.0
    mc._frac_y = 0.0
    start_pos = mc.mouse.position
    for _ in range(10):
        mc.move_by(0.4, 0.0)
    moved = mc.mouse.position[0] - start_pos[0]
    check("mouse sub-pixel acumula", moved == 4, f"moved={moved} frac={mc._frac_x:.2f}")


def t_clap():
    cd = ClapDetector()
    scales = [100.0, 100.0]
    fired = False
    t = time.perf_counter()
    cd.update([(100.0, 300.0), (520.0, 300.0)], scales, t)
    for bx in [480, 430, 350, 230, 205]:
        t += 0.033
        if cd.update([(100.0, 300.0), (float(bx), 300.0)], scales, t):
            fired = True
    check("clap dispara apos aproximacao", fired)
    again = cd.update([(100.0, 300.0), (205.0, 300.0)], scales, t + 0.05)
    check("clap sem refire imediato", not again)


def t_magnifier():
    m = MagnifierCtl(step_frac=0.85)
    launches = []
    m._launch_magnifier = lambda: launches.append(1) or True

    presses = []

    class RecKB:
        def press(self, k):
            presses.append(("p", str(k)))

        def release(self, k):
            presses.append(("r", str(k)))

    m.kb = RecKB()
    now = time.perf_counter()
    for i in range(6):
        m.update(
            [
                (Gesture.OPEN, (300.0, 300.0), 100.0),
                (Gesture.OPEN, (520.0, 300.0), 100.0),
            ],
            now + i * 0.03,
        )
    entered = m.on and launches
    check("lupa entra com 2 maos abertas", bool(entered))
    plus_steps = 0
    for j in range(12):
        m.update(
            [
                (Gesture.OPEN, (280.0, 300.0), 100.0),
                (Gesture.OPEN, (600.0 + j * 40.0, 300.0), 100.0),
            ],
            now + 1.0 + j * 0.2,
        )
    plus_steps = sum(
        1
        for i in range(1, len(presses))
        if presses[i][1] == "+" and presses[i - 1][1] == "Key.cmd"
    )
    check("lupa zoom+ por afastamento", plus_steps >= 5, f"steps={plus_steps}")
    m.update([], now + 5.0)
    note_off = m.update([], now + 5.5)
    check("lupa sai sem maos", note_off == "LUPA OFF", str(note_off))


def t_nlu_new():
    cases = [
        ("abre o assistente", "assistant"),
        ("assistente", "assistant"),
        ("fecha o assistente", "assistant_close"),
        ("ampliar", "magnify_on"),
        ("zoom", "magnify_on"),
        ("lupa", "magnify_on"),
        ("tirar a ampliacao", "magnify_off"),
        ("tirar a ampliação", "magnify_off"),
        ("menos ampliacao", "magnify_off"),
        ("snap", "snap_toggle"),
        ("pausa", "pause"),
        ("clique direito", "right_click"),
        ("mais rapido", "gain_up"),
        ("abrir um documento", None),
    ]
    ok = True
    detail = []
    for text, want in cases:
        got = parse_local(text)[0]
        if got != want:
            ok = False
            detail.append(f"{text!r}->{got}(want {want})")
    check("nlu intencoes novas+regressao", ok, "; ".join(detail))


def t_light():
    lb = LightBoost(low=40, high=60, frames=3, check_every=1)
    saw_on = False
    saw_off = False
    for _ in range(5):
        if lb.feed(30.0) == "on":
            saw_on = True
    for _ in range(5):
        if lb.feed(70.0) == "off":
            saw_off = True
    check("light histerese on/off", saw_on and saw_off and not lb.active)


def t_handpool():
    cfg = Config()
    pool = HandPool(cfg, None)
    lm = [(0.5 + 0.001 * i, 0.5, 0.0) for i in range(21)]
    res = pool.update([lm], ["Right"], 640, 480)
    check("pool mao unica right", set(res) == {"Right"})
    res2 = pool.update([lm], ["Left"], 640, 480)
    check("pool troca para left", set(res2) == {"Left"})
    check("pool reset lado ausente", pool.engines["Right"]._committed == Gesture.NONE)


def t_snap_disabled_safe():
    se = SnapEngine(enabled=False)
    p = se.pull((500, 500), time.perf_counter())
    check("snap desativado nao puxa", p == (0.0, 0.0))


if __name__ == "__main__":
    t_emitter_conservation()
    t_emitter_clear()
    t_lead_offset()
    t_accel_expo()
    t_mouse_fractional()
    t_clap()
    t_magnifier()
    t_nlu_new()
    t_light()
    t_handpool()
    t_snap_disabled_safe()
    print(f"\n{len(PASS)} PASS / {len(FAIL)} FAIL")
    sys.exit(1 if FAIL else 0)
