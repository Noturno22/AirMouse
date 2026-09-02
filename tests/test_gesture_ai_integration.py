import numpy as np
import pytest

from config import Config
from core.gesture_ai import _normalize
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
    lm = [(p[0] / 640, p[1] / 480, z) for (p, z) in zip(pts2, skel[:, 2])]
    for _ in range(5):
        eng.update(lm, 640, 480)


class _StubAI:
    def __init__(self, gesture, conf=0.9):
        self.gesture = gesture
        self.conf = conf

    def classify(self, pts):
        return self.gesture, self.conf


def test_ai_receives_3d_points():
    captured = []
    class SpyAI:
        def classify(self, pts):
            captured.append(pts)
            return Gesture.OPEN, 0.0
    eng = GestureEngine(Config(), gesture_ai=SpyAI())
    skel = synthesize(Gesture.OPEN, np.random.default_rng(3)).astype(float)
    pts2 = skel[:, :2] * 150 + np.array([320.0, 240.0])
    lm = [(p[0] / 640, p[1] / 480, z) for (p, z) in zip(pts2, skel[:, 2])]
    eng.update(lm, 640, 480)
    assert captured
    c = np.asarray(captured[0])
    assert c.ndim == 2
    assert c.shape[1] == 3
