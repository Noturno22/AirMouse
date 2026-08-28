"""Toggleable help overlay panel (cartão com seções agrupadas)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QFrame

from ui.theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, ACCENT,
    FONT_HELP, FONT_PRIMARY, FONT_PRIMARY_BOLD,
    gesture_color,
)

# Fundo sólido (opaco) para o painel de ajuda — sempre legível, mesmo quando
# sobreposto ao feed da câmara ou ao dashboard, sem os "buracos" transparentes
# que deixavam o texto a flutuar sobre o conteúdo por trás.
HELP_BG = "#0A0A12"
HELP_BG_SOLID = "#16162A"
from core.gestures import Gesture


def _dot(gesture):
    color = gesture_color(gesture)
    return (
        f'<span style="color:{color.name()};font-size:14px;">&#9679;</span>'
    )


SECTIONS = [
    ("MOVER & CLIQUE", [
        (_dot(Gesture.OPEN), "mão aberta / 1 dedo", "mover cursor"),
        (_dot(Gesture.PINCH), "pinça (indicador)", "clique esq · manter = arrastar"),
        (_dot(Gesture.PINCH_MID), "pinça (médio)", "clique direito"),
    ]),
    ("SCROLL & VOLUME", [
        (_dot(Gesture.FIST), "punho + cima/baixo", "scroll"),
        (_dot(Gesture.THREE), "três dedos + cima/baixo", "volume"),
    ]),
    ("BRILHO (2 MÃOS)", [
        (_dot(Gesture.PEACE), "dois dedos · mão esq", "diminuir brilho"),
        (_dot(Gesture.PEACE), "dois dedos · mão dir", "aumentar brilho"),
    ]),
    ("MULTIMÉDIA & SISTEMA", [
        (_dot(Gesture.THUMB_UP), "polegar cima", "play / pausa"),
        (_dot(Gesture.PINKY), "mindinho", "copiar (Ctrl+C)"),
        (_dot(Gesture.SHAKA), "polegar + mindinho", "colar (Ctrl+V)"),
        ("", "punho duplo ×2", "Win+D"),
        ("", "bye bye (onda)", "minimizar (Win+↓)"),
        ("", "2 mãos abertas + afastar", "lupa (zoom)"),
    ]),
    ("INTERFACE", [
        ("", "swipe ← · mão esq", "abrir interface"),
        ("", "swipe → · mão esq", "fechar interface"),
    ]),
]


class HelpPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HelpPanel")
        self.setFixedWidth(360)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            f"HelpPanel {{ background-color: {HELP_BG_SOLID};"
            f" border: 1px solid #969696; border-radius: 8px; }}"
        )
        self.hide()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Cabeçalho
        title = QLabel("AJUDA")
        title.setObjectName("HelpTitle")
        title.setFont(FONT_PRIMARY_BOLD)
        subtitle = QLabel("GESTOS & ATALHOS")
        subtitle.setObjectName("HelpSubtitle")
        outer.addWidget(title)
        outer.addWidget(subtitle)
        outer.addSpacing(8)

        # Corpo com scroll
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea {{ background: transparent; border: none; }}"
            f"QScrollArea > QWidget > QWidget {{ background: {HELP_BG_SOLID}; }}"
            f"QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}"
            f"QScrollBar::handle:vertical {{ background: #3A3A5A; border-radius: 4px; min-height: 24px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}"
        )
        body = QWidget()
        body.setObjectName("HelpPanelBody")
        body.setStyleSheet(f"background-color: {HELP_BG_SOLID};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(10, 6, 8, 10)
        body_layout.setSpacing(2)

        for title_text, rows in SECTIONS:
            sec = QLabel(title_text)
            sec.setObjectName("HelpSection")
            sec.setFont(FONT_PRIMARY)
            body_layout.addWidget(sec)
            body_layout.addSpacing(2)
            for dot, gesture, action in rows:
                row = QLabel(f"{dot} {gesture}  ·  <b>{action}</b>")
                row.setObjectName("HelpRow")
                row.setWordWrap(True)
                row.setTextFormat(Qt.RichText)
                body_layout.addWidget(row)
            body_layout.addSpacing(8)

        # Secção de atalhos de teclado
        kb_sec = QLabel("ATALHOS TECLADO")
        kb_sec.setObjectName("HelpSection")
        kb_sec.setFont(FONT_PRIMARY)
        body_layout.addWidget(kb_sec)
        body_layout.addSpacing(2)
        for combo, action in (
            ("[ / ]", "ganho −/+"),
            (", / .", "suavidade"),
            ("M", "snap ON/OFF"),
            ("C", "ver câmara (config)"),
            ("A", "auto-afinação"),
            ("V", "voz"),
            ("S", "gravar"),
            ("espaço", "pausar"),
            ("Q", "sair"),
            ("F1", "mostrar/ocultar ajuda"),
        ):
            row = QLabel(f"<span style='color:{ACCENT.name()};'>{combo}</span>   {action}")
            row.setObjectName("HelpRow")
            body_layout.addWidget(row)

        # Voz
        body_layout.addSpacing(8)
        voice_sec = QLabel("VOZ")
        voice_sec.setObjectName("HelpSection")
        voice_sec.setFont(FONT_PRIMARY)
        body_layout.addWidget(voice_sec)
        voice_row = QLabel("jarvis &lt;comando natural&gt;")
        voice_row.setObjectName("HelpRow")
        body_layout.addWidget(voice_row)

        body_layout.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self._fit()
            self.show()
            self.raise_()

    def _fit(self):
        if self.parent():
            ph = self.parent().height()
            self.setFixedHeight(min(ph - 40, 560))
            self.move(12, int(ph * 0.15))
