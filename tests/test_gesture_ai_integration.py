import numpy as np

from config import Config
from core.gestures import Gesture, GestureEngine
from tools.train_gesture_ai import synthesize


def _engine():
    cfg = Config()
    return GestureEngine(cfg, gesture_ai=None)


def test_update_accepts_2d_landmarks():
    eng = _engine()
    skel = synthesize(Gesture.OPEN, np.random.default_rng(1)).astype(float)
    pts = skel[:, :2] * 150 + np.array([320.0, 240.0])
    lm = [(p[0] / 640, p[1] / 480) for p in pts]
    # nao deve lancar excecao
    for _ in range(5):
        eng.update(lm, 640, 480)


def test_update_accepts_3d_landmarks():
    eng = _engine()
    skel = synthesize(Gesture.OPEN, np.random.default_rng(2)).astype(float)
    pts2 = skel[:, :2] * 150 + np.array([320.0, 240.0])
    lm = [(p[0] / 640, p[1] / 480, z) for (p, z) in zip(pts2, skel[:, 2], strict=True)]
    for _ in range(5):
        eng.update(lm, 640, 480)


class _StubAI:
    def __init__(self, gesture, conf=0.9):
        self.gesture = gesture
        self.conf = conf

    def classify(self, pts):
        return self.gesture, self.conf


def test_ai_receives_window_of_3d_points():
    captured = []
    class SpyAI:
        def classify(self, pts):
            captured.append(pts)
            return Gesture.OPEN, 0.0
    eng = GestureEngine(Config(), gesture_ai=SpyAI())
    skel = synthesize(Gesture.OPEN, np.random.default_rng(3)).astype(float)
    pts2 = skel[:, :2] * 150 + np.array([320.0, 240.0])
    lm = [(p[0] / 640, p[1] / 480, z) for (p, z) in zip(pts2, skel[:, 2], strict=True)]
    for _ in range(3):
        eng.update(lm, 640, 480)
    assert captured
    c = np.asarray(captured[-1], dtype=float)
    # janela recebida pelo classify: lista de frames (W, 21, 3)
    assert c.ndim == 3
    assert c.shape[1] == 21 and c.shape[2] == 3


def test_ai_window_capped_by_config():
    cfg = Config()
    cfg.ai_window = 2
    captured = []
    class SpyAI:
        def classify(self, pts):
            captured.append(pts)
            return Gesture.OPEN, 0.0
    eng = GestureEngine(cfg, gesture_ai=SpyAI())
    skel = synthesize(Gesture.OPEN, np.random.default_rng(4)).astype(float)
    pts2 = skel[:, :2] * 150 + np.array([320.0, 240.0])
    lm = [(p[0] / 640, p[1] / 480, z) for (p, z) in zip(pts2, skel[:, 2], strict=True)]
    for _ in range(7):
        eng.update(lm, 640, 480)
    c = np.asarray(captured[-1], dtype=float)
    assert c.shape[0] == 2  # limitado por ai_window=2


def test_reset_clears_ai_window():
    cfg = Config()
    called = []
    class SpyAI:
        def classify(self, pts):
            called.append(pts)
            return Gesture.OPEN, 0.0
    eng = GestureEngine(cfg, gesture_ai=SpyAI())
    skel = synthesize(Gesture.OPEN, np.random.default_rng(5)).astype(float)
    pts2 = skel[:, :2] * 150 + np.array([320.0, 240.0])
    lm = [(p[0] / 640, p[1] / 480, z) for (p, z) in zip(pts2, skel[:, 2], strict=True)]
    eng.update(lm, 640, 480)
    eng.reset()
    assert len(eng._ai_window) == 0
