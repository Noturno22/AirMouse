"""Top-left gesture status badge."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from ui.theme import TEXT_SECONDARY, FONT_BADGE, gesture_color, gesture_label


class GestureBadge(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GestureBadge")
        self.setFont(FONT_BADGE)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(52)
        self.setMinimumWidth(180)
        self._apply(TEXT_SECONDARY, "SEM MAO")

    def update_gesture(self, gesture, paused=False):
        if paused:
            self._apply(TEXT_SECONDARY, "PAUSA")
        else:
            self._apply(gesture_color(gesture), gesture_label(gesture))

    def _apply(self, color, text):
        self.setText(text)
        self.setStyleSheet(
            f"background-color: rgba(10,10,18,204);"
            f"border: 2px solid {color.name()};"
            f"border-radius: 6px;"
            f"color: {color.name()};"
            f"font-family: 'Consolas'; font-size: 22px; font-weight: bold;"
            f"padding: 8px 16px;"
        )
