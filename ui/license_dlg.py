"""Upgrade / License dialog for Mãouse.

Mostra as opções Pro (Lifetime / Subscrição / Família) com os preços do
modelo de negócio, lança o checkout Paddle (Merchant of Record, decisão D2)
no browser e permite ativar/inserir uma chave Pro offline.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.licensing import Tier
from ui.theme import FONT_PRIMARY, MAIN_STYLESHEET

PADDLE_VENDOR_ID = 0  # TODO: preencher com o vendor_id real do Paddle (D2)

_PRODUCTS = [
    ("Lifetime", "€39,90 (uma vez)", "lifetime"),
    ("Subscrição", "€4,99/mês · €3,49/mês (anual)", "subscription"),
    ("Família", "€59,90 · 3 dispositivos", "family"),
    ("Desconto acessibilidade", "a partir de €19,95 · sob validação", "access"),
]


class LicenseDialog(QDialog):

    def __init__(self, cfg, license_mgr, parent=None):
        super().__init__(parent)
        self._cfg = cfg
        self._lm = license_mgr
        self.setWindowTitle("Mãouse Pro — Licença")
        self.setObjectName("SettingsDialog")
        self.setFixedSize(460, 460)
        self.setStyleSheet(MAIN_STYLESHEET)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(20, 20, 20, 20)

        # Estado atual
        estado = "✔ PRO ATIVO" if self._lm.is_pro else "MODO FREE"
        self._status_lbl = QLabel(estado)
        self._status_lbl.setFont(FONT_PRIMARY)
        self._status_lbl.setStyleSheet(
            "color:#50C8FF;" if not self._lm.is_pro else "color:#7DDB8A;"
        )
        self._status_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._status_lbl)

        if self._lm.is_pro:
            self._build_pro_ui(lay)
        else:
            self._build_free_ui(lay)

    def _build_free_ui(self, lay):
        txt = QLabel(
            "Desbloqueia no Pro:\n"
            "• Snap magnético (cursor \"gruda\" em botões)\n"
            "• Voz \"Jarvis\" + TTS neural\n"
            "• Duas mãos (lupa, brilho, gestos)\n"
            "• IA avançada + auto-afinação\n"
            "• Luz baixa, arranque automático, personalização"
        )
        txt.setWordWrap(True)
        txt.setStyleSheet("color:#F0F4F8;")
        lay.addWidget(txt)

        for name, price, product in _PRODUCTS:
            row = QHBoxLayout()
            lbl = QLabel(f"  {name}  —  {price}")
            lbl.setStyleSheet("color:#F0F4F8;")
            btn = QPushButton("Pagar / Checkout")
            btn.setObjectName("SettingsButton")
            btn.clicked.connect(lambda _=False, p=product: self._open_checkout(p))
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(btn)
            lay.addLayout(row)

        lay.addSpacing(8)

        self._key_edit = QLineEdit()
        self._key_edit.setPlaceholderText("Já tem uma chave Pro? Cole-a aqui")
        self._key_edit.setStyleSheet(
            "background:#12121E;color:#F0F4F8;border:1px solid #1A1A2E;"
            "border-radius:6px;padding:8px;font-family:Consolas;"
        )
        lay.addWidget(self._key_edit)

        activate = QPushButton("Ativar Chave")
        activate.setObjectName("SettingsButton")
        activate.clicked.connect(self._activate_key)
        lay.addWidget(activate)

    def _build_pro_ui(self, lay):
        txt = QLabel("A sua licença Mãouse Pro está ativa. 💎")
        txt.setAlignment(Qt.AlignCenter)
        txt.setStyleSheet("color:#7DDB8A;")
        lay.addWidget(txt)

        remover = QPushButton("Remover Licença (voltar a Free)")
        remover.setObjectName("SettingsButton")
        remover.clicked.connect(self._deactivate)
        lay.addWidget(remover)

    def _open_checkout(self, product):
        if not self._lm.open_checkout(product, PADDLE_VENDOR_ID):
            QMessageBox.warning(self, "Checkout",
                                "Não foi possível abrir o checkout no browser.")
        else:
            QMessageBox.information(
                self, "Checkout",
                "O checkout Paddle abriu no seu browser.\n"
                "Após a compra, cole a chave que receber no campo abaixo e clique em "
                "\"Ativar Chave\".",
            )

    def _activate_key(self):
        key = self._key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "Chave", "Cole a sua chave Pro primeiro.")
            return
        if self._lm.activate(key):
            self._cfg.license_tier = Tier.PRO.value
            QMessageBox.information(self, "Licença", "Licença Pro ativada com sucesso!")
            self.accept()
        else:
            QMessageBox.warning(self, "Chave", "Chave inválida. Verifique e tente novamente.")

    def _deactivate(self):
        self._lm.deactivate()
        self._cfg.license_tier = Tier.FREE.value
        QMessageBox.information(self, "Licença", "Licença removida. Modo Free ativo.")
        self.accept()
