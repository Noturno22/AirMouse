"""Centered timed toast notification."""
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation
from PySide6.QtWidgets import QLabel

from ui.theme import FONT_MONO_BOLD


class Toast(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setFont(FONT_MONO_BOLD)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(44)
        self.setMinimumWidth(200)
        self.hide()

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)

        self._fade = QPropertyAnimation(self, b"windowOpacity")
        self._fade.setDuration(200)
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self.hide)

    def show_toast(self, text, duration_ms=1300):
        self.setText(text)
        self.setWindowOpacity(1.0)
        if self.parent():
            pw = self.parent().width()
            self.setFixedWidth(min(max(len(text) * 12 + 48, 200), pw - 40))
            x = (pw - self.width()) // 2
            self.move(x, max(self.y(), 50))
        self.show()
        self.raise_()
        self._timer.start(duration_ms)

    def _fade_out(self):
        self._fade.setStartValue(1.0)
        self._fade.start()
