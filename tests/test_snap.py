"""Unit tests para a física do snap (core/snap.py).

Métodos puros testáveis sem UI Automation/thread: pull() (atração
magnética), fresh_center() (atualidade do alvo) e toggle()/status.
"""

import time

from core.snap import SnapEngine


def _mk_engine(enabled=True, radius=46.0, strength=0.35):
    eng = SnapEngine(radius_px=radius, strength=strength)
    eng.enabled = enabled  # independe de _AUTO_OK para testar a física
    return eng


def _set_center(eng, x, y, speed=0.0):
    with eng._lock:
        eng._center = (float(x), float(y))
        eng._ts = time.perf_counter()
        eng._speed = speed


def test_fresh_center_when_recent():
    eng = _mk_engine()
    _set_center(eng, 100, 100)
    now = time.perf_counter()
    assert eng.fresh_center(now, max_age_s=0.45) == (100.0, 100.0)


def test_fresh_center_none_when_stale():
    eng = _mk_engine()
    _set_center(eng, 100, 100)
    # Simula que o centro tem 1s de idade
    eng._ts = time.perf_counter() - 1.0
    assert eng.fresh_center(time.perf_counter(), max_age_s=0.45) is None


def test_fresh_center_none_when_no_center():
    eng = _mk_engine()
    assert eng.fresh_center(time.perf_counter()) is None


def test_pull_zero_when_disabled():
    eng = _mk_engine(enabled=False)
    _set_center(eng, 100, 100)
    assert eng.pull((90, 90), time.perf_counter()) == (0.0, 0.0)


def test_pull_zero_outside_radius():
    eng = _mk_engine(radius=46.0)
    # centrar a 200px de distância > raio
    _set_center(eng, 300, 100)
    assert eng.pull((100, 100), time.perf_counter()) == (0.0, 0.0)


def test_pull_attracts_toward_center():
    eng = _mk_engine(radius=46.0, strength=0.35)
    # centro a (110,100), cursor a (100,100) → atração para +x
    _set_center(eng, 110, 100)
    px, py = eng.pull((100, 100), time.perf_counter())
    assert px > 0.0
    assert abs(py) < 1e-6
    # atração mais forte quanto mais perto (mas nunca mais que o alvo)
    assert px <= 10.0


def test_pull_zero_when_cursor_on_center():
    eng = _mk_engine()
    _set_center(eng, 100, 100)
    assert eng.pull((100, 100), time.perf_counter()) == (0.0, 0.0)


def test_pull_zero_when_fast():
    eng = _mk_engine()
    _set_center(eng, 110, 100, speed=5000.0)  # > 1100 → sem snap em movimento rápido
    assert eng.pull((100, 100), time.perf_counter()) == (0.0, 0.0)


def test_pull_capped_magnitude():
    eng = _mk_engine(radius=200.0, strength=1.0)
    # Dentro do raio, mas a uma distância que geraria atração > cap(22)
    _set_center(eng, 160, 160)
    px, py = eng.pull((100, 100), time.perf_counter())
    mag = (px * px + py * py) ** 0.5
    assert 0.0 < mag <= 22.0 + 1e-6


def test_assist_point_returns_center_when_near():
    eng = _mk_engine(radius=46.0)
    _set_center(eng, 120, 120)
    assert eng.assist_point((110, 110), time.perf_counter()) == (120.0, 120.0)
    # longe demais → None
    assert eng.assist_point((200, 200), time.perf_counter()) is None


def test_toggle_flips_enabled_and_status():
    eng = _mk_engine(enabled=True)
    assert eng.status in ("ON", "off")  # status depende de _AUTO_OK
    en = eng.enabled
    toggled = eng.toggle()
    assert eng.enabled == (not en)
    assert isinstance(toggled, str)
