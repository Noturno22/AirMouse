"""Side menu panel: brand header + grouped action buttons."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)

from ui.brand import BrandHeader
from ui.theme import FONT_HELP


class MenuPanel(QWidget):
    """Painel lateral com logo e botões agrupados (topo-direito)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MenuPanel")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(0)

        self.brand = BrandHeader(self)
        self.brand.setFixedHeight(58)
        root.addWidget(self.brand)
        root.addSpacing(2)

        self._section1 = self._make_section("CONTROLO")
        root.addWidget(self._section1)
        root.addSpacing(6)

        self.btn_pause = self._make_button("⏸  PAUSA", checkable=False)
        self.btn_save = self._make_button("💾  GRAVAR")
        self.btn_voice = self._make_button("🎤  VOZ", checkable=True)
        self.btn_snap = self._make_button("🖼  SNAP", checkable=True)
        for btn in (self.btn_pause, self.btn_save, self.btn_voice, self.btn_snap):
            root.addWidget(btn)
            root.addSpacing(6)

        root.addWidget(self._make_divider())
        root.addSpacing(6)

        self._section2 = self._make_section("SISTEMA")
        root.addWidget(self._section2)
        root.addSpacing(6)

        self.btn_camera = self._make_button("📷  VER CÂMERA", checkable=True)
        self.btn_help = self._make_button("❓  AJUDA", checkable=True)
        self.btn_config = self._make_button("⚙  CONFIG")
        self.btn_quit = self._make_button("✕  SAIR")
        for btn in (self.btn_camera, self.btn_help, self.btn_config, self.btn_quit):
            root.addWidget(btn)
            root.addSpacing(6)

        root.addStretch(1)

    @staticmethod
    def _make_section(text):
        lbl = QLabel(text)
        lbl.setObjectName("MenuSection")
        lbl.setFont(FONT_HELP)
        return lbl

    @staticmethod
    def _make_button(text, checkable=False):
        btn = QPushButton(text)
        btn.setObjectName("MenuBtn")
        btn.setFixedHeight(32)
        btn.setCheckable(checkable)
        return btn

    @staticmethod
    def _make_divider():
        bar = QFrame()
        bar.setObjectName("MenuDivider")
        bar.setFixedHeight(1)
        return bar
