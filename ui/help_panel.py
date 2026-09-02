"""Toggleable help overlay panel (cartão moderno com seções agrupadas e i18n)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from i18n import I18N, tr
from ui.icon_kits import menu_icon
from ui.theme import (
    ACCENT,
    FONT_PRIMARY,
    FONT_PRIMARY_BOLD,
    gesture_color,
)

# Fundo sólido (opaco) para o painel de ajuda — sempre legível, mesmo quando
# sobreposto ao feed da câmara ou ao dashboard.
HELP_BG_SOLID = "#0C0C18"
HELP_BORDER = "#2A2A45"


def _dot(gesture):
    color = gesture_color(gesture)
    return (
        f'<span style="color:{color.name()};font-size:13px;">&#9679;</span>'
    )


def _icon(name, size):
    return menu_icon(name, size=size)


def _val(key):
    return tr(key)


# Cada secção: (chave_título_i18n, [ (gesture|None, chave_gesto, chave_ação) ])
# O gesto None significa que não há bolinha colorida associada.
SECTIONS = [
    ("help.sec.move", [
        (None, "help.g.move", "help.g.one"),
        (None, "help.g.click", ""),
        (None, "help.g.mid", "help.g.right"),
    ]),
    ("help.sec.scroll", [
        (None, "help.g.scroll", "help.g.scroll_act"),
        (None, "help.g.vol", "help.g.vol_act"),
    ]),
    ("help.sec.bright", [
        (None, "help.g.peace_l", "help.g.dim"),
        (None, "help.g.peace_r", "help.g.raise"),
    ]),
    ("help.sec.media", [
        (None, "help.g.thumb", "help.g.play"),
        (None, "help.g.pinky", "help.g.copy"),
        (None, "help.g.shaka", "help.g.paste"),
        (None, "help.g.2fist", "help.g.wind"),
        (None, "help.g.bye", "help.g.min"),
        (None, "help.g.zoomm", "help.g.zoom"),
    ]),
    ("help.sec.window", [
        (None, "help.g.swipe", "help.g.nextwin"),
        (None, "help.g.swipel", "help.g.prevwin"),
        (None, "help.g.hold", "help.g.switch"),
        (None, "help.g.peace_toggle", "help.g.ui_toggle"),
    ]),
]

KB_SHORTCUTS = [
    ("[ / ]", "help.kb.gain"),
    (", / .", "help.kb.smooth"),
    ("M", "help.kb.snap"),
    ("C", "help.kb.cam"),
    ("A", "help.kb.auto"),
    ("V", "help.kb.voice"),
    ("S", "help.kb.save"),
    ("espaço", "help.kb.pause"),
    ("Q", "help.kb.quit"),
    ("F1", "help.kb.help"),
]


class HelpPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HelpPanel")
        self.setFixedWidth(340)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.hide()

        # Cabeçalho fixo fora do scroll (sempre visível).
        header = QWidget(self)
        header.setObjectName("HelpPanelHeader")
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(14, 12, 12, 10)
        hlay.setSpacing(10)

        self._icon_lbl = QLabel()
        self._icon_lbl.setPixmap(_icon("menu-help", 22).pixmap(22, 22))
        hlay.addWidget(self._icon_lbl)

        txt = QVBoxLayout()
        txt.setSpacing(1)
        self._title = QLabel(tr("help.title"))
        self._title.setObjectName("HelpTitle")
        self._title.setFont(FONT_PRIMARY_BOLD)
        self._subtitle = QLabel(tr("help.subtitle"))
        self._subtitle.setObjectName("HelpSubtitle")
        txt.addWidget(self._title)
        txt.addWidget(self._subtitle)
        hlay.addLayout(txt)
        hlay.addStretch()
        self._header = header

        # Corpo com scroll.
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background: transparent; border: none; }}"
            f"QScrollArea > QWidget > QWidget {{ background: {HELP_BG_SOLID}; }}"
            f"QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}"
            f"QScrollBar::handle:vertical {{ background: #3A3A5A; border-radius: 4px; min-height: 24px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}"
        )

        self._body = None
        self._build_body()

        # Layout externo.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header)
        outer.addWidget(self._scroll, 1)

        I18N.language_changed.connect(lambda *_: self._build_body())

    # ── Conteúdo ──────────────────────────────────────────────────────
    def _build_body(self):
        # Remove o corpo anterior (se existir) e reconstrói com o idioma atual.
        if self._body is not None:
            self._scroll.takeWidget()
            self._body.deleteLater()
        body = QWidget()
        body.setObjectName("HelpPanelBody")
        self._body = body
        lay = QVBoxLayout(body)
        lay.setContentsMargins(12, 8, 10, 12)
        lay.setSpacing(0)

        # Cabeçalho.
        self._title.setText(tr("help.title"))
        self._subtitle.setText(tr("help.subtitle"))

        for sec_key, rows in SECTIONS:
            sec = QLabel(tr(sec_key))
            sec.setObjectName("HelpSection")
            sec.setFont(FONT_PRIMARY)
            lay.addWidget(sec)
            lay.addSpacing(3)
            for gesture, gk, ak in rows:
                dot = _dot(gesture) if gesture is not None else (
                    '<span style="color:#3A3A5A;font-size:12px;">&#8226;</span>'
                )
                gesto = _val(gk)
                acao = _val(ak) if ak else ""
                if acao:
                    row = QLabel(f"{dot} {gesto}  ·  <b>{acao}</b>")
                else:
                    row = QLabel(f"{dot} {gesto}")
                row.setObjectName("HelpRow")
                row.setWordWrap(True)
                row.setTextFormat(Qt.RichText)
                lay.addWidget(row)
                lay.addSpacing(2)
            lay.addSpacing(8)

        # Atalhos de teclado.
        kb_sec = QLabel(tr("help.sec.kb"))
        kb_sec.setObjectName("HelpSection")
        kb_sec.setFont(FONT_PRIMARY)
        lay.addWidget(kb_sec)
        lay.addSpacing(3)
        for combo, ak in KB_SHORTCUTS:
            row = QLabel(
                f'<span style="color:{ACCENT.name()};font-family:\'Consolas\';font-weight:bold;">{combo}</span>'
                f'   {_val(ak)}'
            )
            row.setObjectName("HelpRow")
            row.setTextFormat(Qt.RichText)
            lay.addWidget(row)
            lay.addSpacing(2)

        # Voz.
        lay.addSpacing(8)
        voice_sec = QLabel(tr("help.sec.voice"))
        voice_sec.setObjectName("HelpSection")
        voice_sec.setFont(FONT_PRIMARY)
        lay.addWidget(voice_sec)
        lay.addSpacing(3)
        voice_row = QLabel(tr("help.voice_tip"))
        voice_row.setObjectName("HelpRow")
        voice_row.setTextFormat(Qt.RichText)
        lay.addWidget(voice_row)

        lay.addStretch(1)
        self._scroll.setWidget(body)

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
