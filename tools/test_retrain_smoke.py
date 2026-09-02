import os
import shutil
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.gesture_ai import CLASSES, N_CLASSES, GestureAI
from tools.train_gesture_ai import (
    _to_feature,
    load_real,
    split_real,
    synthesize,
    train,
)

passed, failed = 0, 0


def check(name, cond):
    global passed, failed
    print(("PASS " if cond else "FAIL ") + name)
    passed, failed = passed + int(cond), failed + int(not cond)


tmp = tempfile.mkdtemp(prefix="airmouse_retrain_")
try:
    rng = np.random.default_rng(42)

    # --- dados "reais" falsos: esqueletos sinteticos em pixels (3D) ---
    xs, ys = [], []
    for cid, g in enumerate(CLASSES):
        for i in range(60):
            skel = synthesize(g, rng)
            origin = rng.uniform(200, 400, 2)
            pts = np.empty_like(skel)
            pts[:, :2] = skel[:, :2] * rng.uniform(120, 180) + origin
            pts[:, 2] = skel[:, 2]
            pts[:, :2] = pts[:, :2] + rng.normal(0, 2.0, (21, 2))
            xs.append(pts)
            ys.append(cid)
    fake = os.path.join(tmp, "real.npz")
    np.savez_compressed(fake, X=np.stack(xs).astype(np.float32),
                        y=np.array(ys, dtype=np.int64))

    # --- load_real valida formato e minimos ---
    Xr, Yr = load_real(fake, min_per_class=30)
    check(
        "load_real carrega",
        Xr.shape == (60 * N_CLASSES, 21, 3) and len(np.unique(Yr)) == N_CLASSES,
    )

    # load_real aceita um dataset 2D legado (converte para 3D com z=0)
    fake2 = os.path.join(tmp, "real2d.npz")
    rows2 = np.asarray(xs)[:, :, :2]
    np.savez_compressed(fake2, X=rows2,
                        y=np.array(ys, dtype=np.int64))
    Xr2, _ = load_real(fake2, min_per_class=30)
    check("load_real aceita 2D legado -> 3D", Xr2.shape[2] == 3)
    try:
        load_real(fake, min_per_class=1000)
        check("load_real rejeita minimos", False)
    except ValueError:
        check("load_real rejeita minimos", True)

    # --- split estratificado ---
    itr, iva = split_real(Yr, np.random.default_rng(1))
    va_counts = np.bincount(Yr[iva], minlength=N_CLASSES)
    check("split estratificado", len(set(va_counts.tolist())) == 1 and len(itr) > len(iva))

    # --- treino completo com dados reais ---
    out_dir = os.path.join(tmp, "models")
    os.makedirs(out_dir, exist_ok=True)
    dummy = os.path.join(out_dir, "gesture_mlp.npz")
    np.savez_compressed(dummy, w1=np.zeros((120, 96)), b1=np.zeros(96),
                        w2=np.zeros((96, 48)), b2=np.zeros(48),
                        w3=np.zeros((48, N_CLASSES)), b3=np.zeros(N_CLASSES))
    train(per_class=300, epochs=2, real_path=fake, out_dir=out_dir, real_copies=2)

    check("backup do modelo anterior criado",
          os.path.isfile(os.path.join(out_dir, "gesture_mlp_prev.npz")))

    ai = GestureAI(os.path.join(out_dir, "gesture_mlp.npz"))
    ok = 0
    vrng = np.random.default_rng(77)
    for g in CLASSES:
        skel = synthesize(g, vrng)
        px = np.empty_like(skel)
        px[:, :2] = skel[:, :2] * 150 + np.array([320.0, 240.0])
        px[:, 2] = skel[:, 2]
        pred, conf = ai.classify(px)
        ok += int(pred == g and conf > 0.5)
    check(f"modelo retreinado classifica (ok={ok}/{N_CLASSES})", ok >= N_CLASSES - 1)

    check("_to_feature dimensao", _to_feature(xs[0]).shape == (60,))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{passed} PASS / {failed} FAIL")
sys.exit(1 if failed else 0)
