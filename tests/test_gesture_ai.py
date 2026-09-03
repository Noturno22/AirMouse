
import numpy as np
import pytest

from core.gesture_ai import CLASSES, FEATURES, N_CLASSES, GestureAI, _normalize


def _skeleton_3d(seed=0):
    r = np.random.default_rng(seed)
    pts = r.uniform(-1.0, 1.0, (21, 3))
    pts[0] = [0.0, 0.0, 0.0]
    pts[9] = [0.0, 1.0, 0.0]
    return pts.astype(np.float64)


def _skeleton_2d(seed=0):
    r = np.random.default_rng(seed)
    pts = r.uniform(-1.0, 1.0, (21, 2))
    pts[0] = [0.0, 0.0]
    pts[9] = [0.0, 1.0]
    return pts.astype(np.float64)


class TestNormalize:
    def test_3d_shape(self):
        f = _normalize(_skeleton_3d())
        assert f is not None
        assert f.shape == (60,)

    def test_2d_fallback_shape(self):
        f = _normalize(_skeleton_2d())
        assert f is not None
        assert f.shape == (60,)

    def test_2d_z_features_are_zero(self):
        f = _normalize(_skeleton_2d())
        assert np.allclose(f[40:], 0.0)

    def test_rotation_invariance_xy(self):
        skel = _skeleton_3d(7)
        theta = np.pi / 3
        cos, sin = np.cos(theta), np.sin(theta)
        R = np.array([[cos, -sin, 0], [sin, cos, 0], [0, 0, 1]])
        rotated = skel @ R.T
        assert np.allclose(
            _normalize(skel)[:40], _normalize(rotated)[:40], atol=1e-10
        )

    def test_scale_invariance_xy(self):
        skel = _skeleton_3d(7)
        scaled = skel.copy()
        scaled[:, :2] = skel[:, :2] * 3.5 + 100.0
        assert np.allclose(
            _normalize(skel)[:40], _normalize(scaled)[:40], atol=1e-10
        )

    def test_z_relative_independent_of_xy_scale(self):
        skel = _skeleton_3d(7)
        scaled = skel.copy()
        scaled[:, :2] = skel[:, :2] * 3.5 + 100.0
        assert np.allclose(
            _normalize(skel)[40:], _normalize(scaled)[40:], atol=1e-10
        )

    def test_degenerate_returns_none(self):
        bad = np.zeros((21, 3))
        bad[9] = [1e-10, 1e-10, 0.0]
        assert _normalize(bad) is None


class TestConstants:
    def test_n_classes(self):
        assert N_CLASSES == 9

    def test_len_matches(self):
        assert len(CLASSES) == N_CLASSES

    def test_features(self):
        assert FEATURES == 120

    def test_rock_in_classes(self):
        names = [c.name for c in CLASSES]
        assert "ROCK" in names

    def test_shaka_in_classes(self):
        names = [c.name for c in CLASSES]
        assert "SHAKA" in names


class TestGestureAI:
    @pytest.fixture
    def tmp_models(self, tmp_path):
        old = tmp_path / "old_40.npz"
        ok = tmp_path / "ok_60.npz"
        bad_cls = tmp_path / "ok_cls.npz"
        np.savez_compressed(
            old,
            w1=np.zeros((40, 96)), b1=np.zeros(96),
            w2=np.zeros((96, 48)), b2=np.zeros(48),
            w3=np.zeros((48, N_CLASSES)), b3=np.zeros(N_CLASSES),
        )
        np.savez_compressed(
            ok,
            w1=np.zeros((FEATURES, 96)), b1=np.zeros(96),
            w2=np.zeros((96, 48)), b2=np.zeros(48),
            w3=np.zeros((48, N_CLASSES)), b3=np.zeros(N_CLASSES),
        )
        np.savez_compressed(
            bad_cls,
            w1=np.zeros((FEATURES, 96)), b1=np.zeros(96),
            w2=np.zeros((96, 48)), b2=np.zeros(48),
            w3=np.zeros((48, 7)), b3=np.zeros(7),
        )
        return old, ok, bad_cls

    def test_old_40_features_rejected(self, tmp_models):
        with pytest.raises(FileNotFoundError, match="features"):
            GestureAI(tmp_models[0])

    def test_wrong_class_count_rejected(self, tmp_models):
        with pytest.raises(FileNotFoundError, match="classes"):
            GestureAI(tmp_models[2])

    def test_valid_model_loads(self, tmp_models):
        ai = GestureAI(tmp_models[1])
        assert ai is not None

    def test_classify_returns_class_and_conf(self, tmp_models):
        ai = GestureAI(tmp_models[1])
        pred, conf = ai.classify(_skeleton_3d(5))
        assert pred in CLASSES
        assert 0.0 <= conf <= 1.0

    def test_classify_accepts_2d_input(self, tmp_models):
        ai = GestureAI(tmp_models[1])
        pred, conf = ai.classify(_skeleton_2d(5))
        assert pred in CLASSES or pred is None

    def test_classify_degenerate_returns_none(self, tmp_models):
        ai = GestureAI(tmp_models[1])
        degenerate = np.zeros((21, 3))
        degenerate[9] = [0.0, 1e-10, 0.0]
        pred, conf = ai.classify(degenerate)
        assert pred is None
        assert conf == 0.0

    def test_classify_window_of_frames(self, tmp_models):
        ai = GestureAI(tmp_models[1])
        local = np.random.default_rng(11)
        base = _skeleton_3d(5)
        frames = [base + local.uniform(0, 0.02, base.shape) for _ in range(5)]
        frames.append(_skeleton_3d(6))
        pred, conf = ai.classify(frames)
        assert pred in CLASSES
        assert 0.0 <= conf <= 1.0

    def test_classify_empty_window_none(self, tmp_models):
        ai = GestureAI(tmp_models[1])
        # todos os frames degenerados -> nenhum normalizavel
        bad = np.zeros((21, 3))
        pred, conf = ai.classify([bad, bad])
        assert pred is None
        assert conf == 0.0

    def test_classify_single_numpy_frame_not_list(self, tmp_models):
        # numpy (21,3) tratado como frame unico (nao como lista de frames)
        ai = GestureAI(tmp_models[1])
        pred, conf = ai.classify(_skeleton_3d(9))
        assert pred in CLASSES
