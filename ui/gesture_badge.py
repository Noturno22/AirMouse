"""Top-left gesture status badge."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from ui.theme import FONT_BADGE, TEXT_SECONDARY, gesture_color, gesture_label


class GestureBadge(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GestureBadge")
        self.setFont(FONT_BADGE)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(52)
        self.setMinimumWidth(180)
        self._last_color = None
        self._last_text = None
        self._apply(TEXT_SECONDARY, "SEM MÃO")

    def update_gesture(self, gesture, paused=False):
        if paused:
            self._apply(TEXT_SECONDARY, "PAUSA")
        else:
            self._apply(gesture_color(gesture), gesture_label(gesture))

    def _apply(self, color, text):
        # Evita `setStyleSheet`/`setText` em todos os frames quando nada mudou.
        # `setStyleSheet` re-pols a widget e é uma fonte de stutter no feed.
        color_name = color.name()
        if text == self._last_text and color_name == self._last_color:
            return
        self._last_text = text
        self._last_color = color_name
        self.setText(text)
        self.setStyleSheet(
            f"background-color: rgba(0,0,0,204);"
            f"border: 2px solid {color.name()};"
            f"border-radius: 6px;"
            f"color: {color.name()};"
            f"font-family: 'Consolas'; font-size: 22px; font-weight: bold;"
            f"padding: 8px 16px;"
        )
