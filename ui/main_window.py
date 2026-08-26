"""Main frameless window with QTimer processing loop."""
import math
import time

import cv2
import numpy as np

from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QMainWindow, QWidget, QLabel, QApplication

from config import Config
from ui.theme import (
    MAIN_STYLESHEET, BG_PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY,
    FONT_MONO, FONT_STATUS,
    init_gesture_colors, gesture_color, gesture_label,
)
from ui.camera_view import CameraView
from ui.gesture_badge import GestureBadge
from ui.status_indicators import StatusBadges
from ui.voice_bar import VoiceBar
from ui.toast import Toast
from ui.help_panel import HelpPanel

from core.gestures import Gesture
from core.filters import FilterPair2D, AccelCurve
from core.motion import SmoothEmitter, lead_offset
from core.twohand import HandPool
from core.light import LightBoost


MOVE_GESTURES = frozenset({Gesture.OPEN, Gesture.ONE, Gesture.PINCH, Gesture.FIST})


class MainWindow(QMainWindow):

    def __init__(self, cfg, cam, tracker, mouse, gesture_ai=None,
                 voice=None, tuner=None, speaker=None, snap=None,
                 assistant=None, magnifier=None):
        super().__init__()
        init_gesture_colors()

        self._cfg = cfg
        self._cam = cam
        self._tracker = tracker
        self._mouse = mouse
        self._gesture_ai = gesture_ai
        self._voice = voice
        self._tuner = tuner
        self._speaker = speaker
        self._snap = snap
        self._assistant = assistant
        self._magnifier = magnifier

        self._filters = FilterPair2D(cfg.filter_min_cutoff, cfg.filter_beta)
        self._curve = AccelCurve(cfg.accel_min_gain, cfg.accel_max_gain,
                                 cfg.accel_ref_speed, cfg.accel_expo)
        self._pool = HandPool(cfg, gesture_ai)
        self._emitter = SmoothEmitter(mouse, cfg.emitter_rate_hz)
        self._light = LightBoost() if cfg.low_light_boost else None
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

        self._paused = False
        self._show_help = False
        self._smooth_name = "NORMAL"
        self._flash = 0
        self._freeze_until = 0.0
        self._button_down = False
        self._last_palm = None
        self._prev_filtered = None
        self._jump_streak = 0
        self._fast_until = 0.0
        self._dt_ema = 0.05
        self._last_accept_t = None
        self._last_hand_t = None
        self._active_side = None
        self._last_frame = None
        self._fps = 0.0
        self._fps_counter = 0
        self._fps_time = time.perf_counter()
        self._warmup = cfg.warmup_frames
        self._left_fist_prev = False
        self._right_fist_prev = False

        self._build_ui()
        self._build_shortcuts()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(0)
        self._emitter.start()

    def _build_ui(self):
        self.setWindowTitle("Mãouse")
        self.setObjectName("MainWindow")
        self.setMinimumSize(640, 480)
        self.resize(800, 600)
        self.setStyleSheet(MAIN_STYLESHEET)
        self.setWindowFlags(Qt.FramelessWindowHint)

        central = QWidget()
        central.setObjectName("MainWindow")
        self.setCentralWidget(central)

        self._cam_view = CameraView(central)
        self._cam_view.setGeometry(0, 0, 800, 600)

        self._gesture_badge = GestureBadge(central)
        self._gesture_badge.move(12, 10)

        self._voice_bar = VoiceBar(central)
        self._voice_bar.move(12, 70)

        self._status = StatusBadges(central)
        self._status.move(0, 10)
        self._status.resize(300, 28)

        self._toast = Toast(central)

        self._help = HelpPanel(central)
        self._help.move(12, 120)

        self._status_bar = QLabel(central)
        self._status_bar.setObjectName("StatusBar")
        self._status_bar.setFont(FONT_STATUS)
        self._status_bar.setFixedHeight(22)

        self._fps_lbl = QLabel(central)
        self._fps_lbl.setObjectName("StatusBar")
        self._fps_lbl.setFont(FONT_MONO)
        self._fps_lbl.setFixedHeight(22)
        self._fps_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def _build_shortcuts(self):
        pass

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Q, Qt.Key_Escape):
            self.close()
        elif key == Qt.Key_Space:
            self._paused = not self._paused
            self._toast.show_toast("PAUSA" if self._paused else "RETOMAR")
        elif key in (Qt.Key_H, Qt.Key_F1):
            self._show_help = not self._show_help
            self._help.toggle()
        elif key == Qt.Key_S:
            self._save_settings()
            self._toast.show_toast("GRAVAR")
        elif key == Qt.Key_A:
            if self._tuner:
                self._toast.show_toast(self._tuner.toggle())
        elif key == Qt.Key_V:
            if self._voice:
                self._voice.toggle()
        elif key == Qt.Key_M:
            if self._snap and self._snap.available:
                self._cfg.snap_enabled = not self._cfg.snap_enabled
                self._toast.show_toast(f"SNAP {'ON' if self._cfg.snap_enabled else 'OFF'}")
        elif key == Qt.Key_F2:
            self._open_settings()
        elif key == Qt.Key_BracketLeft:
            self._cfg.move_gain = max(0.6, round(self._cfg.move_gain - 0.2, 2))
            if self._tuner:
                self._tuner.set_user_gain(self._cfg.move_gain)
            self._toast.show_toast(f"GANHO {self._cfg.move_gain:.1f}")
        elif key == Qt.Key_BracketRight:
            self._cfg.move_gain = max(0.6, round(self._cfg.move_gain + 0.2, 2))
            if self._tuner:
                self._tuner.set_user_gain(self._cfg.move_gain)
            self._toast.show_toast(f"GANHO {self._cfg.move_gain:.1f}")
        elif key == Qt.Key_Comma:
            self._step_smooth(-1)
        elif key == Qt.Key_Period:
            self._step_smooth(+1)
        else:
            super().keyPressEvent(event)

    def _step_smooth(self, direction):
        presets = [("SUAVE", 0.9, 0.02), ("NORMAL", 1.4, 0.028), ("REACTIVO", 2.2, 0.05)]
        cur = next((i for i, (n, _, _) in enumerate(presets) if n == self._smooth_name), 1)
        idx = (cur + direction) % len(presets)
        name, cut, beta = presets[idx]
        self._cfg.filter_min_cutoff = cut
        self._cfg.filter_beta = beta
        self._filters.set_params(cut, beta)
        self._smooth_name = name
        self._toast.show_toast(name)

    def _open_settings(self):
        from ui.settings_dlg import SettingsDialog
        dlg = SettingsDialog(self._cfg, self._smooth_name, self)
        if dlg.exec() == SettingsDialog.Accepted:
            self._smooth_name = dlg.smooth_name
            self._filters.set_params(self._cfg.filter_min_cutoff, self._cfg.filter_beta)
            self._toast.show_toast("Definicoes atualizadas")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._cam_view.setGeometry(0, 0, w, h)
        self._status.move(w - 310, 10)
        self._status.resize(300, 28)
        self._status_bar.setGeometry(0, h - 22, w, 22)
        self._fps_lbl.setGeometry(w - 100, h - 22, 90, 22)
        tw = self._toast.width() if self._toast.width() > 0 else 200
        self._toast.move((w - tw) // 2, 50)

    # ── Processing Loop ─────────────────────────────────────────────
    def _tick(self):
        frame, seq = self._cam.read()
        if frame is None:
            return

        if self._warmup > 0:
            self._warmup -= 1
            return

        if self._cfg.mirror:
            frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        if self._light is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gmean = float(cv2.mean(gray)[0])
            evt = self._light.feed(gmean)
            if evt:
                self._toast.show_toast(
                    "LUZ BAIXA: realce ativado" if evt == "on" else "LUZ NORMAL"
                )
        if self._light is not None and self._light.active:
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            lch, ach, bch = cv2.split(lab)
            lch = self._clahe.apply(lch)
            frame = cv2.cvtColor(cv2.merge((lch, ach, bch)), cv2.COLOR_LAB2BGR)

        ts_ms = time.monotonic_ns() // 1_000_000
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hands, sides = self._tracker.process(rgb, ts_ms)
        results = self._pool.update(hands, sides, w, h)
        now = time.perf_counter()

        event = None
        ev_value = None
        hand_frame = None

        if results:
            if self._active_side in results:
                hand_frame, event, ev_value = results[self._active_side]
            else:
                self._active_side = "Right" if "Right" in results else next(iter(results))
                hand_frame, event, ev_value = results[self._active_side]
                self._filters.reset()
                self._last_palm = None
                self._prev_filtered = None
                self._jump_streak = 0
                self._fast_until = 0.0
                self._emitter.clear()

        all_frames = {s: r[0] for s, r in results.items()}

        self._last_frame = frame
        self._process_movement(hand_frame, all_frames, w, h, now)
        self._process_events(event, ev_value, now)
        self._process_voice()
        self._process_autotune(now)
        self._update_fps()

        if self._flash > 0:
            self._flash -= 1

        self._refresh_ui(all_frames, hand_frame)

    def _process_movement(self, hand_frame, all_frames, w, h, now):
        if hand_frame is not None and hand_frame.gesture != Gesture.NONE:
            palm = hand_frame.palm_center
            accept = True
            if self._last_palm is not None:
                d = math.hypot(palm[0] - self._last_palm[0], palm[1] - self._last_palm[1])
                limit = self._cfg.max_jump_frac * w
                if d <= limit:
                    self._jump_streak = 0
                    self._fast_until = 0.0
                elif now < self._fast_until:
                    pass
                elif self._jump_streak < 2:
                    self._jump_streak += 1
                    accept = False
                else:
                    self._jump_streak = 0
                    self._fast_until = now + 0.5

            if accept:
                if self._last_accept_t is not None:
                    inst_dt = now - self._last_accept_t
                    self._dt_ema = self._dt_ema * 0.7 + min(max(inst_dt, 0.008), 0.2) * 0.3
                self._last_accept_t = now
                self._last_palm = palm
                self._last_hand_t = now
                fx, fy = self._filters.filter(*palm)
                if self._prev_filtered is None:
                    self._prev_filtered = (fx, fy)
                dx = fx - self._prev_filtered[0]
                dy = fy - self._prev_filtered[1]
                self._prev_filtered = (fx, fy)

                gain = self._cfg.move_gain * self._curve.apply(self._filters.vx, self._filters.vy)
                sx = self._mouse.screen_w / max(w, 1)
                sy = self._mouse.screen_h / max(h, 1)
                mdx = dx * gain * sx
                mdy = dy * gain * sy
                movable = (
                    not self._paused
                    and now >= self._freeze_until
                    and hand_frame.gesture in MOVE_GESTURES
                    and not (self._magnifier is not None and self._magnifier.on)
                )
                if movable:
                    if abs(mdx) < self._cfg.deadzone_px:
                        mdx = 0.0
                    if abs(mdy) < self._cfg.deadzone_px:
                        mdy = 0.0
                    if abs(mdx) > 0 or abs(mdy) > 0:
                        lx, ly = lead_offset(self._filters.vx, self._filters.vy, self._cfg.predict_ms)
                        try:
                            cx, cy = self._mouse.mouse.position
                            pxl, pyl = self._snap.pull((cx, cy), now) if self._snap else (0.0, 0.0)
                        except Exception:
                            pxl = pyl = 0.0
                        self._emitter.push(mdx + lx + pxl, mdy + ly + pyl, self._dt_ema)
                if self._tuner:
                    self._tuner.feed(True, self._filters, mdx, mdy)
        else:
            if hand_frame is None:
                self._active_side = None
            self._filters.reset()
            self._last_palm = None
            self._prev_filtered = None
            self._jump_streak = 0
            self._fast_until = 0.0
            self._last_accept_t = None
            self._emitter.clear()
            if self._tuner:
                self._tuner.feed(False, self._filters, 0.0, 0.0)
            if self._button_down and (self._last_hand_t is None or now - self._last_hand_t > 0.20):
                self._mouse.release_left()
                self._button_down = False

    def _process_events(self, event, ev_value, now):
        if not event or (self._paused and event != "left_up"):
            return
        if event == "left_down":
            self._mouse.press_left()
            self._button_down = True
            self._freeze_until = now + self._cfg.click_freeze_ms / 1000.0
            self._flash = 5
            self._emitter.clear()
        elif event == "left_up":
            self._mouse.release_left()
            self._button_down = False
            self._emitter.clear()
        elif event == "right_click":
            self._mouse.right_click()
            self._freeze_until = now + self._cfg.click_freeze_ms / 1000.0
            self._flash = 5
            self._emitter.clear()
        elif event == "copy":
            self._key_combo("ctrl+c")
            self._toast.show_toast("COPIAR (Ctrl+C)")
            self._freeze_until = now + self._cfg.click_freeze_ms / 1000.0
            self._flash = 5
        elif event == "paste":
            self._key_combo("ctrl+v")
            self._toast.show_toast("COLAR (Ctrl+V)")
            self._freeze_until = now + self._cfg.click_freeze_ms / 1000.0
            self._flash = 5
        elif event == "scroll" and ev_value is not None:
            self._mouse.scroll(ev_value * self._cfg.scroll_gain_factor)
        else:
            note = self._handle_media(event, ev_value)
            if note:
                self._toast.show_toast(note)

    def _process_voice(self):
        if not self._voice:
            return
        while True:
            try:
                cmd = self._voice.cmd_queue.get_nowait()
            except Exception:
                break
            action = cmd.get("action")
            if action == "pause_toggle":
                self._paused = not self._paused
                note = "PAUSA" if self._paused else "RETOMAR"
            elif action == "pause":
                self._paused = True
                note = "PAUSA"
            elif action == "resume":
                self._paused = False
                note = "RETOMAR"
            elif action == "gain_up":
                self._cfg.move_gain = max(0.6, round(self._cfg.move_gain + 0.2, 2))
                if self._tuner:
                    self._tuner.set_user_gain(self._cfg.move_gain)
                note = f"GANHO {self._cfg.move_gain:.1f}"
            elif action == "gain_down":
                self._cfg.move_gain = max(0.6, round(self._cfg.move_gain - 0.2, 2))
                if self._tuner:
                    self._tuner.set_user_gain(self._cfg.move_gain)
                note = f"GANHO {self._cfg.move_gain:.1f}"
            elif action == "exit":
                note = "SAIR"
                self.close()
            elif action == "snap_toggle":
                if self._snap and self._snap.available:
                    self._cfg.snap_enabled = not self._cfg.snap_enabled
                    note = f"SNAP {'ON' if self._cfg.snap_enabled else 'OFF'}"
                else:
                    note = None
            else:
                note = None
            if note:
                self._toast.show_toast(str(note))
                if self._speaker:
                    self._speaker.say(str(note))

    def _process_autotune(self, now):
        if self._tuner:
            note = self._tuner.maybe_apply(time.monotonic(), self._filters, self._cfg)
            if note:
                self._toast.show_toast(note)
                self._smooth_name = "AUTO"

    def _update_fps(self):
        self._fps_counter += 1
        elapsed = time.perf_counter() - self._fps_time
        if elapsed >= 0.5:
            self._fps = self._fps_counter / elapsed
            self._fps_counter = 0
            self._fps_time = time.perf_counter()

    def _refresh_ui(self, all_frames, hand_frame):
        gesture = hand_frame.gesture if hand_frame else Gesture.NONE
        self._gesture_badge.update_gesture(gesture, self._paused)
        self._cam_view.update_frame(self._last_frame, all_frames, self._active_side, self._flash)

        ai_conf = hand_frame.ai_conf if hand_frame else 0.0
        hands = len(all_frames)
        magnify = self._magnifier.last_action if (self._magnifier and self._magnifier.on) else ""
        self._status.update_state(self._gesture_ai is not None, ai_conf, magnify, hands)

        if self._voice:
            self._voice_bar.update_state(self._voice.status, self._cfg.voice_wake_word)
        else:
            self._voice_bar.update_state("off")

        strip = f"{self._fps:4.0f} fps | ganho {self._cfg.move_gain:.1f} | {self._smooth_name}"
        if self._tuner and self._tuner.enabled:
            strip += " | AT"
        if self._speaker:
            strip += f" | voz:{self._speaker.status}"
        self._status_bar.setText(strip)
        self._fps_lbl.setText(f"{self._fps:4.0f} fps")

    @staticmethod
    def _key_combo(combo):
        try:
            from pynput.keyboard import Controller, Key
            kb = Controller()
            key_map = {
                "ctrl": Key.ctrl_l, "alt": Key.alt_l, "shift": Key.shift_l,
                "cmd": Key.cmd, "tab": Key.tab,
            }
            parts = combo.lower().split("+")
            keys = [key_map.get(p.strip(), p.strip()) for p in parts]
            for k in keys:
                kb.press(k)
            for k in reversed(keys):
                kb.release(k)
        except Exception:
            pass

    @staticmethod
    def _handle_media(event, value):
        VOLUME_STEP = 8.0
        try:
            from pynput.keyboard import Controller, Key
            kb = Controller()
        except Exception:
            return None
        if event == "volume":
            presses = int(abs(value) / VOLUME_STEP)
            if presses >= 1:
                key = Key.media_volume_up if value > 0 else Key.media_volume_down
                for _ in range(min(presses, 8)):
                    kb.press(key)
                    kb.release(key)
                return "VOL " + ("+" * min(presses, 4) if value > 0 else "-" * min(presses, 4))
        elif event == "play_pause":
            kb.press(Key.media_play_pause)
            kb.release(Key.media_play_pause)
            return "PLAY/PAUSA"
        return None

    def _save_settings(self):
        import json
        import os
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({
                    "move_gain": round(self._cfg.move_gain, 2),
                    "suavidade": self._smooth_name,
                    "filter_min_cutoff": round(self._cfg.filter_min_cutoff, 3),
                    "filter_beta": round(self._cfg.filter_beta, 4),
                    "snap_enabled": bool(self._cfg.snap_enabled),
                }, fh, indent=2)
        except Exception as exc:
            print(f"ERRO ao gravar: {exc}")

    def closeEvent(self, event):
        self._timer.stop()
        self._emitter.stop()
        if self._button_down:
            self._mouse.release_left()
        if self._snap:
            self._snap.stop()
        if self._voice:
            self._voice.stop()
        if self._speaker:
            self._speaker.stop()
        self._tracker.close()
        self._cam.release()
        cv2.destroyAllWindows()
        event.accept()
