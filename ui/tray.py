"""QSystemTrayIcon integration."""
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


class SystemTray(QSystemTrayIcon):

    pause_toggled = Signal()
    voice_toggled = Signal()
    snap_toggled = Signal()
    gain_up = Signal()
    gain_down = Signal()
    open_settings = Signal()
    quit_requested = Signal()

    def __init__(self, icon_path=None, parent=None):
        super().__init__(parent)
        if icon_path:
            self.setIcon(QIcon(icon_path))
        self.setToolTip("Mãouse")
        self._build_menu()

    def _build_menu(self):
        menu = QMenu()
        self._pause_act = QAction("Pausar", self)
        self._pause_act.triggered.connect(self.pause_toggled.emit)
        menu.addAction(self._pause_act)
        menu.addSeparator()
        menu.addAction(QAction("Ganho +", self, triggered=self.gain_up.emit))
        menu.addAction(QAction("Ganho -", self, triggered=self.gain_down.emit))
        menu.addSeparator()
        self._voice_act = QAction("Voz: off", self)
        self._voice_act.triggered.connect(self.voice_toggled.emit)
        menu.addAction(self._voice_act)
        self._snap_act = QAction("Snap: off", self)
        self._snap_act.triggered.connect(self.snap_toggled.emit)
        menu.addAction(self._snap_act)
        menu.addSeparator()
        menu.addAction(QAction("Definicoes...", self, triggered=self.open_settings.emit))
        menu.addSeparator()
        menu.addAction(QAction("Sair", self, triggered=self.quit_requested.emit))
        self.setContextMenu(menu)

    def update_state(self, paused, voice_status, snap_status, gain):
        self._pause_act.setText("Retomar" if paused else "Pausar")
        self._voice_act.setText(f"Voz: {voice_status}")
        self._snap_act.setText(f"Snap: {snap_status}")
