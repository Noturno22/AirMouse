"""Tests for the runtime block gate inside process_frame (via state flag).

O gate lê ``state["license_blocked"]`` (set no arranque pelo main.py/UI) OU
``active_license().is_blocked()`` e devolve cedo SEM mover o rato quando
bloqueado. O teste usa a flag de estado (NÃO ``_forceblock``).
"""
import types

import numpy as np

import core.licensing as lic
from config import Config
from core import engine


class _NoopMouse:
    def __init__(self):
        self.moved = False
        self.moved_by = False

    def move(self, *a, **k):
        self.moved = True

    def move_by(self, *a, **k):
        self.moved_by = True

    def click(self, *a, **k):
        pass

    def press_left(self, *a, **k):
        pass

    def release_left(self, *a, **k):
        pass

    def right_click(self, *a, **k):
        pass

    def scroll(self, *a, **k):
        pass

    class mouse:
        position = (100.0, 100.0)


class _NoopCam:
    """Devolve um frame sintético NÃO-None para o motor passar o early-return
    (``if frame is None``) e chegar ao gate."""

    def __init__(self):
        self._frame = np.zeros((240, 320, 3), dtype=np.uint8)

    def read(self):
        return self._frame, 0

    def try_boost_exposure(self):
        pass


class _NoopTracker:
    """Tracker falso: nenhuma mão detetada -> sem movimento (sem crash)."""

    def process(self, rgb, ts_ms):
        return [], []


class _NoopTuner:
    enabled = False

    def feed(self, *a, **k):
        pass

    def maybe_apply(self, *a, **k):
        return None

    def set_user_gain(self, *a, **k):
        pass

    def toggle(self):
        return "OFF"


class _FakeEmitter:
    def __init__(self):
        self.pushed = 0

    def start(self):
        pass

    def stop(self):
        pass

    def push(self, *a, **k):
        self.pushed += 1

    def clear(self):
        pass


def _make_engine(cfg):
    ctx = types.SimpleNamespace(
        assistant=None, speaker=None, snap=None, magnifier=None,
        exit_requested=False,
    )
    E = engine.make_engine_ctx(cfg, -1, None, _NoopTuner(), ctx)
    E.emitter = _FakeEmitter()
    return E, ctx


def _base_cfg():
    cfg = Config()
    # Passa direto do warmup e desliga extras para a pipeline correr limpa.
    cfg.warmup_frames = 0
    cfg.low_light_boost = False
    return cfg


def _state(**over):
    s = {
        "license_blocked": False,
        "_license_warned": False,
        "paused": False,
        "freeze_until": 0.0,
        "button_down": False,
        "flash": 0,
        "smooth_name": "NORMAL",
        "dbg_until": 0.0,
    }
    s.update(over)
    return s


def test_process_frame_blocks_when_license_blocked(monkeypatch):
    """Com license_blocked=True o gate devolve cedo e o rato NÃO se move."""
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=60)
    lm.report_usage(60)  # esgota o trial -> is_blocked() True
    monkeypatch.setattr(engine, "active_license", lambda: lm)

    cfg = _base_cfg()
    E, ctx = _make_engine(cfg)
    mouse = _NoopMouse()
    cam = _NoopCam()
    tracker = _NoopTracker()
    state = _state(license_blocked=True)

    snap = engine.process_frame(
        cfg, cam, tracker, mouse, None, None, _NoopTuner(), ctx, state, E,
    )

    assert mouse.moved is False
    assert mouse.moved_by is False
    # O gate devolve o shape de bloqueio: sem render.
    assert snap["to_render"] is False
    assert snap["frame"] is not None
    assert snap["done"] is False
    assert state["_license_warned"] is True


def test_process_frame_blocks_via_active_license(monkeypatch):
    """Sem a flag no state mas com a license ativa bloqueada, o gate bloqueia."""
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=60)
    lm.report_usage(60)
    monkeypatch.setattr(engine, "active_license", lambda: lm)

    cfg = _base_cfg()
    E, ctx = _make_engine(cfg)
    mouse = _NoopMouse()
    cam = _NoopCam()
    tracker = _NoopTracker()
    # flag no state falsa, mas is_blocked() da licença é True.
    state = _state(license_blocked=False)

    snap = engine.process_frame(
        cfg, cam, tracker, mouse, None, None, _NoopTuner(), ctx, state, E,
    )

    assert mouse.moved is False
    assert mouse.moved_by is False
    assert snap["to_render"] is False


def test_process_frame_not_blocked_passes_gate(monkeypatch):
    """Sem bloqueio o gate NÃO sacode o frame: processa até ao fim."""
    lm = lic.LicenseManager(store_path=":memory:", trial_seconds=60)
    monkeypatch.setattr(engine, "active_license", lambda: lm)

    cfg = _base_cfg()
    E, ctx = _make_engine(cfg)
    mouse = _NoopMouse()
    cam = _NoopCam()
    tracker = _NoopTracker()
    state = _state(license_blocked=False)

    snap = engine.process_frame(
        cfg, cam, tracker, mouse, None, None, _NoopTuner(), ctx, state, E,
    )

    # O gate não ativou: não devolve o shape de bloqueio (to_render True).
    assert snap["to_render"] is True
    assert state["_license_warned"] is False
