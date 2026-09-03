import argparse
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.gesture_ai import CLASSES, FEATURES, N_CLASSES, GestureAI, _normalize
from core.gestures import Gesture

RNG = np.random.default_rng(7)

OPEN_SKELETON = {
    0: (0.00, 0.00),
    1: (-0.32, -0.26),
    5: (0.46, -1.02),
    9: (0.02, -1.10),
    13: (-0.42, -1.04),
    17: (-0.82, -0.82),
}
FINGER_LEN = {
    "index": (0.58, 0.42, 0.32),
    "middle": (0.62, 0.46, 0.33),
    "ring": (0.56, 0.41, 0.30),
    "pinky": (0.44, 0.29, 0.22),
    "thumb": (0.34, 0.32, 0.28),
}
MAX_ANGLES = np.deg2rad([78.0, 98.0, 62.0])
THUMB_MAX = np.deg2rad([38.0, 34.0, 30.0])
FINGER_CHAINS = {
    "index": ((5, 6, 7, 8), np.deg2rad(-84.0)),
    "middle": ((9, 10, 11, 12), np.deg2rad(-90.0)),
    "ring": ((13, 14, 15, 16), np.deg2rad(-97.0)),
    "pinky": ((17, 18, 19, 20), np.deg2rad(-112.0)),
}


def _chain(base, ang0, lengths, curls, max_angles, fold_gain=0.22):
    pts = []
    p = np.asarray(base, dtype=np.float64)[:2]
    z = 0.0
    ang = ang0
    pts.append(np.array([p[0], p[1], z]))
    for L, amax, c in zip(lengths, max_angles, curls, strict=True):
        ang += float(c) * amax
        # z: dedos dobrados aproximam-se da câmara (negativo resp. ao pulso).
        # Só acumula com a dobragem (c) — dedo esticado mantém z ~ 0.
        z += -L * amax * c * fold_gain
        p = p + L * np.array([np.cos(ang), np.sin(ang)])
        pts.append(np.array([p[0], p[1], z]))
    return pts


def _thumb(curls):
    return _chain(
        OPEN_SKELETON[1], np.deg2rad(-118.0), FINGER_LEN["thumb"], curls, THUMB_MAX
    )


def synthesize(gesture, rng):
    skel = [None] * 21

    def jitter(a=0.05):
        return rng.uniform(-a, a)

    skel[0] = np.array([OPEN_SKELETON[0][0], OPEN_SKELETON[0][1], 0.0])
    skel[1] = np.array(
        [OPEN_SKELETON[1][0] + jitter(0.03), OPEN_SKELETON[1][1] + jitter(0.03), 0.0]
    )

    t_curls = (jitter(0.15), 0.15 + jitter(0.1), 0.1 + jitter(0.1))
    th = _thumb(t_curls)
    skel[2], skel[3], skel[4] = th[1], th[2], th[3]

    def finger(name, base_id, curl_base, spread=0.0):
        ids, ang0 = FINGER_CHAINS[name]
        lengths = tuple(L * (1.0 + jitter(0.08)) for L in FINGER_LEN[name])
        curls = tuple(min(max(c + jitter(0.12), 0.0), 1.0) for c in curl_base)
        base = np.array(
            [OPEN_SKELETON[base_id][0] + jitter(0.04),
             OPEN_SKELETON[base_id][1] + jitter(0.04), 0.0]
        )
        pts = _chain(base, ang0 + spread, lengths, curls, MAX_ANGLES)
        for k, i in enumerate(ids):
            skel[i] = pts[k]

    if gesture == Gesture.OPEN:
        cb = (0.06, 0.04, 0.03)
        finger("index", 5, cb, jitter(0.09))
        finger("middle", 9, cb, jitter(0.07))
        finger("ring", 13, cb, jitter(0.07))
        finger("pinky", 17, cb, jitter(0.09))
    elif gesture == Gesture.FIST:
        finger("index", 5, (0.94, 0.97, 0.92), jitter(0.05))
        finger("middle", 9, (0.94, 0.97, 0.92), jitter(0.05))
        finger("ring", 13, (0.94, 0.97, 0.92), jitter(0.05))
        finger("pinky", 17, (0.96, 0.98, 0.9), jitter(0.05))
        # polegar dobrado sobre a palma (evita confundir com THUMB_UP)
        skel[2] = np.array([-0.32 + jitter(0.03), -0.26 + jitter(0.03), -0.30])
        skel[3] = np.array([-0.45 + jitter(0.04), -0.50 + jitter(0.04), -0.34])
        skel[4] = np.array([-0.36 + jitter(0.04), -0.70 + jitter(0.04), -0.38])
    elif gesture == Gesture.PEACE:
        finger("index", 5, (0.05, 0.04, 0.03), jitter(0.06))
        finger("middle", 9, (0.05, 0.04, 0.03), jitter(0.06))
        finger("ring", 13, (0.93, 0.95, 0.9), jitter(0.05))
        finger("pinky", 17, (0.95, 0.96, 0.9), jitter(0.05))
    elif gesture == Gesture.ROCK:
        finger("index", 5, (0.05, 0.04, 0.03), jitter(0.06))
        finger("pinky", 17, (0.06, 0.04, 0.03), jitter(0.06))
        finger("middle", 9, (0.93, 0.95, 0.9), jitter(0.05))
        finger("ring", 13, (0.94, 0.95, 0.9), jitter(0.05))
    elif gesture == Gesture.SHAKA:
        finger("index", 5, (0.92, 0.95, 0.9), jitter(0.05))
        finger("middle", 9, (0.93, 0.95, 0.9), jitter(0.05))
        finger("ring", 13, (0.94, 0.95, 0.9), jitter(0.05))
        # polegar + mindinho esticados (espécime do "hang loose")
        finger("pinky", 17, (0.05, 0.04, 0.03), jitter(0.06))
        t_curls = (0.05, 0.04, 0.03)
        th = _thumb(t_curls)
        skel[2], skel[3], skel[4] = th[1], th[2], th[3]
    elif gesture == Gesture.PINCH:
        finger("index", 5, (0.52, 0.72, 0.78), jitter(0.05))
        finger("middle", 9, (0.18, 0.14, 0.1), jitter(0.06))
        finger("ring", 13, (0.35, 0.3, 0.25), jitter(0.06))
        finger("pinky", 17, (0.4, 0.35, 0.3), jitter(0.06))
        t_curls = (0.3, 0.28, 0.25)
        th = _thumb(t_curls)
        skel[2], skel[3], skel[4] = th[1], th[2], th[3]
        gap = skel[4] - skel[8]
        skel[8] = skel[8] + gap * rng.uniform(0.75, 0.95)
        skel[7] = skel[7] + gap * rng.uniform(0.25, 0.45)
    elif gesture == Gesture.PINCH_MID:
        finger("index", 5, (0.16, 0.12, 0.09), jitter(0.06))
        finger("middle", 9, (0.54, 0.74, 0.78), jitter(0.05))
        finger("ring", 13, (0.36, 0.31, 0.26), jitter(0.06))
        finger("pinky", 17, (0.42, 0.36, 0.3), jitter(0.06))
        t_curls = (0.3, 0.28, 0.25)
        th = _thumb(t_curls)
        skel[2], skel[3], skel[4] = th[1], th[2], th[3]
        gap = skel[4] - skel[12]
        skel[12] = skel[12] + gap * rng.uniform(0.75, 0.95)
        skel[11] = skel[11] + gap * rng.uniform(0.25, 0.45)
    elif gesture == Gesture.THREE:
        finger("index", 5, (0.05, 0.04, 0.03), jitter(0.07))
        finger("middle", 9, (0.05, 0.04, 0.03), jitter(0.07))
        finger("ring", 13, (0.07, 0.05, 0.04), jitter(0.07))
        finger("pinky", 17, (0.93, 0.96, 0.92), jitter(0.05))
        t_curls = (0.18 + jitter(0.1), 0.15 + jitter(0.08), 0.12 + jitter(0.08))
        th = _thumb(t_curls)
        skel[2], skel[3], skel[4] = th[1], th[2], th[3]
    elif gesture == Gesture.THUMB_UP:
        finger("index", 5, (0.94, 0.97, 0.92), jitter(0.05))
        finger("middle", 9, (0.94, 0.97, 0.92), jitter(0.05))
        finger("ring", 13, (0.94, 0.96, 0.9), jitter(0.05))
        finger("pinky", 17, (0.95, 0.97, 0.9), jitter(0.05))
        base = np.array(
            [-0.58 + jitter(0.03), -0.55 + jitter(0.03), 0.0]
        )
        up_curls = (
            max(0.01 + jitter(0.03), 0.0),
            max(0.01 + jitter(0.03), 0.0),
            max(0.005 + jitter(0.02), 0.0),
        )
        th = _chain(base, np.deg2rad(-92.0), FINGER_LEN["thumb"], up_curls, THUMB_MAX)
        skel[2], skel[3], skel[4] = th[1], th[2], th[3]
    elif gesture == Gesture.THUMB_DOWN:
        finger("index", 5, (0.94, 0.97, 0.92), jitter(0.05))
        finger("middle", 9, (0.94, 0.97, 0.92), jitter(0.05))
        finger("ring", 13, (0.94, 0.96, 0.9), jitter(0.05))
        finger("pinky", 17, (0.95, 0.97, 0.9), jitter(0.05))
        base = np.array(
            [-0.32 + jitter(0.03), -0.26 + jitter(0.03), 0.0]
        )
        down_curls = (
            max(0.01 + jitter(0.03), 0.0),
            max(0.01 + jitter(0.03), 0.0),
            max(0.005 + jitter(0.02), 0.0),
        )
        th = _chain(base, np.deg2rad(92.0), FINGER_LEN["thumb"], down_curls, THUMB_MAX)
        skel[2], skel[3], skel[4] = th[1], th[2], th[3]
    else:
        raise ValueError(gesture)
    # Caminho único de ruído: deixar o augment() tratar o jitter isotrópico 3D.
    out = np.stack([np.asarray(p, dtype=np.float64) for p in skel])
    if out.shape != (21, 3):
        raise AssertionError(f"sintese {gesture} -> {out.shape}, esperado (21,3)")
    return out


def augment(raw, rng):
    pts = raw.copy()
    n = len(pts)
    theta = rng.uniform(-np.pi, np.pi)
    cos, sin = np.cos(theta), np.sin(theta)
    R2 = np.array([[cos, -sin], [sin, cos]])
    pts[:, :2] = pts[:, :2] @ R2.T
    scale_px = max(rng.normal(150.0, 45.0), 20.0)
    origin = rng.uniform(-300, 300, 2)
    pts[:, :2] = pts[:, :2] * scale_px + origin

    sigma = rng.choice([0.004, 0.012, 0.026, 0.05], p=[0.3, 0.35, 0.25, 0.1])
    pts[:, :2] += rng.normal(0.0, sigma * scale_px, (n, 2))
    pts[:, 2] += rng.normal(0.0, sigma * scale_px * 0.3, n)

    if rng.random() < 0.15:
        k = int(rng.integers(1, 4))
        idx = rng.choice(n, size=k, replace=False)
        pts[idx, :2] += rng.normal(0.0, 0.09 * scale_px, (k, 2))

    feat = _normalize(pts)
    if feat is None or not np.all(np.isfinite(feat)):
        return None
    return feat.astype(np.float32)


CLASS_IDS = {g: i for i, g in enumerate(CLASSES)}
LABEL_NAMES = [g.name for g in CLASSES]


def _to_feature(pts):
    feat = _normalize(pts)
    if feat is None or not np.all(np.isfinite(feat)):
        return None
    return feat.astype(np.float32)


WINDOW = 5


def _window_from_features(feats):
    feats = np.stack([np.asarray(f, dtype=np.float64) for f in feats])
    cur = feats[-1]
    mean = feats.mean(axis=0)
    return np.concatenate([cur, mean]).astype(np.float32)


def jitter_real(pts, rng):
    scale = float(np.hypot(pts[9, 0] - pts[0, 0], pts[9, 1] - pts[0, 1]))
    if scale < 1e-6:
        return None
    sigma = rng.choice([0.004, 0.010, 0.020], p=[0.4, 0.4, 0.2]) * scale
    out = pts.copy()
    out[:, :2] += rng.normal(0.0, sigma, (len(pts), 2))
    out[:, 2] += rng.normal(0.0, sigma * 0.3, len(pts))
    if rng.random() < 0.10:
        k = int(rng.integers(1, 3))
        idx = rng.choice(len(pts), size=k, replace=False)
        out[idx, :2] += rng.normal(0.0, 0.07 * scale, (k, 2))
    return out


def split_real(y, rng, val_frac=0.15):
    tr, va = [], []
    for c in np.unique(y):
        idx = np.where(y == c)[0]
        idx = idx[rng.permutation(len(idx))]
        n_va = max(1, int(round(len(idx) * val_frac))) if len(idx) >= 4 else 0
        va.extend(idx[:n_va].tolist())
        tr.extend(idx[n_va:].tolist())
    return np.array(tr, dtype=np.int64), np.array(va, dtype=np.int64)


def load_real(path, min_per_class=30):
    data = np.load(path)
    X, y = data["X"].astype(np.float64), data["y"].astype(np.int64)
    if X.ndim != 3 or X.shape[1:] not in ((21, 2), (21, 3)):
        raise ValueError(
            f"formato inesperado em {path}: X{X.shape} (esperado N x 21 x 2|3)"
        )
    if X.shape[2] == 2:
        X = np.concatenate([X, np.zeros((*X.shape[:2], 1), dtype=np.float64)], axis=2)
    counts = np.bincount(y, minlength=N_CLASSES)
    if (counts < min_per_class).any():
        raise ValueError(
            "dados reais insuficientes por classe "
            f"{dict(zip(LABEL_NAMES, counts.tolist(), strict=True))}; "
            f"minimo {min_per_class} por classe. Usa tools/collect_gestures.py"
        )
    return X, y


def make_dataset(per_class, rng):
    xs, ys = [], []
    for g in CLASSES:
        made = 0
        while made < per_class:
            feats = []
            for _ in range(WINDOW):
                raw = synthesize(g, rng)
                f = augment(raw, rng)
                if f is None:
                    break
                feats.append(f)
            if len(feats) < WINDOW:
                continue
            xs.append(_window_from_features(feats))
            ys.append(CLASS_IDS[g])
            made += 1
    X = np.stack(xs)
    Y = np.array(ys, dtype=np.int64)
    perm = rng.permutation(len(X))
    return X[perm], Y[perm]


def ce_loss(P, Y):
    return -np.log(P[np.arange(len(Y)), Y] + 1e-9).mean()


class MLP:
    def __init__(self, seed=3):
        r = np.random.default_rng(seed)
        self.w1 = r.normal(0, 0.12, (FEATURES, 96)).astype(np.float64)
        self.b1 = np.zeros(96)
        self.w2 = r.normal(0, 0.12, (96, 48)).astype(np.float64)
        self.b2 = np.zeros(48)
        self.w3 = r.normal(0, 0.12, (48, N_CLASSES)).astype(np.float64)
        self.b3 = np.zeros(N_CLASSES)

    def forward(self, X):
        h1 = np.tanh(X @ self.w1 + self.b1)
        h2 = np.tanh(h1 @ self.w2 + self.b2)
        logits = h2 @ self.w3 + self.b3
        e = np.exp(logits - logits.max(axis=1, keepdims=True))
        return h1, h2, e / e.sum(axis=1, keepdims=True)


def evaluate_runtime(net_params, trials=4000, seed=4242):
    ai = GestureAI.__new__(GestureAI)
    ai.w1, ai.b1 = net_params[0], net_params[1]
    ai.w2, ai.b2 = net_params[2], net_params[3]
    ai.w3, ai.b3 = net_params[4], net_params[5]
    vrng = np.random.default_rng(seed)
    correct = 0
    tested = 0
    low_conf_wrong = 0
    for _ in range(trials):
        g = CLASSES[int(vrng.integers(0, N_CLASSES))]
        frames = []
        for _ in range(WINDOW):
            raw = synthesize(g, vrng)
            px = np.empty_like(raw)
            px[:, :2] = raw[:, :2] * 150 + 320.0
            px[:, 2] = raw[:, 2]
            frames.append(px)
        pg, pc = ai.classify(frames)
        tested += 1
        if pg == g:
            correct += 1
        elif pc < 0.72:
            low_conf_wrong += 1
    return correct, tested, low_conf_wrong


def train(per_class=6000, epochs=24, real_path=None, out_dir=None, real_copies=4):
    Xr = Yr = None
    if real_path:
        print(f"A carregar dados reais: {real_path}")
        Xr, Yr = load_real(real_path)
        per_class = min(per_class, 3000)
        print(
            "dados reais: "
            f"{dict(zip(LABEL_NAMES, np.bincount(Yr, minlength=N_CLASSES).tolist(), strict=True))}"
        )

    print("A gerar dados sinteticos ...")
    Xtr, Ytr = make_dataset(per_class, RNG)
    Xva, Yva = make_dataset(800, np.random.default_rng(999))
    print(f"treino {Xtr.shape} | validacao {Xva.shape}")

    real_va_X = real_va_y = None
    if real_path:
        rng_real = np.random.default_rng(1234)
        idx_tr, idx_va = split_real(Yr, rng_real)
        feats, labels = [], []
        pts_tr = Xr[idx_tr]
        for i in range(len(pts_tr)):
            f = _to_feature(pts_tr[i])
            if f is not None:
                feats.append(_window_from_features([f]))
                labels.append(int(Yr[idx_tr[i]]))
            for _ in range(real_copies):
                j = jitter_real(pts_tr[i], rng_real)
                fj = _to_feature(j) if j is not None else None
                if fj is not None:
                    feats.append(_window_from_features([fj]))
                    labels.append(int(Yr[idx_tr[i]]))
        Xtr = np.vstack([Xtr, np.stack(feats)])
        Ytr = np.concatenate([Ytr, np.array(labels, dtype=np.int64)])
        perm = rng_real.permutation(len(Xtr))
        Xtr, Ytr = Xtr[perm], Ytr[perm]
        clean = []
        for p in Xr[idx_va]:
            f = _to_feature(p)
            if f is not None:
                clean.append(_window_from_features([f]))
        real_va_X = np.stack(clean) if clean else np.zeros((0, FEATURES))
        real_va_y = Yr[idx_va][: len(clean)]
        order = rng_real.permutation(len(real_va_X))
        real_va_X, real_va_y = real_va_X[order], real_va_y[order]
        print(f"mistura: +{len(feats)} amostras reais (com {real_copies} variantes)")

    net = MLP()
    params = [net.w1, net.b1, net.w2, net.b2, net.w3, net.b3]
    m = [np.zeros_like(p) for p in params]
    v = [np.zeros_like(p) for p in params]
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    step = 0
    batch = 256

    for epoch in range(epochs):
        order = np.random.default_rng(epoch).permutation(len(Xtr))
        lr = 2.5e-3 * (0.5 ** (epoch // 8))
        tot = 0.0
        for s in range(0, len(order), batch):
            idx = order[s : s + batch]
            Xb, Yb = Xtr[idx], Ytr[idx]
            h1, h2, P = net.forward(Xb)
            step += 1
            dlogits = P.copy()
            dlogits[np.arange(len(Yb)), Yb] -= 1.0
            dlogits /= len(Yb)
            dh2 = (dlogits @ net.w3.T) * (1 - h2**2)
            dh1 = (dh2 @ net.w2.T) * (1 - h1**2)
            grads = [None] * 6
            grads[0] = Xb.T @ dh1
            grads[1] = dh1.sum(0)
            grads[2] = h1.T @ dh2
            grads[3] = dh2.sum(0)
            grads[4] = h2.T @ dlogits
            grads[5] = dlogits.sum(0)
            for pi, (p, g) in enumerate(zip(params, grads, strict=True)):
                m[pi] = beta1 * m[pi] + (1 - beta1) * g
                v[pi] = beta2 * v[pi] + (1 - beta2) * g * g
                mh = m[pi] / (1 - beta1**step)
                vh = v[pi] / (1 - beta2**step)
                p -= lr * mh / (np.sqrt(vh) + eps)
            tot += ce_loss(P, Yb) * len(Yb)

        _, _, Pv = net.forward(Xva)
        va_acc = (Pv.argmax(1) == Yva).mean()
        line = f"epoca {epoch+1:2d} | loss {(tot/len(Xtr)):.4f} | val sint {va_acc*100:.2f}%"
        if real_va_X is not None:
            _, _, Pr = net.forward(real_va_X)
            ra = (Pr.argmax(1) == real_va_y).mean()
            line += f" | val REAL {ra*100:.2f}%"
        print(line)

    _, _, Pv = net.forward(Xva)
    pred_v = Pv.argmax(1)
    acc = (pred_v == Yva).mean()
    n = N_CLASSES
    conf = np.zeros((n, n), dtype=int)
    for y, p in zip(Yva, pred_v, strict=True):
        conf[y, p] += 1
    print("\nMatriz de confusao SINTETICA (linhas=real, colunas=pred):")
    print("      " + " ".join(f"{nm:>9}" for nm in LABEL_NAMES))
    for i, nm in enumerate(LABEL_NAMES):
        print(f"{nm:>9} " + " ".join(f"{conf[i,j]:9d}" for j in range(n)))
    print(f"\nValidacao sintetica: acc={acc*100:.2f}%")
    if acc < 0.97:
        print("AVISO: accuracy abaixo de 97%")

    real_acc = None
    if real_va_X is not None:
        _, _, Pr = net.forward(real_va_X)
        pred_r = Pr.argmax(1)
        real_acc = (pred_r == real_va_y).mean()
        conf_r = np.zeros((n, n), dtype=int)
        for y, p in zip(real_va_y, pred_r, strict=True):
            conf_r[y, p] += 1
        print("\nMatriz de confusao REAL (linhas=real, colunas=pred):")
        print("      " + " ".join(f"{nm:>9}" for nm in LABEL_NAMES))
        for i, nm in enumerate(LABEL_NAMES):
            print(f"{nm:>9} " + " ".join(f"{conf_r[i,j]:9d}" for j in range(n)))
        print(f"\nValidacao REAL: acc={real_acc*100:.2f}%")

    out_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = out_dir or os.path.join(out_root, "models")
    os.makedirs(models_dir, exist_ok=True)
    dest = os.path.join(models_dir, "gesture_mlp.npz")
    prev = os.path.join(models_dir, "gesture_mlp_prev.npz")
    if os.path.isfile(dest):
        shutil.copyfile(dest, prev)
        print(f"Modelo anterior guardado como {prev}")
    np.savez_compressed(
        dest,
        w1=params[0],
        b1=params[1],
        w2=params[2],
        b2=params[3],
        w3=params[4],
        b3=params[5],
    )
    if out_dir is None:
        shutil.copyfile(dest, os.path.join(out_root, "core", "gesture_mlp.npz"))
        print(f"Modelo gravado em {dest} (+ copia em core/)")
    else:
        print(f"Modelo gravado em {dest}")
    if real_acc is not None and real_acc < 0.90:
        print(
            "AVISO: accuracy REAL abaixo de 90%. Para reverter: copia "
            f"{prev} de volta para {dest}"
        )

    okc, tot, lowc = evaluate_runtime([p.copy() for p in params])
    print(
        f"Ciclo completo inferencia: {okc}/{tot} = {100.0*okc/tot:.2f}%"
        f" (erros com confianca baixa: {lowc})"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Treina a IA de gestos (sintetico + opcionais dados reais)"
    )
    p.add_argument("--real", default=None, help="npz do collect_gestures.py")
    p.add_argument("--per-class", type=int, default=6000, help="amostras sinteticas/classe")
    p.add_argument("--epochs", type=int, default=24)
    p.add_argument(
        "--real-copies", type=int, default=4,
        help="variantes com ruido por amostra real",
    )
    p.add_argument("--out", default=None, help="pasta destino do modelo (default models/)")
    a = p.parse_args()
    train(
        per_class=a.per_class,
        epochs=a.epochs,
        real_path=a.real,
        out_dir=a.out,
        real_copies=a.real_copies,
    )
