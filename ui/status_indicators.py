"""Top-right stacked status badges: AI confidence, magnifier, hand count."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ui.theme import FONT_MONO, SUCCESS, TEXT_PRIMARY


class StatusBadges(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addStretch()

        self._ai = self._badge()
        self._mag = self._badge()
        self._hands = self._badge()
        layout.addWidget(self._ai)
        layout.addWidget(self._mag)
        layout.addWidget(self._hands)
        self._mag.hide()
        self._hands.hide()

    def _badge(self):
        lbl = QLabel()
        lbl.setObjectName("StatusBadge")
        lbl.setFont(FONT_MONO)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedHeight(28)
        lbl.setMinimumWidth(60)
        lbl._last = ("", "")
        return lbl

    def _style(self, lbl, text, color_name):
        # Evita `setStyleSheet`/`setText` em todos os frames quando nada mudou.
        if (text, color_name) == lbl._last:
            return
        lbl._last = (text, color_name)
        lbl.setText(text)
        lbl.setStyleSheet(
            f"background-color: rgba(10,10,18,204);"
            f"border: 1px solid {color_name}; border-radius: 4px;"
            f"color: {color_name}; padding: 4px 10px;"
        )

    def update_state(self, ai_on, ai_conf, magnify, hands):
        if ai_on:
            self._ai.show()
            txt = f"IA {int(ai_conf * 100):3d}%" if hands > 0 else "IA  ok"
            col = SUCCESS.name() if ai_conf >= 0.72 else TEXT_PRIMARY.name()
            self._style(self._ai, txt, col)
        else:
            self._ai.hide()

        if magnify:
            self._mag.show()
            self._style(self._mag, f"LUPA {magnify}", "#FF50C8")
        else:
            self._mag.hide()

        if hands > 0:
            self._hands.show()
            self._style(self._hands, f"{hands} MÃOS", TEXT_PRIMARY.name())
        else:
            self._hands.hide()
