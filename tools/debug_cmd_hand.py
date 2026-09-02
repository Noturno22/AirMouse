"""Diagnóstico AO VIVO do pipeline da mão de comandos.

Replica exatamente o que o engine faz (incluindo o flip do espelho ANTES do
tracking) e imprime, por frame com mãos detetadas:
  - o label que o MediaPipe dá a cada mão
  - a posição X (px) da palma de cada mão no frame ESPELHADO
  - quais mãos o HandPool produz (após o fix de dedup por-X)
  - o que _command_hand_frame escolhe como mão de comandos

O objetivo é perceber porque a mão esquerda não dispara comandos em tempo real.
Correr com as DUAS mãos à frente: a ESQUERDA física a fazer gestos de comando
e a DIREITA parada (cursor).
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import cv2

from config import Config
from core.engine import _command_hand_frame
from core.tracker import HandTracker, ensure_model
from core.twohand import HandPool
from main import open_camera

cfg = Config()
cfg.num_hands = 2
print("=== DIAGNÓSTICO MÃO DE COMANDOS (com espelho) ===")
print(f"cfg.mirror     = {cfg.mirror}")
print(f"frame espelhado ANTES do tracking? SIM (igual ao engine)")
print("Levanta as DUAS mãos e faz gestos na esquerda. Ctrl+C para sair.")
print("-" * 64)

cam = open_camera(cfg)
if cam is None:
    print("ERRO: nenhuma câmara.")
    sys.exit(1)

model_path = ensure_model(cfg.model_path, cfg.model_url)
tracker = HandTracker(model_path, num_hands=2,
                      use_gpu=False, num_threads=cfg.tracker_threads)
pool = HandPool(cfg, None)

outpath = os.path.join(ROOT, "tools", "cmd_hand_debug.txt")
last_print = 0.0
frame_i = 0
last_seq = -1
with open(outpath, "w", encoding="utf-8") as fh:
    try:
        while True:
            frame, seq = cam.read()
            if frame is None:
                time.sleep(0.002)
                continue
            if seq == last_seq:
                time.sleep(0.002)
                continue
            last_seq = seq
            frame_i += 1

            if cfg.mirror:
                frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = frame[:, :, ::-1]  # BGR->RGB
            hands, sides = tracker.process(rgb, time.monotonic_ns() // 1_000_000)
            results = pool.update(hands, sides, w, h)
            now = time.time()
            if now - last_print >= 0.4 and results:
                last_print = now
                line_parts = [f"[fr{frame_i}]"]
                # labels + X de cada mão no frame espelhado
                for side_label, (hf, _ev, _val) in results.items():
                    p = hf.palm_center
                    line_parts.append(f"{side_label}@x={int(p[0]) if p else '?'}")
                cmd = _command_hand_frame(results, cfg.mirror, w)
                cmd_txt = f"{cmd[0].gesture.name}@x={int(cmd[0].palm_center[0])}" if cmd else "NENHUMA"
                line_parts.append(f"  COMANDOS-> {cmd_txt}")
                line = " ".join(line_parts)
                print(line)
                fh.write(line + "\n")
                fh.flush()
    except KeyboardInterrupt:
        pass
    finally:
        cam.release()

print("-" * 64)
print("done. log em", outpath)