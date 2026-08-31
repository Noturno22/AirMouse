"""Headless render test:
Forca o paintEvent da CameraView a desenhar o esqueleto + crosshair com uma
mao simulada, para apanhar bugs de desempacotamento (ex.: QPoint nao iteravel).
Antes este teste nao existia -> o bug so rebentava com camera real.
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication

from core.gestures import Gesture, HandFrame
from ui.camera_view import CameraView

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(("PASS  " if ok else "FAIL  ") + name + (("  -> " + detail) if detail else ""))


def make_hand_frame():
    pts = [(120 + i * 8, 160) for i in range(21)]
    return HandFrame(
        points_px=pts,
        hand_scale_px=120.0,
        pinch_ratio=0.4,
        pinch_mid_ratio=0.6,
        raw_gesture=Gesture.PINCH,
        gesture=Gesture.PINCH,
        index_tip=(200, 200),
        palm_center=(150.0, 150.0),
        ai_conf=0.9,
    )


def make_frame_bgr(w=640, h=480):
    import numpy as np
    return np.zeros((h, w, 3), dtype=np.uint8)


def main():
    app = QApplication(sys.argv)
    view = CameraView()
    view.resize(640, 480)
    view.show()

    try:
        view.update_frame(
            make_frame_bgr(),
            {"left": make_hand_frame()},
            "left",
            flash=0,
        )
    except Exception as exc:  # noqa: BLE001
        check("update_frame com mao", False, repr(exc))
    else:
        check("update_frame com mao", True)

    # Forca o paintEvent (desenha esqueleto + crosshair + barra) e apanha erros.
    try:
        _pix = view.grab()
        check("paintEvent crosshair+esqueleto", True, f"pixmap {_pix.width()}x{_pix.height()}")
    except Exception as exc:  # noqa: BLE001
        check("paintEvent crosshair+esqueleto", False, repr(exc))

    # Tambem testa um gesto PEACE e a mao NAO ativa, para cobrir esqueleto inativo.
    hf2 = make_hand_frame()
    hf2 = HandFrame(**{**hf2.__dict__, "gesture": Gesture.PEACE})
    try:
        view.update_frame(
            make_frame_bgr(),
            {"left": hf2, "right": make_hand_frame()},
            "right",
            flash=1,
        )
        view.grab()
        check("paintEvent peace + flash + mao inativa", True)
    except Exception as exc:  # noqa: BLE001
        check("paintEvent peace + flash + mao inativa", False, repr(exc))

    # Caso palm_center apos EMA suavizado (tupla float).
    try:
        view.update_frame(
            make_frame_bgr(),
            {"left": make_hand_frame()},
            "left",
            flash=0,
        )
        view.grab()
        check("paintEvent segundo frame (EMA smooth)", True)
    except Exception as exc:  # noqa: BLE001
        check("paintEvent segundo frame (EMA smooth)", False, repr(exc))

    app.quit()

    fails = [r for r in RESULTS if not r[1]]
    print()
    print(f"{len(RESULTS) - len(fails)}/{len(RESULTS)} PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
