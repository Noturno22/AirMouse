"""Voice status indicator."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel

from ui.theme import TEXT_SECONDARY, FONT_MONO


class VoiceBar(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VoiceIndicator")
        self.setFont(FONT_MONO)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(28)
        self.setMinimumWidth(140)
        self.hide()

    def update_state(self, voice_status, wake_word="jarvis"):
        if voice_status == "off":
            self.hide()
            return
        self.show()
        labels = {
            "on": "VOZ ON",
            "listening": "VOZ <OUVINDO>",
            "wake": f"VOZ {wake_word.upper()}",
        }
        txt = labels.get(voice_status, f"VOZ {voice_status.upper()}")
        colors = {
            "on": QColor(255, 80, 200),
            "listening": QColor(255, 80, 200),
            "wake": TEXT_SECONDARY,
        }
        color = colors.get(voice_status, TEXT_SECONDARY)
        self.setText(txt)
        self.setStyleSheet(
            f"background-color: rgba(10,10,18,204);"
            f"border: 1px solid {color.name()}; border-radius: 4px;"
            f"color: {color.name()}; padding: 4px 10px;"
        )
