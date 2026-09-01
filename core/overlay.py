"""OpenCV preview rendering (overlay, skeleton, badges).

Extraído de ``main.py``: apenas apresentação do preview; a lógica vive em
``core.engine.process_frame``, partilhada com a MainWindow PySide6.
"""
import time

import cv2

from core.gestures import Gesture
from core.tracker import HAND_CONNECTIONS

BADGES = {
    Gesture.NONE: ("SEM MAO", (150, 150, 150)),
    Gesture.OPEN: ("MOVER", (80, 200, 255)),
    Gesture.ONE: ("MOVER 1D", (80, 200, 255)),
    Gesture.PINCH: ("CLIQUE ESQ", (90, 220, 90)),
    Gesture.PINCH_MID: ("CLIQUE DIR", (60, 60, 235)),
    Gesture.FIST: ("SCROLL", (255, 80, 200)),
    Gesture.PEACE: ("DOIS DEDOS", (255, 80, 200)),
    Gesture.THREE: ("VOLUME", (255, 170, 60)),
    Gesture.THUMB_UP: ("PLAY/PAUSA", (140, 225, 225)),
    Gesture.PINKY: ("COPIAR", (180, 120, 255)),
    Gesture.SHAKA: ("COLAR", (120, 200, 180)),
}
COLOR_GRAY = (160, 160, 160)
COLOR_WHITE = (245, 245, 245)
COLOR_GREEN = (90, 220, 90)
COLOR_PINK = (255, 80, 200)
COLOR_DARK = (22, 22, 22)


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
            if hf.gesture == Gesture.FIST:
                mid = tuple(int(v) for v in hf.points_px[12])
                cv2.circle(frame, mid, 7, BADGES[Gesture.FIST][1], 2)
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
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, BADGES[Gesture.FIST][1], 1, cv2.LINE_AA,
        )

    if ui.get("light"):
        cv2.putText(frame, "LUZ BAIXA: realce ON", (16, 132),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 180, 255), 1, cv2.LINE_AA)

    cv2.putText(
        frame, "H ajuda | Q sai", (w - 170, h - 34),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_GRAY, 1, cv2.LINE_AA,
    )

    if cfg.license_tier != "pro":
        wtxt = "MAouse FREE"
        (tww, twh), _ = cv2.getTextSize(wtxt, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.putText(
            frame, wtxt, ((w - tww) // 2, 44),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (90, 180, 255), 2, cv2.LINE_AA,
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
            "mao aberta / 1 dedo ... mover cursor",
            "pinca index ............ botao esquerdo (manter=arrastar)",
            "punho + cima/baixo ..... scroll",
            "pinca medio ............ clique direito",
            "dois dedos ............. (sem funcao)",
            "tres dedos + cima/baixo = volume",
            "polegar cima ........... play/pausa multimédia",
            "dedo mindinho .......... copiar (Ctrl+C)",
            "polegar + mindinho ..... colar (Ctrl+V)",
            "swipe < com mao esq ..... janela anterior (Alt+Tab)",
            "swipe > com mao esq ..... proxima janela (Alt+Tab)",
            "segurar mao esq aberta ... escolher janela (alternador)",
            "dois dedos esq (2 maos)  diminuir brilho",
            "dois dedos dir (2 maos)  aumentar brilho",
            "fechar/abrir punho x2 .. Win+D",
            "bye bye (onda) ......... minimizar janela (Win+↓)",
            "ondas 2 maos ........... Alt+Tab",
            "PALMAS (x3) ........... Alt+Tab",
            "2 maos abertas + afastar = lupa (zoom)",
            "[ / ] ................. ganho -/+",
            ", / . ................. suavidade",
            "m ..................... snap magnetico ON/OFF",
            "a ............. auto-afinacao | v voz | s gravar",
            "espaco ................ pausar | Q sair",
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
