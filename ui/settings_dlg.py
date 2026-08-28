"""Settings dialog for real-time parameter adjustment."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QCheckBox, QComboBox, QPushButton, QGroupBox,
)

from ui.theme import MAIN_STYLESHEET, FONT_PRIMARY, FONT_MONO

SMOOTH_PRESETS = [
    ("SUAVE", 0.9, 0.02),
    ("NORMAL", 1.4, 0.028),
    ("REACTIVO", 2.2, 0.05),
]


class SettingsDialog(QDialog):

    def __init__(self, cfg, smooth_name, parent=None):
        super().__init__(parent)
        self._cfg = cfg
        self._smooth_name = smooth_name
        self.setWindowTitle("Definições — AirMouse")
        self.setObjectName("SettingsDialog")
        self.setFixedSize(430, 620)
        self.setStyleSheet(MAIN_STYLESHEET)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(16, 16, 16, 16)

        # Gain
        g = QGroupBox("Ganho do Cursor")
        g.setFont(FONT_PRIMARY)
        gl = QVBoxLayout()
        self._gain_lbl = QLabel(f"{self._cfg.move_gain:.1f}")
        self._gain_lbl.setFont(FONT_MONO)
        self._gain_sl = QSlider(Qt.Horizontal)
        self._gain_sl.setRange(6, 50)
        self._gain_sl.setValue(int(self._cfg.move_gain * 10))
        self._gain_sl.valueChanged.connect(lambda v: self._gain_lbl.setText(f"{v / 10:.1f}"))
        gl.addWidget(self._gain_lbl)
        gl.addWidget(self._gain_sl)
        g.setLayout(gl)
        lay.addWidget(g)

        # Smoothness
        s = QGroupBox("Suavidade")
        s.setFont(FONT_PRIMARY)
        sl = QVBoxLayout()
        self._smooth_cb = QComboBox()
        for name, _, _ in SMOOTH_PRESETS:
            self._smooth_cb.addItem(name)
        idx = next((i for i, (n, _, _) in enumerate(SMOOTH_PRESETS) if n == self._smooth_name), 1)
        self._smooth_cb.setCurrentIndex(idx)
        sl.addWidget(self._smooth_cb)
        s.setLayout(sl)
        lay.addWidget(s)

        # Toggles
        t = QGroupBox("Funcionalidades")
        t.setFont(FONT_PRIMARY)
        tl = QVBoxLayout()
        self._snap_ch = QCheckBox("Snap magnético")
        self._snap_ch.setChecked(self._cfg.snap_enabled)
        tl.addWidget(self._snap_ch)
        self._voice_ch = QCheckBox("Comandos de voz")
        self._voice_ch.setChecked(self._cfg.voice_enabled)
        tl.addWidget(self._voice_ch)
        self._tts_ch = QCheckBox("Voz falada (TTS)")
        self._tts_ch.setChecked(self._cfg.tts_enabled)
        tl.addWidget(self._tts_ch)
        self._ai_ch = QCheckBox("IA de gestos")
        self._ai_ch.setChecked(self._cfg.ai_enabled)
        tl.addWidget(self._ai_ch)
        self._at_ch = QCheckBox("Auto-afinação")
        self._at_ch.setChecked(self._cfg.autotune_enabled)
        tl.addWidget(self._at_ch)
        t.setLayout(tl)
        lay.addWidget(t)

        # Personalizacao
        p = QGroupBox("Personalizacao")
        p.setFont(FONT_PRIMARY)
        pl = QVBoxLayout()
        self._mirror_ch = QCheckBox("Espelhar imagem")
        self._mirror_ch.setChecked(self._cfg.mirror)
        pl.addWidget(self._mirror_ch)
        self._left_hand_ch = QCheckBox("Comandos mão esquerda")
        self._left_hand_ch.setChecked(self._cfg.left_hand_commands)
        pl.addWidget(self._left_hand_ch)
        self._lowlight_ch = QCheckBox("Realce em pouca luz")
        self._lowlight_ch.setChecked(self._cfg.low_light_boost)
        pl.addWidget(self._lowlight_ch)

        dl = QVBoxLayout()
        self._dead_lbl = QLabel(f"Zona morta do cursor: {self._cfg.deadzone_px:.0f}px")
        self._dead_lbl.setFont(FONT_MONO)
        self._dead_sl = QSlider(Qt.Horizontal)
        self._dead_sl.setRange(0, 20)
        self._dead_sl.setValue(int(self._cfg.deadzone_px))
        self._dead_sl.valueChanged.connect(
            lambda v: self._dead_lbl.setText(f"Zona morta do cursor: {v}px")
        )
        dl.addWidget(self._dead_lbl)
        dl.addWidget(self._dead_sl)
        pl.addLayout(dl)

        sl = QVBoxLayout()
        self._stable_lbl = QLabel(f"Estabilidade do gesto: {self._cfg.gesture_stable_frames} frames")
        self._stable_lbl.setFont(FONT_MONO)
        self._stable_sl = QSlider(Qt.Horizontal)
        self._stable_sl.setRange(1, 6)
        self._stable_sl.setValue(int(self._cfg.gesture_stable_frames))
        self._stable_sl.valueChanged.connect(
            lambda v: self._stable_lbl.setText(f"Estabilidade do gesto: {v} frames")
        )
        sl.addWidget(self._stable_lbl)
        sl.addWidget(self._stable_sl)
        pl.addLayout(sl)
        p.setLayout(pl)
        lay.addWidget(p)

        lay.addStretch()

        bl = QHBoxLayout()
        bl.addStretch()
        cancel = QPushButton("Cancelar")
        cancel.setObjectName("SettingsButton")
        cancel.clicked.connect(self.reject)
        bl.addWidget(cancel)
        save = QPushButton("Gravar")
        save.setObjectName("SettingsButton")
        save.clicked.connect(self._save)
        bl.addWidget(save)
        lay.addLayout(bl)

    def _save(self):
        self._cfg.move_gain = max(0.6, self._gain_sl.value() / 10.0)
        name = self._smooth_cb.currentText()
        for pname, cut, beta in SMOOTH_PRESETS:
            if pname == name:
                self._cfg.filter_min_cutoff = cut
                self._cfg.filter_beta = beta
                self._smooth_name = name
                break
        self._cfg.snap_enabled = self._snap_ch.isChecked()
        self._cfg.voice_enabled = self._voice_ch.isChecked()
        self._cfg.tts_enabled = self._tts_ch.isChecked()
        self._cfg.ai_enabled = self._ai_ch.isChecked()
        self._cfg.autotune_enabled = self._at_ch.isChecked()
        self._cfg.mirror = self._mirror_ch.isChecked()
        self._cfg.left_hand_commands = self._left_hand_ch.isChecked()
        self._cfg.low_light_boost = self._lowlight_ch.isChecked()
        self._cfg.deadzone_px = float(self._dead_sl.value())
        self._cfg.gesture_stable_frames = self._stable_sl.value()
        self.accept()

    @property
    def smooth_name(self):
        return self._smooth_name
