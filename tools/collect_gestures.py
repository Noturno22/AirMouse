import argparse
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from core.camera import CameraStream
from core.filters import FilterPair2D  # noqa: F401  (mantem paridade com main)
from core.tracker import HAND_CONNECTIONS, HandTracker, ensure_model

CLASS_KEYS = {
    ord("1"): ("OPEN", 0),
    ord("2"): ("PINCH", 1),
    ord("3"): ("PINCH_MID", 2),
    ord("4"): ("FIST", 3),
    ord("5"): ("PEACE", 4),
    ord("6"): ("THREE", 5),
    ord("7"): ("THUMB_UP", 6),
    ord("8"): ("ROCK", 7),
    ord("9"): ("SHAKA", 8),
}
CLASS_NAMES = (
    "OPEN", "PINCH", "PINCH_MID", "FIST", "PEACE",
    "THREE", "THUMB_UP", "ROCK", "SHAKA",
)
MAX_PER_CLASS = 5000
COLOR_DARK = (22, 22, 22)
COLOR_GREEN = (90, 220, 90)
COLOR_RED = (60, 60, 235)
COLOR_WHITE = (245, 245, 245)
COLOR_GRAY = (160, 160, 160)


def open_camera(cfg):
    candidates = [cfg.camera_index] if cfg.camera_index is not None else [0, 1, 2]
    for index in candidates:
        cam = CameraStream(index)
        if cam.open(cfg.frame_width, cfg.frame_height, 30):
            return cam
        cam.release()
    return None


class Collector:
    def __init__(self):
        self.samples = {i: [] for i in range(len(CLASS_NAMES))}
        self.active: int | None = None

    def counts(self):
        return [len(self.samples[i]) for i in range(len(CLASS_NAMES))]

    def total(self):
        return sum(self.counts())

    def add(self, cls_id, pts):
        if len(self.samples[cls_id]) >= MAX_PER_CLASS:
            return False
        self.samples[cls_id].append(pts)
        return True

    def undo(self):
        if self.active is not None and self.samples[self.active]:
            self.samples[self.active].pop()
            return True
        return False

    def clear_active(self):
        if self.active is not None:
            self.samples[self.active].clear()
            return True
        return False


def save(out_path, collector):
    xs, ys = [], []
    for cls_id, arr in collector.samples.items():
        for pts in arr:
            xs.append(np.asarray(pts, dtype=np.float32))
            ys.append(cls_id)
    if not xs:
        print("Nada para gravar.")
        return False
    parent = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(parent, exist_ok=True)
    np.savez_compressed(
        out_path,
        X=np.stack(xs),
        y=np.array(ys, dtype=np.int64),
        classes=np.array(CLASS_NAMES),
    )
    print(f"Gravado: {out_path} | total {len(xs)} amostras | por classe "
          f"{dict(zip(CLASS_NAMES, collector.counts(), strict=False))}")
    return True


def draw(frame, points, collector, fps, quality_ok, auto_label):
    h, w = frame.shape[:2]
    if points is not None:
        for a, b in HAND_CONNECTIONS:
            pa = tuple(int(v) for v in points[a])
            pb = tuple(int(v) for v in points[b])
            cv2.line(frame, pa, pb, (200, 200, 200), 1)
    rec_on = collector.active is not None
    label = (
        f"A GRAVAR: {CLASS_NAMES[collector.active]}"
        if rec_on else "PRIME 1-5 PARA ESCOLHER GESTO"
    )
    color = COLOR_RED if rec_on else COLOR_WHITE
    cv2.rectangle(frame, (12, 10), (420, 40), COLOR_DARK, -1)
    cv2.putText(frame, label, (24, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

    for i, name in enumerate(CLASS_NAMES):
        y = 64 + 22 * i
        mark = ">" if collector.active == i else " "
        col = COLOR_GREEN if collector.counts()[i] > 0 else COLOR_GRAY
        txt = f"{mark}[{i+1}] {name:<9} {collector.counts()[i]:4d}"
        cv2.putText(frame, txt, (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 1, cv2.LINE_AA)

    q_txt = "OK" if quality_ok else "MAO PERTO/QUALIDADE"
    q_col = COLOR_GREEN if quality_ok else COLOR_RED
    cv2.putText(frame, q_txt, (w - 240, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, q_col, 1, cv2.LINE_AA)
    cv2.putText(
        frame, f"{fps:4.0f} fps | z apaga ultima | c limpa gesto | s grava | Q sai",
        (16, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.48, COLOR_GRAY, 1, cv2.LINE_AA,
    )
    if auto_label:
        cv2.putText(frame, f"MODO AUTO: {auto_label}", (w - 260, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_GREEN, 1, cv2.LINE_AA)


def run(args):
    cfg = Config()
    if args.camera is not None:
        cfg.camera_index = args.camera
    model_path = ensure_model(cfg.model_path, cfg.model_url)
    cam = open_camera(cfg)
    if cam is None:
        print("ERRO: nenhuma camera encontrada.")
        return 1
    tracker = HandTracker(model_path, num_hands=1)
    collector = Collector()
    auto_label = None
    auto_left = 0

    if args.frames > 0:
        if not args.cls:
            print("ERRO: --frames exige --class.")
            cam.release()
            tracker.close()
            return 1
        key = next((k for k, (n, _) in CLASS_KEYS.items() if n == args.cls.upper()), None)
        if key is None:
            print(f"ERRO: gesto desconhecido {args.cls!r}. Usa: {', '.join(CLASS_NAMES)}")
            cam.release()
            tracker.close()
            return 1
        auto_label, auto_left = args.cls.upper(), args.frames
        collector.active = CLASS_KEYS[key][1]

    fps = 0.0
    last_seq = -1
    warmup = max(cfg.warmup_frames, 0)
    window = "AirMouse-Coleta"

    try:
        if not args.no_preview:
            cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        while True:
            t0 = time.perf_counter()
            frame, seq = cam.read()
            if frame is None:
                time.sleep(0.002)
                continue
            if seq == last_seq:
                time.sleep(0.002)
                continue
            last_seq = seq
            if warmup > 0:
                warmup -= 1
                continue
            frame = cv2.flip(frame, 1) if cfg.mirror else frame
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hands = tracker.process(rgb, time.monotonic_ns() // 1_000_000)

            points = None
            quality_ok = False
            if hands:
                lm = hands[0]
                pts = np.array(
                    [(p[0] * w, p[1] * h, p[2] if len(p) > 2 else 0.0) for p in lm],
                    dtype=np.float32,
                )
                scale = float(np.hypot(*(pts[9] - pts[0])))
                quality_ok = scale >= cfg.min_hand_scale_px * 1.15 and bool(
                    np.all(np.isfinite(pts))
                )
                points = pts
                if (
                    quality_ok
                    and collector.active is not None
                    and collector.add(collector.active, pts.copy())
                ):
                    if auto_label:
                        auto_left -= 1
                        if auto_left <= 0:
                            break

            dt = time.perf_counter() - t0
            inst = 1.0 / dt if dt > 0 else 0.0
            fps = inst if fps == 0.0 else fps * 0.9 + inst * 0.1

            if not args.no_preview:
                draw(frame, points, collector, fps, quality_ok, auto_label)
                cv2.imshow(window, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key in CLASS_KEYS:
                    name, cid = CLASS_KEYS[key]
                    collector.active = None if collector.active == cid else cid
                    if auto_label is None:
                        print(f"Gesto ativo: {name if collector.active is not None else '-'}")
                elif key == ord("z"):
                    collector.undo()
                elif key == ord("c"):
                    collector.clear_active()
                elif key == ord("s"):
                    save(args.out, collector)
            elif auto_label and auto_left <= 0:
                break
    finally:
        ok = False
        if not args.no_save:
            ok = save(args.out, collector)
        tracker.close()
        cam.release()
        cv2.destroyAllWindows()

    if args.frames > 0 and not args.no_save:
        got = collector.counts()[CLASS_NAMES.index(auto_label)] if auto_label else 0
        print(f"[coleta-selftest] pedido {args.frames} | gravado {got}")
        return 0 if got == args.frames else 1
    return 0 if (args.no_save or ok or collector.total() == 0) else 0


def parse_args():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = argparse.ArgumentParser(description="Coleta landmarks reais para treinar a IA de gestos")
    p.add_argument("--out", default=os.path.join(root, "data", "real_landmarks.npz"))
    p.add_argument("--camera", type=int, default=None)
    p.add_argument("--no-preview", action="store_true")
    p.add_argument("--no-save", action="store_true", help="nao grava ficheiro (teste)")
    p.add_argument(
        "--frames", type=int, default=0,
        help="modo automatico: captura N amostras do gesto --class e sai",
    )
    p.add_argument(
        "--class", dest="cls", default=None,
        help="OPEN|PINCH|PINCH_MID|FIST|PEACE|THREE|THUMB_UP|ROCK|SHAKA",
    )
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(run(parse_args()))
