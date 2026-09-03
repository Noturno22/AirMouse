"""Diagnóstico: imprime por frame o label ("Left"/"Right") que o MediaPipe dá
a CADA mão, para perceber porque a mão esquerda não dispara comandos."""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config  # noqa: E402
from core.tracker import HandTracker, ensure_model  # noqa: E402
from main import open_camera  # noqa: E402

cfg = Config()
print("=== DIAGNÓSTICO HANDEDNESS ===")
print(f"cfg.mirror       = {cfg.mirror}")
print(f"cfg.num_hands    = {cfg.num_hands}")
print("command_side     = 'Right' se mirror, 'Left' se not")
print("(a mão que executa comandos deve bater com o label que o MediaPipe dá)")
print("-" * 60)

cam = open_camera(cfg)
if cam is None:
    print("ERRO: nenhuma câmara.")
    sys.exit(1)
print("câmara aberta.")

model_path = ensure_model(cfg.model_path, cfg.model_url)
tracker = HandTracker(model_path, num_hands=cfg.num_hands,
                      use_gpu=False, num_threads=cfg.tracker_threads)

t0 = time.time()
last_print = 0.0
frame_i = 0
last_seq = -1
outpath = os.path.join(ROOT, "tools", "sides_debug.txt")
with open(outpath, "w", encoding="utf-8") as fh:
    side = "Right" if cfg.mirror else "Left"
    fh.write(f"cfg.mirror={cfg.mirror} command_side='{side}'\n")
    try:
        while time.time() - t0 < 30:
            frame, seq = cam.read()
            if frame is None:
                time.sleep(0.002)
                continue
            if seq == last_seq:
                time.sleep(0.002)
                continue
            last_seq = seq
            frame_i += 1
            rgb = frame[:, :, ::-1]  # BGR->RGB
            hands, sides = tracker.process(rgb, time.monotonic_ns() // 1_000_000)
            now = time.time()
            if now - last_print >= 0.5 and sides:
                last_print = now
                line = f"[{frame_i}] mãos: {sides}"
                print(line)
                fh.write(line + "\n")
                fh.flush()
    finally:
        cam.release()

print("-" * 60)
print("done.")
