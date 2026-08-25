import os
import urllib.request
import zipfile

import numpy as np

from core.gestures import Gesture

CLASSES = (
    Gesture.OPEN,
    Gesture.PINCH,
    Gesture.PINCH_MID,
    Gesture.FIST,
    Gesture.PEACE,
    Gesture.THREE,
    Gesture.THUMB_UP,
)
FEATURES = 40
N_CLASSES = len(CLASSES)

MODEL_URLS = (
    "https://github.com/airmouse-ai/models/releases/download/v1/gesture_mlp.npz",
)


def _normalize(points):
    pts = np.asarray(points, dtype=np.float64)[:, :2]
    wrist = pts[0]
    v = pts[9] - wrist
    scale = np.hypot(v[0], v[1])
    if scale < 1e-6:
        return None
    theta = -np.arctan2(v[1], v[0])
    cos, sin = np.cos(theta), np.sin(theta)
    rel = pts[1:] - wrist
    x = rel[:, 0] * cos - rel[:, 1] * sin
    y = rel[:, 0] * sin + rel[:, 1] * cos
    return np.concatenate([x / scale, y / scale])


class GestureAI:
    def __init__(self, path):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        data = np.load(path)
        self.w1, self.b1 = data["w1"], data["b1"]
        self.w2, self.b2 = data["w2"], data["b2"]
        self.w3, self.b3 = data["w3"], data["b3"]
        if self.b3.shape[0] != N_CLASSES:
            raise FileNotFoundError(
                f"modelo obsoleto em {path} ({self.b3.shape[0]} classes; "
                f"esperado {N_CLASSES}). Retreina: tools\\train_gesture_ai.py"
            )

    def classify(self, points_px):
        feat = _normalize(points_px)
        if feat is None:
            return None, 0.0
        h1 = np.tanh(feat @ self.w1 + self.b1)
        h2 = np.tanh(h1 @ self.w2 + self.b2)
        logits = h2 @ self.w3 + self.b3
        e = np.exp(logits - logits.max())
        prob = e / e.sum()
        idx = int(prob.argmax())
        return CLASSES[idx], float(prob[idx])


def ensure_ai_model(path, url=None):
    if os.path.isfile(path):
        return path
    parent = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(parent, "gesture_mlp.npz")
    if os.path.isfile(local):
        import shutil

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        shutil.copyfile(local, path)
        return path
    urls = (url,) if url else MODEL_URLS
    for u in urls:
        try:
            print(f"A baixar modelo de gestos IA para {path} ...")
            tmp = path + ".part"
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            urllib.request.urlretrieve(u, tmp)
            os.replace(tmp, path)
            print("Modelo IA pronto.")
            return path
        except Exception:
            continue
    raise FileNotFoundError(
        "Modelo gesture_mlp.npz nao encontrado. Corre: "
        ".venv\\Scripts\\python.exe tools\\train_gesture_ai.py"
    )
