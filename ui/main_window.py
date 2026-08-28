"""Main frameless window with QTimer processing loop.

A MainWindow é apenas a APRESENTAÇÃO: toda a lógica de reconhecimento/
movimento/gestos vive em ``process_frame``/``make_engine_ctx`` (main.py),
partilhada com o preview OpenCV. Isto garante paridade total de comportamento
entre as duas UIs.
"""
import json
import os
import time

import cv2

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QMainWindow, QWidget, QLabel, QHBoxLayout

from config import Config
from ui.theme import (
    MAIN_STYLESHEET, TEXT_PRIMARY, FONT_MONO, FONT_STATUS,
    init_gesture_colors, gesture_color, gesture_label,
)
from ui.camera_view import CameraView
from ui.gesture_badge import GestureBadge
from ui.status_indicators import StatusBadges
from ui.voice_bar import VoiceBar
from ui.toast import Toast
from ui.help_panel import HelpPanel
from ui.menu_panel import MenuPanel

from core.gestures import Gesture


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

        self._paused = False
        self._show_help = False
        self._smooth_name = "NORMAL"
        self._ui_show = False
        self._flash = 0
        self._last_frame = None
        self._all_frames = {}
        self._active_side = None
        self._fps = 0.0
        self._fps_counter = 0
        self._fps_time = time.perf_counter()

        # A câmara é o conteúdo principal da janela (semelhante ao preview original):
        # aparece de imediato; o rastreio de gestos corre sempre em segundo plano.
        self._camera_on = True

        self._E = None
        self._ctx = None
        self._state = {}

        self._build_ui()
        self._build_shortcuts()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(0)

    def _build_ui(self):
        self.setWindowTitle("AirMouse")
        self.setObjectName("MainWindow")
        self.setMinimumSize(640, 480)
        self.resize(800, 600)
        self.setStyleSheet(MAIN_STYLESHEET)
        self.setWindowFlags(Qt.FramelessWindowHint)

        central = QWidget()
        central.setObjectName("MainWindow")
        self.setCentralWidget(central)

        # Painel de marca central (dashboard). O feed da câmara não é o fundo:
        # a janela é um painel de controlo limpo; a câmara é um preview opcional.
        self._brand = QLabel(central)
        self._brand.setObjectName("DashboardBrand")
        self._brand.setAlignment(Qt.AlignCenter)
        self._brand.setText(
            "<span style='font-size:44px;font-weight:bold;color:#50C8FF;'>MÃOUSE</span>"
            "<br><span style='font-size:16px;color:#969696;'>Controlo do rato por gestos</span>"
        )

        self._cam_view = CameraView(central)
        self._cam_view.setObjectName("CameraPreview")
        self._cam_view.show()
        self._brand.hide()

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

        self._menu = MenuPanel(central)
        self._menu.setFixedWidth(168)

        self._status_bar = QLabel(central)
        self._status_bar.setObjectName("StatusBar")
        self._status_bar.setFont(FONT_STATUS)
        self._status_bar.setFixedHeight(22)

        self._fps_lbl = QLabel(central)
        self._fps_lbl.setObjectName("StatusBar")
        self._fps_lbl.setFont(FONT_MONO)
        self._fps_lbl.setFixedHeight(22)
        self._fps_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._build_menu()
        self._build_shortcuts()

    def _build_menu(self):
        """Painel lateral de marca com botões agrupados (topo-direito)."""
        m = self._menu
        m.btn_pause.clicked.connect(self._toggle_pause)
        m.btn_save.clicked.connect(self._save_settings)
        m.btn_voice.toggled.connect(self._toggle_voice)
        m.btn_snap.toggled.connect(self._toggle_snap)
        m.btn_camera.toggled.connect(self._toggle_camera)
        m.btn_help.toggled.connect(self._toggle_help)
        m.btn_config.clicked.connect(self._open_settings)
        m.btn_quit.clicked.connect(self.close)
        if self._camera_on:
            m.btn_camera.setChecked(True)
        self._menu_buttons = [
            m.btn_pause, m.btn_save, m.btn_voice, m.btn_snap,
            m.btn_camera, m.btn_help, m.btn_config, m.btn_quit,
        ]

    def _build_shortcuts(self):
        pass

    def _menu_checkable(self, btn, checked):
        btn.setChecked(checked)

    def _toggle_pause(self):
        self._paused = not self._paused
        self._menu.btn_pause.setText("⏸  PAUSA" if not self._paused else "▶  RETOMAR")
        self._toast.show_toast("PAUSA" if self._paused else "RETOMAR")

    def _toggle_voice(self, checked):
        if self._voice:
            self._voice.toggle()
            self._toast.show_toast(f"VOZ {'ON' if checked else 'OFF'}")

    def _toggle_snap(self, checked):
        if self._snap and self._snap.available:
            self._cfg.snap_enabled = checked
            self._toast.show_toast(f"SNAP {'ON' if checked else 'OFF'}")

    def _toggle_help(self, checked):
        self._show_help = checked
        self._help.toggle()

    def _toggle_camera(self, checked):
        """Mostra/oculta o preview da câmara. O reconhecimento de gestos NÃO é
        afetado: o rastreio continua a correr em segundo plano o tempo todo."""
        self._camera_on = checked
        self._cam_view.setVisible(checked)
        self._brand.setVisible(not checked)
        self._layout_camera()
        self._toast.show_toast("CÂMARA ON" if checked else "CÂMARA OFF")

    def _sync_toolbar(self):
        self._menu.btn_pause.setText("⏸  PAUSA" if not self._paused else "▶  RETOMAR")
        self._menu_checkable(self._menu.btn_voice, bool(self._voice) and self._voice.status != "off")
        self._menu_checkable(self._menu.btn_snap, bool(self._cfg.snap_enabled))

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
        elif key == Qt.Key_C:
            new_state = not self._camera_on
            self._menu.btn_camera.setChecked(new_state)
            self._toggle_camera(new_state)
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
        if self._E is not None:
            self._E.filters.set_params(cut, beta)
        self._smooth_name = name
        self._toast.show_toast(name)

    def _open_settings(self):
        from ui.settings_dlg import SettingsDialog
        dlg = SettingsDialog(self._cfg, self._smooth_name, self)
        if dlg.exec() == SettingsDialog.Accepted:
            self._smooth_name = dlg.smooth_name
            if self._E is not None:
                self._E.filters.set_params(self._cfg.filter_min_cutoff, self._cfg.filter_beta)
            self._toast.show_toast("Definições atualizadas")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._brand.setGeometry(0, int(h * 0.32), w, int(h * 0.36))
        self._layout_camera()
        self._status.move(w - 310, 10)
        self._status.resize(300, 28)
        self._status_bar.setGeometry(0, h - 22, w, 22)
        self._fps_lbl.setGeometry(w - 100, h - 22, 90, 22)
        tw = self._toast.width() if self._toast.width() > 0 else 200
        self._toast.move((w - tw) // 2, 50)

        bw = self._menu.width()
        mw = self._menu.sizeHint() if hasattr(self._menu, "sizeHint") else None
        mh = self._menu.sizeHint().height()
        x = w - bw - 10
        y = 10
        self._menu.setGeometry(x, y, bw, mh)

    def _layout_camera(self):
        """Posiciona o preview da câmara como um painel centrado (não o fundo),
        mantendo a proporção e cachê sem esticar o vídeo."""
        w, h = self.width(), self.height()
        if not self._camera_on:
            return
        cfg = self._cfg
        fw, fh = cfg.frame_width, cfg.frame_height
        max_w = w - 40
        max_h = h - 90
        scale = min(max_w / max(fw, 1), max_h / max(fh, 1))
        sw = int(fw * scale)
        sh = int(fh * scale)
        x = (w - sw) // 2
        y = 40
        self._cam_view.setGeometry(x, y, sw, sh)
        self._cam_view.raise_()

    # ── Processing Loop ─────────────────────────────────────────────
    def _tick(self):
        from main import process_frame, make_engine_ctx
        from core.motion import SmoothEmitter

        if self._ctx is None:
            from main import AppCtl
            self._ctx = AppCtl()
        if self._E is None:
            self._E = make_engine_ctx(self._cfg, -1, self._gesture_ai, self._tuner, self._ctx)
            self._E.emitter = SmoothEmitter(self._mouse, self._cfg.emitter_rate_hz)
            self._E.emitter.start()
        self._state["smooth_name"] = self._smooth_name
        self._ctx.speaker = self._speaker
        self._ctx.snap = self._snap
        self._ctx.assistant = self._assistant
        self._ctx.magnifier = self._magnifier
        self._state.setdefault("paused", False)
        self._state.setdefault("show_help", False)
        self._state.setdefault("flash", 0)
        self._state.setdefault("freeze_until", 0.0)
        self._state.setdefault("button_down", False)
        self._state.setdefault("dbg_until", 0.0)
        self._state["filters"] = self._E.filters
        self._state["tuner"] = self._tuner
        self._state["emitter"] = self._E.emitter

        # O Ctrl+C (SIGINT) pode interromper o MediaPipe no meio de
        # `tracker.process`. Para sair de forma limpa (sem tracebacks
        # repetidos nem janela presa), fechamos a janela: o closeEvent para
        # o timer e o app termina quando a janela única fechar.
        try:
            snap = process_frame(
                self._cfg, self._cam, self._tracker, self._mouse,
                self._gesture_ai, self._voice, self._tuner, self._ctx,
                self._state, self._E,
            )
        except KeyboardInterrupt:
            self.close()
            return
        if snap["done"] or self._ctx.exit_requested:
            self.close()
            return
        if not snap.get("to_render") or snap["frame"] is None:
            if self._ctx.exit_requested:
                self.close()
            return
        self._flash = snap.get("flash", self._state.get("flash", 0))
        self._update_fps()
        self._refresh_ui(snap)

        # Gate por gesto: a janela so se mostra/oculta conforme o ROCK (chifre)
        # na mao de comandos seja feito. Arranca oculta (apenas configuracao).
        ui_show = bool(snap.get("ui", {}).get("ui_show", self._ui_show))
        if ui_show != self._ui_show:
            self._ui_show = ui_show
            if ui_show:
                self.show()
                self.raise_()
                self.activateWindow()
            else:
                self.hide()

    def _update_fps(self):
        self._fps_counter += 1
        elapsed = time.perf_counter() - self._fps_time
        if elapsed >= 0.5:
            self._fps = self._fps_counter / elapsed
            self._fps_counter = 0
            self._fps_time = time.perf_counter()
    def _refresh_ui(self, snap):
        frame = snap["frame"]
        all_frames = snap["all_frames"]
        active_side = snap["active_side"]
        self._last_frame = frame
        self._all_frames = all_frames
        self._active_side = active_side
        hand_frame = all_frames.get(active_side)

        self._sync_toolbar()

        gesture = hand_frame.gesture if hand_frame else Gesture.NONE
        self._gesture_badge.update_gesture(gesture, self._paused)
        if self._camera_on:
            self._cam_view.update_frame(frame, all_frames, active_side, self._flash)

        ai_conf = hand_frame.ai_conf if hand_frame else 0.0
        hands = len(all_frames)
        magnify = self._magnifier.last_action if (self._magnifier and self._magnifier.on) else ""
        self._status.update_state(self._gesture_ai is not None, ai_conf, magnify, hands)

        if self._voice:
            self._voice_bar.update_state(self._voice.status, self._cfg.voice_wake_word)
        else:
            self._voice_bar.update_state("off")

        ui = snap["ui"]
        if ui.get("toast") and time.monotonic() < ui.get("toast_until", 0):
            self._toast.show_toast(ui["toast"])
            ui["toast_until"] = 0

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
                    "mirror": bool(self._cfg.mirror),
                    "left_hand_commands": bool(self._cfg.left_hand_commands),
                    "low_light_boost": bool(self._cfg.low_light_boost),
                    "deadzone_px": round(self._cfg.deadzone_px, 1),
                    "gesture_stable_frames": int(self._cfg.gesture_stable_frames),
                    "voice_enabled": bool(self._cfg.voice_enabled),
                    "tts_enabled": bool(self._cfg.tts_enabled),
                    "ai_enabled": bool(self._cfg.ai_enabled),
                    "autotune_enabled": bool(self._cfg.autotune_enabled),
                }, fh, indent=2)
        except Exception as exc:
            print(f"ERRO ao gravar: {exc}")

    def closeEvent(self, event):
        self._timer.stop()
        try:
            if self._E is not None and self._E.emitter is not None:
                self._E.emitter.stop()
        except Exception:
            pass
        try:
            if self._state.get("button_down"):
                self._mouse.release_left()
        except Exception:
            pass
        for obj, meth in (
            (self._snap, "stop"), (self._voice, "stop"),
            (self._speaker, "stop"), (self._tracker, "close"),
            (self._cam, "release"),
        ):
            if obj is None or not hasattr(obj, meth):
                continue
            try:
                getattr(obj, meth)()
            except Exception:
                pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        event.accept()
