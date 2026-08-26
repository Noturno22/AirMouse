"""Toggleable help overlay panel."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from ui.theme import TEXT_PRIMARY, FONT_HELP


HELP_LINES = [
    "AJUDA",
    "",
    "mao aberta / 1 dedo ... mover cursor",
    "pinca index ............ botao esquerdo (manter=arrastar)",
    "punho .................. arrastar",
    "pinca medio ............ clique direito",
    "dois dedos ............. scroll",
    "tres dedos + cima/baixo = volume",
    "polegar cima ........... play/pausa multimedia",
    "dedo mindinho .......... copiar (Ctrl+C)",
    "polegar + mindinho ..... colar (Ctrl+V)",
    "punho esq (2 maos) .... diminuir brilho",
    "punho dir (2 maos) .... aumentar brilho",
    "fechar/abrir punho x2 .. Win+D",
    "bye bye (onda) ......... minimizar janela (Win+Down)",
    "ondas 2 maos ........... Alt+Tab",
    "PALMAS (x3) ........... Alt+Tab",
    "2 maos abertas + afastar = lupa (zoom)",
    "",
    "[ / ] ................. ganho -/+",
    ", / . ................. suavidade",
    "m ..................... snap magnetico ON/OFF",
    "a ............. auto-afinacao | v voz | s gravar",
    "espaco ................ pausar | Q sair",
    "F1 .................... mostrar/ocultar ajuda",
    "",
    "voz: jarvis <comando natural>",
]


class HelpPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HelpPanel")
        self.hide()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        self._label = QLabel("\n".join(HELP_LINES))
        self._label.setFont(FONT_HELP)
        self._label.setStyleSheet(f"color: {TEXT_PRIMARY.name()};")
        self._label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self._label)

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self._fit()
            self.show()
            self.raise_()

    def _fit(self):
        if self.parent():
            pw = self.parent().width()
            ph = self.parent().height()
            self.setFixedSize(min(430, pw - 40), min(len(HELP_LINES) * 20 + 30, ph - 40))
            self.move(12, int(ph * 0.25))
