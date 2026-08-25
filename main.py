import argparse
import ctypes
import json
import math
import os
import sys
import time

import cv2
import numpy as np

from typing import Any

from config import Config
from core.assistant import Assistant3D
from core.autotune import AutoTuner
from core.camera import CameraStream
from core.filters import AccelCurve, FilterPair2D
from core.gesture_ai import GestureAI, ensure_ai_model
from core.gestures import Gesture
from core.light import LightBoost
from core.motion import SmoothEmitter, lead_offset
from core.mouse_ctl import MouseCtl
from core.nlu import ACTION_LABELS
from core.snap import SnapEngine
from core.tracker import HAND_CONNECTIONS, HandTracker, ensure_model
from core.tray import TrayAppAdapter, TrayIcon
from core.twohand import ClapDetector, HandPool, MagnifierCtl
from core.tts import Speaker
from core.voice import VoiceEngine

SMOOTH_PRESETS = (
    ("SUAVE", 0.9, 0.02),
    ("NORMAL", 1.4, 0.028),
    ("REACTIVO", 2.2, 0.05),
)
SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "settings.json"
)

BADGES = {
    Gesture.NONE: ("SEM MAO", (150, 150, 150)),
    Gesture.OPEN: ("MOVER", (80, 200, 255)),
    Gesture.PINCH: ("CLIQUE ESQ", (90, 220, 90)),
    Gesture.PINCH_MID: ("CLIQUE DIR", (60, 60, 235)),
    Gesture.FIST: ("ARRASTAR", (70, 130, 255)),
    Gesture.PEACE: ("SCROLL", (255, 80, 200)),
    Gesture.THREE: ("VOLUME", (255, 170, 60)),
    Gesture.THUMB_UP: ("PLAY/PAUSA", (140, 225, 225)),
}
MOVE_GESTURES = frozenset({Gesture.OPEN, Gesture.PINCH, Gesture.FIST})
COLOR_GRAY = (160, 160, 160)
COLOR_WHITE = (245, 245, 245)
COLOR_GREEN = (90, 220, 90)
COLOR_PINK = (255, 80, 200)
COLOR_DARK = (22, 22, 22)


def parse_args():
    parser = argparse.ArgumentParser(description="AirMouse - controla o rato com a mao")
    parser.add_argument("--camera", type=int, default=None)
    parser.add_argument("--gain", type=float, default=None)
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("--preview", action="store_true", help="forca janela mesmo em modo bandeja")
    parser.add_argument("--gpu", action="store_true", help="tenta usar delegado GPU no tracker")
    parser.add_argument("--tray", action="store_true", help="modo bandeja: invisivel com icone na bandeja")
    parser.add_argument("--reset-config", action="store_true", help="apaga settings.json")
    parser.add_argument("--no-voice", action="store_true", help="desativa comandos de voz")
    parser.add_argument("--no-ai", action="store_true", help="desativa classificador IA de gestos")
    parser.add_argument("--no-autotune", action="store_true", help="desativa auto-afinacao")
    parser.add_argument("--pinch-debug", action="store_true", help="imprime racios de pinca no console")
    parser.add_argument("--voice-always", action="store_true", help="voz sempre ativa (sem wake word)")
    parser.add_argument("--no-tts", action="store_true", help="sem voz falada do Jarvis")
    parser.add_argument("--whisper-model", type=str, default=None,
                        help="modelo Whisper (tiny/base/small; default small)")
    parser.add_argument(
        "--frames",
        type=int,
        default=0,
        help="processa apenas N frames e sai (modo de teste)",
    )
    return parser.parse_args()


def acquire_single_instance():
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.CreateMutexW(None, False, "AirMouse_JARVIS_v3")
        err = ctypes.get_last_error()
        if not handle or err == 183:
            return None
        return handle
    except Exception:
        return object()


def load_settings(cfg):
    smooth_idx = 1
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        cfg.move_gain = max(float(data.get("move_gain", cfg.move_gain)), 0.6)
        cfg.snap_enabled = bool(data.get("snap_enabled", cfg.snap_enabled))
        name = str(data.get("suavidade", "")).upper()
        found = False
        for i, (pname, cut, beta) in enumerate(SMOOTH_PRESETS):
            if pname == name:
                cfg.filter_min_cutoff = cut
                cfg.filter_beta = beta
                smooth_idx = i
                found = True
        cut = data.get("filter_min_cutoff")
        beta = data.get("filter_beta")
        if isinstance(cut, (int, float)) and isinstance(beta, (int, float)):
            cfg.filter_min_cutoff = min(max(float(cut), 0.4), 3.0)
            cfg.filter_beta = min(max(float(beta), 0.008), 0.08)
            if not found:
                smooth_idx = -1
            else:
                _, pc, pb = SMOOTH_PRESETS[smooth_idx]
                if abs(pc - cfg.filter_min_cutoff) > 1e-6 or abs(pb - cfg.filter_beta) > 1e-6:
                    smooth_idx = -1
    except Exception:
        pass
    return smooth_idx


def save_settings(cfg, smooth_name):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "move_gain": round(cfg.move_gain, 2),
                    "suavidade": smooth_name,
                    "filter_min_cutoff": round(cfg.filter_min_cutoff, 3),
                    "filter_beta": round(cfg.filter_beta, 4),
                    "snap_enabled": bool(cfg.snap_enabled),
                },
                fh,
                indent=2,
            )
        print(f"Definicoes gravadas em {SETTINGS_FILE}")
    except Exception as exc:
        print(f"ERRO ao gravar definicoes: {exc}")


def open_camera(cfg):
    candidates = [cfg.camera_index] if cfg.camera_index is not None else [0, 1, 2]
    for index in candidates:
        cam = CameraStream(index)
        if cam.open(cfg.frame_width, cfg.frame_height, 30):
            print(f"Camera {index} ativa.")
            return cam
        cam.release()
    return None


def draw_hand(frame, hand_frame, color):
    for a, b in HAND_CONNECTIONS:
        pa = tuple(int(v) for v in hand_frame.points_px[a])
        pb = tuple(int(v) for v in hand_frame.points_px[b])
        cv2.line(frame, pa, pb, (200, 200, 200), 1)
    px, py = int(hand_frame.palm_center[0]), int(hand_frame.palm_center[1])
    cv2.line(frame, (px - 14, py), (px + 14, py), color, 1)
    cv2.line(frame, (px, py - 14), (px, py + 14), color, 2)
    cv2.circle(frame, (px, py), 9, color, 2)


def draw_overlay(frame, all_frames, active_side, last_scroll, fps, cfg,
                 smooth_name, paused, show_help, flash, ui):
    h, w = frame.shape[:2]
    hand_frame = all_frames.get(active_side)
    color = BADGES[Gesture.NONE][1]

    for side, hf in all_frames.items():
        c = BADGES.get(hf.gesture, BADGES[Gesture.NONE])[1]
        if side != active_side:
            draw_hand(frame, hf, COLOR_GRAY)
        else:
            draw_hand(frame, hf, c)
            thumb = tuple(int(v) for v in hf.points_px[4])
            tip = tuple(int(v) for v in hf.index_tip)
            pinch_color = COLOR_GREEN if hf.gesture == Gesture.PINCH else COLOR_GRAY
            cv2.line(frame, thumb, tip, pinch_color, 2)
            if hf.gesture == Gesture.PEACE:
                mid = tuple(int(v) for v in hf.points_px[12])
                cv2.circle(frame, mid, 7, BADGES[Gesture.PEACE][1], 2)
            color = c

    label = "PAUSA" if paused else BADGES.get(
        hand_frame.gesture if hand_frame is not None else Gesture.NONE,
        BADGES[Gesture.NONE],
    )[0]
    cv2.rectangle(frame, (12, 10), (268, 66), COLOR_DARK, -1)
    cv2.rectangle(frame, (12, 10), (268, 66), color, 2)
    cv2.putText(frame, label, (24, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)

    x_right = w - 118
    if ui["ai_on"]:
        conf = ui["ai_conf"]
        ai_txt = f"IA {int(conf * 100):3d}%" if hand_frame is not None else "IA  ok"
        ai_col = COLOR_GREEN if conf >= cfg.ai_confidence_min else COLOR_WHITE
        cv2.rectangle(frame, (x_right, 10), (w - 12, 40), COLOR_DARK, -1)
        cv2.putText(frame, ai_txt, (x_right + 10, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, ai_col, 1, cv2.LINE_AA)
        x_right -= 96
    if ui.get("magnify"):
        cv2.rectangle(frame, (x_right, 10), (w - 12, 40), COLOR_DARK, -1)
        cv2.putText(frame, f"LUPA {ui['magnify']}", (x_right + 8, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_PINK, 1, cv2.LINE_AA)
        x_right -= 110
    if ui.get("hands"):
        cv2.rectangle(frame, (x_right, 10), (w - 12, 40), COLOR_DARK, -1)
        cv2.putText(frame, f"{ui['hands']} MAOS", (x_right + 10, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 1, cv2.LINE_AA)

    if ui["voice"] != "off":
        vtxt = {"on": "VOZ ON ", "listening": "VOZ <OUVINDO>"}.get(
            ui["voice"], f'VOZ {cfg.voice_wake_word.upper()}'
        )
        cv2.rectangle(frame, (12, 74), (190, 98), COLOR_DARK, -1)
        vcol = COLOR_PINK if ui["voice"] != "wake" else COLOR_GRAY
        if ui["voice"] == "on":
            vcol = COLOR_PINK
        cv2.putText(frame, vtxt, (20, 92),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, vcol, 1, cv2.LINE_AA)

    if ui["toast_until"] > time.monotonic() and ui["toast"]:
        txt = ui["toast"]
        (tw, _), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        tx = (w - tw) // 2
        cv2.rectangle(frame, (tx - 10, 44), (tx + tw + 10, 76), COLOR_DARK, -1)
        cv2.putText(frame, txt, (tx, 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_GREEN, 2, cv2.LINE_AA)

    if last_scroll is not None:
        cv2.putText(
            frame, f"scroll {last_scroll:+.0f} px/frame", (16, 112),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, BADGES[Gesture.PEACE][1], 1, cv2.LINE_AA,
        )

    if ui.get("light"):
        cv2.putText(frame, "LUZ BAIXA: realce ON", (16, 132),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 180, 255), 1, cv2.LINE_AA)

    cv2.putText(
        frame, "H ajuda | Q sai", (w - 170, h - 34),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_GRAY, 1, cv2.LINE_AA,
    )

    if hand_frame is not None:
        ratio = min(hand_frame.pinch_ratio / 1.2, 1.0)
        pinch_color = COLOR_GREEN if hand_frame.gesture == Gesture.PINCH else COLOR_GRAY
        cv2.rectangle(frame, (12, h - 30), (12 + int(ratio * (w - 24)), h - 24), pinch_color, -1)

    at_txt = "AT" if ui["autotune"] else ""
    strip = f"{fps:4.0f} fps | ganho {cfg.move_gain:.1f} | {smooth_name}"
    if at_txt:
        strip += f" | {at_txt}"
    if ui.get("tts"):
        strip += f" | voz-neural:{ui['tts']}"
    cv2.rectangle(frame, (0, h - 22), (w, h), COLOR_DARK, -1)
    cv2.putText(
        frame, strip, (max(w - 520, 8), h - 7),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 1, cv2.LINE_AA,
    )

    if show_help:
        lines = (
            "AJUDA",
            "mao aberta .... mover cursor",
            "pinca index ... botao esquerdo (manter=arrastar)",
            "punho ......... arrastar",
            "pinca medio ... clique direito",
            "dois dedos .... scroll",
            "tres dedos .... volume | polegar cima = play/pausa",
            "3 dedos ....... volume (mao cima/baixo)",
            "polegar cima .. play/pausa multimédia",
            "PALMAS ........ abrir/fechar assistente 3D",
            "2 maos abertas + afastar = lupa (zoom)",
            "[ / ] ......... ganho -/+",
            ", / . ......... suavidade",
            "m ............. snap magnetico ON/OFF",
            "b ............. assistente 3D",
            "a ............. auto-afinacao | v voz | s gravar",
            "espaco ........ pausar | Q sair",
            "voz: jarvis <comando natural>",
        )
        cv2.rectangle(frame, (12, 120), (430, 120 + 20 * len(lines) + 12), COLOR_DARK, -1)
        cv2.rectangle(frame, (12, 120), (430, 120 + 20 * len(lines) + 12), COLOR_GRAY, 1)
        for i, line in enumerate(lines):
            cv2.putText(
                frame, line, (24, 140 + 20 * i),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, COLOR_WHITE, 1, cv2.LINE_AA,
            )

    if flash > 0:
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), COLOR_GREEN, 6)
    return frame


VOLUME_STEP_PX = 12.0
_kb_ctl = None


def _media_tap(key, times=1):
    global _kb_ctl
    try:
        if _kb_ctl is None:
            from pynput.keyboard import Controller as _KC

            _kb_ctl = _KC()
        for _ in range(max(1, min(times, 8))):
            _kb_ctl.press(key)
            _kb_ctl.release(key)
    except Exception:
        pass


def _handle_media_event(event, value):
    if event == "volume":
        presses = int(abs(value) / VOLUME_STEP_PX)
        if presses >= 1:
            from pynput.keyboard import Key

            _media_tap(
                Key.media_volume_up if value > 0 else Key.media_volume_down,
                presses,
            )
            return "VOL " + ("+" * min(presses, 4) if value > 0 else "-" * min(presses, 4))
        return None
    if event == "play_pause":
        from pynput.keyboard import Key

        _media_tap(Key.media_play_pause, 1)
        return "PLAY/PAUSA"
    return None


class AppCtl:
    def __init__(self):
        self.exit_requested = False
        self.speaker: Any = None
        self.snap: Any = None
        self.assistant: Any = None
        self.magnifier: Any = None


def _release_if_dragging(state, mouse):
    if state.get("button_down"):
        mouse.release_left()
        state["button_down"] = False


def apply_command(action, value, cfg, mouse, state, ctx):
    now = time.monotonic()
    if action == "exit":
        ctx.exit_requested = True
        return "SAIR"
    if action == "pause":
        state["paused"] = True
        _release_if_dragging(state, mouse)
        state["emitter"].clear()
        return "PAUSA"
    if action == "resume":
        state["paused"] = False
        return "RETOMAR"
    if action == "pause_toggle":
        return apply_command(
            "resume" if state["paused"] else "pause",
            value, cfg, mouse, state, ctx,
        )
    if action == "help":
        state["show_help"] = not state["show_help"]
        return "AJUDA"
    if action == "save":
        save_settings(cfg, state["smooth_name"])
        return "GRAVAR"
    if action == "gain_up":
        cfg.move_gain = max(0.6, round(cfg.move_gain + 0.2, 2))
        state["tuner"].set_user_gain(cfg.move_gain)
        return f"GANHO {cfg.move_gain:.1f}"
    if action == "gain_down":
        cfg.move_gain = max(0.6, round(cfg.move_gain - 0.2, 2))
        state["tuner"].set_user_gain(cfg.move_gain)
        return f"GANHO {cfg.move_gain:.1f}"
    preset_map = {
        "smooth_suave": 0,
        "smooth_normal": 1,
        "smooth_reactivo": 2,
    }
    if action in preset_map:
        idx = preset_map[action]
        _, cut, beta = SMOOTH_PRESETS[idx]
        cfg.filter_min_cutoff = cut
        cfg.filter_beta = beta
        state["filters"].set_params(cut, beta)
        state["smooth_name"] = SMOOTH_PRESETS[idx][0]
        return SMOOTH_PRESETS[idx][0]
    if action == "assistant":
        if ctx.assistant is None:
            return "ASSISTENTE INDISPONIVEL"
        return ctx.assistant.toggle()
    if action == "assistant_close":
        if ctx.assistant is None:
            return "ASSISTENTE INDISPONIVEL"
        n = ctx.assistant.close()
        return "FECHAR ASSISTENTE" if n else "NAO ESTA ABERTO"
    if action == "magnify_on":
        if ctx.magnifier is None:
            return "LUPA INDISPONIVEL"
        return ctx.magnifier.force_on()
    if action == "magnify_off":
        if ctx.magnifier is None:
            return "LUPA INDISPONIVEL"
        return ctx.magnifier.force_off()
    if action == "snap_toggle":
        if ctx.snap is None or not ctx.snap.available:
            return "SNAP INDISPONIVEL"
        cfg.snap_enabled = ctx.snap.enabled
        return f"SNAP {ctx.snap.status}"
    if action == "left_click":
        if state["paused"] or state.get("button_down"):
            return None
        _click_assist(ctx, state, mouse, cfg)
        mouse.press_left()
        time.sleep(0.03)
        mouse.release_left()
        state["freeze_until"] = now + cfg.click_freeze_ms / 1000.0
        state["flash"] = 5
        return "CLIQUE ESQ"
    if action == "right_click":
        if state["paused"] or state.get("button_down"):
            return None
        _click_assist(ctx, state, mouse, cfg)
        mouse.right_click()
        state["freeze_until"] = now + cfg.click_freeze_ms / 1000.0
        state["flash"] = 5
        return "CLIQUE DIR"
    if action in ("scroll_up", "scroll_down"):
        if state["paused"]:
            return None
        amount = value if isinstance(value, (int, float)) and abs(value) >= 1 else 3
        mouse.scroll(amount if action == "scroll_up" else -amount)
        return "SCROLL +" if action == "scroll_up" else "SCROLL -"
    if action == "autotune_toggle":
        return state["tuner"].toggle()
    return None


def _click_assist(ctx, state, mouse, cfg):
    if ctx.snap is None or not cfg.snap_click_assist or not ctx.snap.enabled:
        return
    try:
        cur = mouse.mouse.position
        target = ctx.snap.assist_point(cur, time.perf_counter())
        if target is not None:
            mouse.mouse.position = (int(target[0]), int(target[1]))
            state["assist_used"] = True
    except Exception:
        pass


def run_loop(cfg, cam, tracker, mouse, smooth_idx, gesture_ai, voice, tuner, ctx, state):
    pool = HandPool(cfg, gesture_ai)
    filters = FilterPair2D(cfg.filter_min_cutoff, cfg.filter_beta)
    curve = AccelCurve(cfg.accel_min_gain, cfg.accel_max_gain,
                       cfg.accel_ref_speed, cfg.accel_expo)
    emitter = SmoothEmitter(mouse, cfg.emitter_rate_hz)
    emitter.start()

    clap = ClapDetector() if cfg.clap_enabled else None
    magnifier = ctx.magnifier
    light = LightBoost() if cfg.low_light_boost else None
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    state["smooth_name"] = (
        SMOOTH_PRESETS[smooth_idx][0] if smooth_idx >= 0 else "CUSTOM"
    )
    state.setdefault("paused", False)
    state.setdefault("show_help", False)
    state.setdefault("flash", 0)
    state.setdefault("freeze_until", 0.0)
    state.setdefault("button_down", False)
    state["filters"] = filters
    state["tuner"] = tuner
    state["emitter"] = emitter
    ui = {
        "ai_on": gesture_ai is not None,
        "ai_conf": 0.0,
        "voice": "off",
        "toast": "",
        "toast_until": 0.0,
        "autotune": tuner.enabled,
        "magnify": "",
        "hands": 0,
        "light": False,
        "tts": "",
    }

    last_palm = None
    prev_filtered = None
    jump_streak = 0
    fast_until = 0.0
    glitches = 0
    last_seq = -1
    last_scroll = None
    fps = 0.0
    infer_total = 0.0
    frames_done = 0
    warmup_left = max(cfg.warmup_frames, 0)
    started = None
    window = "AirMouse"
    active_side = None
    last_accept_t = None
    last_hand_t = None
    dt_ema = 0.05
    exposure_tried = False
    gray_check = 0

    def toast(text):
        ui["toast"] = text
        ui["toast_until"] = time.monotonic() + 1.3

    try:
        if cfg.preview:
            cv2.namedWindow(window, cv2.WINDOW_NORMAL)

        while True:
            loop_start = time.perf_counter()
            frame, seq = cam.read()
            if frame is None:
                time.sleep(0.002)
                continue

            if warmup_left > 0:
                warmup_left -= 1
                if cfg.preview:
                    cv2.imshow(window, frame)
                    if (cv2.waitKey(1) & 0xFF) in (ord("q"), 27):
                        break
                continue

            if seq == last_seq:
                time.sleep(0.002)
                continue
            last_seq = seq

            if cfg.mirror:
                frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            gray_check += 1
            if light is not None and gray_check % light.check_every == 0:
                gmean = float(cv2.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))[0])
                evt = light.feed(gmean)
                if evt == "on":
                    toast("LUZ BAIXA: realce ativado")
                    if not exposure_tried:
                        exposure_tried = True
                        cam.try_boost_exposure()
                elif evt == "off":
                    toast("LUZ NORMAL")
            if light is not None and light.active:
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                lch, ach, bch = cv2.split(lab)
                lch = clahe.apply(lch)
                frame = cv2.cvtColor(cv2.merge((lch, ach, bch)), cv2.COLOR_LAB2BGR)

            ts_ms = time.monotonic_ns() // 1_000_000
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            t_infer = time.perf_counter()
            hands, sides = tracker.process(rgb, ts_ms)
            infer_total += (time.perf_counter() - t_infer) * 1000.0

            results = pool.update(hands, sides, w, h)
            now = time.perf_counter()

            event = None
            ev_value = None
            hand_frame = None

            if results:
                if active_side in results:
                    hand_frame, event, ev_value = results[active_side]
                else:
                    prev_active = active_side
                    active_side = "Right" if "Right" in results else next(iter(results))
                    hand_frame, event, ev_value = results[active_side]
                    if prev_active is not None:
                        filters.reset()
                        last_palm = None
                        prev_filtered = None
                        jump_streak = 0
                        fast_until = 0.0
                        emitter.clear()

            all_frames = {s: r[0] for s, r in results.items()}
            ui["hands"] = len(results)

            if clap is not None and len(results) == 2 and not state["paused"]:
                palms = [r[0].palm_center for r in results.values()]
                scales = [r[0].hand_scale_px for r in results.values()]
                if clap.update(palms, scales, now):
                    note = ctx.assistant.toggle() if ctx.assistant else "ASSISTENTE OFF"
                    toast(note)
                    if ctx.speaker:
                        ctx.speaker.say(note)

            mag_note = None
            if magnifier is not None and len(results) == 2:
                entries = [
                    (r[0].gesture, r[0].palm_center, r[0].hand_scale_px)
                    for r in results.values()
                ]
                mag_note = magnifier.update(entries, now)
            ui["magnify"] = magnifier.last_action if (magnifier and magnifier.on) else ""

            if mag_note:
                toast(mag_note)

            if hand_frame is not None and hand_frame.gesture != Gesture.NONE:
                palm = hand_frame.palm_center
                accept = True
                if last_palm is not None:
                    d = math.hypot(palm[0] - last_palm[0], palm[1] - last_palm[1])
                    limit = cfg.max_jump_frac * w
                    if d <= limit:
                        jump_streak = 0
                        fast_until = 0.0
                    elif now < fast_until:
                        pass
                    elif jump_streak < 2:
                        jump_streak += 1
                        glitches += 1
                        accept = False
                    else:
                        jump_streak = 0
                        fast_until = now + 0.5
                if accept:
                    if last_accept_t is not None:
                        inst_dt = now - last_accept_t
                        dt_ema = dt_ema * 0.7 + min(max(inst_dt, 0.008), 0.2) * 0.3
                    last_accept_t = now
                    last_palm = palm
                    last_hand_t = now
                    fx, fy = filters.filter(*palm)
                    if prev_filtered is None:
                        prev_filtered = (fx, fy)
                    dx = fx - prev_filtered[0]
                    dy = fy - prev_filtered[1]
                    prev_filtered = (fx, fy)

                    gain = cfg.move_gain * curve.apply(filters.vx, filters.vy)
                    sx = mouse.screen_w / w
                    sy = mouse.screen_h / h
                    mdx = dx * gain * sx
                    mdy = dy * gain * sy
                    movable = (
                        not state["paused"]
                        and now >= state["freeze_until"]
                        and hand_frame.gesture in MOVE_GESTURES
                        and not (magnifier is not None and magnifier.on)
                    )
                    if movable and abs(mdx) < cfg.deadzone_px:
                        mdx = 0.0
                    if movable and abs(mdy) < cfg.deadzone_px:
                        mdy = 0.0
                    if movable:
                        vspeed_cap = curve.ref_speed * 4.0 * cfg.move_gain
                        vxs = mdx / dt_ema if dt_ema > 0 else 0.0
                        vys = mdy / dt_ema if dt_ema > 0 else 0.0
                        sp = math.hypot(vxs, vys)
                        if sp > vspeed_cap and sp > 0:
                            k = vspeed_cap / sp
                            vxs *= k
                            vys *= k
                        lx, ly = lead_offset(vxs, vys, cfg.predict_ms)
                        try:
                            cx, cy = mouse.mouse.position
                            pxl, pyl = ctx.snap.pull((cx, cy), now) if ctx.snap else (0.0, 0.0)
                        except Exception:
                            pxl = pyl = 0.0
                        emitter.push(mdx + lx + pxl, mdy + ly + pyl, dt_ema)
                    tuner.feed(True, filters, mdx, mdy)
            else:
                if hand_frame is None:
                    active_side = None
                filters.reset()
                last_palm = None
                prev_filtered = None
                jump_streak = 0
                fast_until = 0.0
                last_accept_t = None
                emitter.clear()
                tuner.feed(False, filters, 0.0, 0.0)
                if state["button_down"] and (
                    last_hand_t is None or now - last_hand_t > 0.20
                ):
                    mouse.release_left()
                    state["button_down"] = False

            if event and (not state["paused"] or event == "left_up"):
                if event == "left_down":
                    _click_assist(ctx, state, mouse, cfg)
                    mouse.press_left()
                    state["button_down"] = True
                    state["freeze_until"] = now + cfg.click_freeze_ms / 1000.0
                    state["flash"] = 5
                    emitter.clear()
                elif event == "left_up":
                    mouse.release_left()
                    state["button_down"] = False
                    emitter.clear()
                elif event == "right_click":
                    _click_assist(ctx, state, mouse, cfg)
                    mouse.right_click()
                    state["freeze_until"] = now + cfg.click_freeze_ms / 1000.0
                    state["flash"] = 5
                    emitter.clear()
                elif event == "scroll" and ev_value is not None:
                    mouse.scroll(ev_value * cfg.scroll_gain_factor)
                else:
                    media_note = _handle_media_event(event, ev_value)
                    if media_note:
                        toast(media_note)

            if event == "scroll" and ev_value is not None:
                last_scroll = ev_value
            elif hand_frame is None or hand_frame.gesture != Gesture.PEACE:
                last_scroll = None

            tune_note = tuner.maybe_apply(time.monotonic(), filters, cfg)
            if tune_note:
                toast(tune_note)
                state["smooth_name"] = "AUTO"

            while True:
                try:
                    cmd = voice.cmd_queue.get_nowait() if voice else None
                except Exception:
                    cmd = None
                if cmd is None:
                    break
                action = cmd.get("action")
                note = apply_command(action, cmd.get("value"), cfg, mouse, state, ctx)
                if note:
                    print(f"[voz] {cmd.get('text','')!r} -> {note}")
                    toast(note)
                    if ctx.speaker:
                        ctx.speaker.say(note)
                if ctx.exit_requested:
                    break
            if ctx.exit_requested:
                break

            dt = time.perf_counter() - loop_start
            inst = 1.0 / dt if dt > 0 else 0.0
            fps = inst if frames_done == 0 else fps * 0.9 + inst * 0.1
            if started is None:
                started = loop_start
            frames_done += 1

            ui["ai_conf"] = hand_frame.ai_conf if hand_frame is not None else 0.0
            if state.get("pinch_debug") and hand_frame is not None and now > state["dbg_until"]:
                state["dbg_until"] = now + 0.25
                print(
                    f"[pincha] idx={hand_frame.pinch_ratio:.2f} "
                    f"mid={hand_frame.pinch_mid_ratio:.2f} "
                    f"lim={cfg.pinch_on_ratio:.2f} -> {hand_frame.gesture.name}"
                )
            if voice:
                st = voice.status
                ui["voice"] = {"off": "off", "wake": "wake",
                               "listening": "listening"}.get(st, st)
            else:
                ui["voice"] = "off"
            ui["autotune"] = tuner.enabled
            ui["light"] = light.active if light else False
            if ctx.speaker:
                ui["tts"] = ctx.speaker.status

            if cfg.preview:
                draw_overlay(
                    frame, all_frames, active_side, last_scroll, fps, cfg,
                    state["smooth_name"], state["paused"], state["show_help"],
                    state["flash"], ui,
                )
                cv2.imshow(window, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord(" "):
                    note = apply_command("pause_toggle", None, cfg, mouse, state, ctx)
                    if note:
                        toast(note)
                elif key == ord("["):
                    cfg.move_gain = max(0.6, round(cfg.move_gain - 0.2, 2))
                    tuner.set_user_gain(cfg.move_gain)
                elif key == ord("]"):
                    cfg.move_gain = max(0.6, round(cfg.move_gain + 0.2, 2))
                    tuner.set_user_gain(cfg.move_gain)
                elif key in (ord(","), ord(".")):
                    step = -1 if key == ord(",") else 1
                    cur = next(
                        (i for i, p in enumerate(SMOOTH_PRESETS) if p[0] == state["smooth_name"]),
                        1,
                    )
                    idx = (cur + step) % len(SMOOTH_PRESETS)
                    _, cut, beta = SMOOTH_PRESETS[idx]
                    cfg.filter_min_cutoff = cut
                    cfg.filter_beta = beta
                    filters.set_params(cut, beta)
                    state["smooth_name"] = SMOOTH_PRESETS[idx][0]
                elif key == ord("s"):
                    save_settings(cfg, state["smooth_name"])
                elif key == ord("h"):
                    state["show_help"] = not state["show_help"]
                elif key == ord("v"):
                    if voice is not None:
                        voice.toggle()
                elif key == ord("a"):
                    toast(tuner.toggle())
                elif key == ord("m"):
                    if ctx.snap is not None and ctx.snap.available:
                        cfg.snap_enabled = ctx.snap.enabled
                        note = apply_command("snap_toggle", None, cfg, mouse, state, ctx)
                        toast(str(note))
                elif key == ord("b"):
                    note = apply_command("assistant", None, cfg, mouse, state, ctx)
                    toast(str(note))
                    if ctx.speaker:
                        ctx.speaker.say(str(note))

            if state["flash"] > 0:
                state["flash"] -= 1

            if cfg.selftest_frames and frames_done >= cfg.selftest_frames:
                elapsed = time.perf_counter() - started
                avg_fps = frames_done / elapsed if elapsed > 0 else 0.0
                avg_infer = infer_total / frames_done if frames_done else 0.0
                tts_name = ctx.speaker.status if ctx.speaker else "-"
                snap_st = ctx.snap.status if ctx.snap else "-"
                print(
                    f"[selftest] {frames_done} frames | {avg_fps:.1f} fps"
                    f" | inferencia {avg_infer:.1f} ms | glitches {glitches}"
                    f" | tts={tts_name} | snap={snap_st}"
                )
                break
    finally:
        emitter.stop()
        if state["button_down"]:
            mouse.release_left()
            state["button_down"] = False

    return state


def resolve_assistant(cfg):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_dir = cfg.assistant_dir or base_dir
    if os.path.isfile(os.path.join(server_dir, "server.py")):
        return Assistant3D(
            server_dir,
            cfg.assistant_url,
            window_hint=cfg.assistant_title,
            port=cfg.assistant_port,
        )
    print("Aviso: barehands (server.py) nao encontrado; assistente 3D desativado.")
    return None


def main():
    args = parse_args()
    cfg = Config()
    cfg.selftest_frames = args.frames

    mutex = acquire_single_instance()
    if mutex is None:
        print("AirMouse ja esta em execucao.")
        return 1

    if args.reset_config:
        try:
            if os.path.isfile(SETTINGS_FILE):
                os.remove(SETTINGS_FILE)
                print("Definicoes apagadas.")
        except Exception:
            pass
    smooth_idx = load_settings(cfg)

    if args.camera is not None:
        cfg.camera_index = args.camera
    if args.gain is not None:
        cfg.move_gain = args.gain
    if args.tray:
        cfg.preview = bool(args.preview) and not args.no_preview
    else:
        if args.no_preview:
            cfg.preview = False
    if args.no_voice:
        cfg.voice_enabled = False
    if args.no_autotune:
        cfg.autotune_enabled = False
    if args.voice_always:
        cfg.voice_always_on = True
    if args.no_tts:
        cfg.tts_enabled = False
    if args.whisper_model:
        cfg.whisper_model = args.whisper_model

    gesture_ai = None
    if cfg.ai_enabled and not args.no_ai:
        try:
            ai_path = ensure_ai_model(cfg.ai_model_path)
            gesture_ai = GestureAI(ai_path)
            print(f"IA de gestos ativa (confianca min {cfg.ai_confidence_min:.2f}).")
        except FileNotFoundError as exc:
            print(f"Aviso: IA de gestos indisponivel ({exc}); a usar regras geometricas.")

    model_path = ensure_model(cfg.model_path, cfg.model_url)

    cam = open_camera(cfg)
    if cam is None:
        print("ERRO: nenhuma camera encontrada.")
        return 1

    tracker = HandTracker(model_path, num_hands=cfg.num_hands, use_gpu=args.gpu)
    mouse = MouseCtl()
    tuner = AutoTuner(cfg)

    speaker = None
    if cfg.tts_enabled:
        voice_files = (
            (cfg.piper_onnx_url, os.path.join(cfg.piper_model_dir, "pt_BR-faber-medium.onnx")),
            (cfg.piper_conf_url, os.path.join(cfg.piper_model_dir, "pt_BR-faber-medium.onnx.json")),
        )
        speaker = Speaker(enabled=True, model_dir=cfg.piper_model_dir,
                          voice_files=voice_files)
        speaker.start()

    snap = SnapEngine(radius_px=cfg.snap_radius_px, strength=cfg.snap_strength,
                      poll_hz=cfg.snap_poll_hz, enabled=cfg.snap_enabled)
    snap.start()

    assistant = resolve_assistant(cfg)
    magnifier = MagnifierCtl(cfg.magnifier_step_frac) if cfg.magnifier_enabled else None

    voice = None
    if cfg.voice_enabled:
        import queue as _queue

        voice = VoiceEngine(cfg, _queue.Queue())
        if speaker is not None:
            voice.set_speaker(speaker)
        voice.start()

    ctx = AppCtl()
    state = {
        "paused": False,
        "show_help": False,
        "flash": 0,
        "freeze_until": 0.0,
        "button_down": False,
        "pinch_debug": bool(getattr(args, "pinch_debug", False)),
        "dbg_until": 0.0,
    }
    tray_icon = None
    tray_adapter = None

    def tray_apply(action, value):
        note = apply_command(action, value, cfg, mouse, state, ctx)
        if note and not cfg.preview:
            if tray_icon:
                tray_icon.notify("AirMouse", note)
            print(f"[bandeja] {note}")

    if args.tray:
        tray_adapter = TrayAppAdapter(state, cfg, voice, snap, tuner,
                                      assistant, tray_apply)
        tray_icon = TrayIcon(tray_adapter)
        if tray_icon.start():
            print("Icone na bandeja ativo.")

    ctx.speaker = speaker
    ctx.snap = snap
    ctx.assistant = assistant
    ctx.magnifier = magnifier

    smooth_label = SMOOTH_PRESETS[smooth_idx][0] if smooth_idx >= 0 else "CUSTOM"
    print(f"Ecra: {mouse.screen_w}x{mouse.screen_h} | ganho: {cfg.move_gain:.1f} | suavidade: {smooth_label}")
    print(
        "Gestos: mao aberta=mover | pinca index=clique esquerdo/arrastar |"
        " punho=arrastar | pinca medio=clique direito | dois dedos=scroll |"
        " 3 dedos=volume | polegar cima=play/pausa"
    )
    print(
        "Novo: palmas=assistente 3D | 2 maos abertas+lupa | snap magnetico (tecla M)"
        " | predicao de movimento ON"
    )
    print(
        "Teclas: [ ] ganho | , . suavidade | a auto-afinacao | v voz | m snap |"
        " b assistente | s gravar | h ajuda | espaco pausa | Q sair"
    )

    exit_code = 0
    initial_params = (cfg.move_gain, cfg.filter_min_cutoff, cfg.filter_beta)
    try:
        end_state = run_loop(
            cfg, cam, tracker, mouse, smooth_idx, gesture_ai, voice, tuner, ctx,
            state,
        )
        if (
            (cfg.move_gain, cfg.filter_min_cutoff, cfg.filter_beta) != initial_params
            or end_state.get("touched_settings")
        ) and tuner.enabled:
            save_settings(cfg, end_state["smooth_name"])
    except KeyboardInterrupt:
        print("\nAte ja!")
    except Exception as exc:
        print(f"ERRO fatal: {exc}")
        exit_code = 1
    finally:
        if tray_icon is not None:
            tray_icon.stop()
        if voice is not None:
            voice.stop()
        if speaker is not None:
            speaker.stop()
        snap.stop()
        tracker.close()
        cam.release()
        cv2.destroyAllWindows()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
