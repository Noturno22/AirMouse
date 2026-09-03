"""Upgrade / License dialog for Mãouse.

Diálogo de upgrade orientado à venda: banner de modo FREE em destaque,
pitch de \"nova experiência tecnológica\", grelha de benefícios
revolucionários, planos selecionáveis, CTA dourado a pulsar e ativação
offline de chave Pro.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.licensing import Tier
from i18n import tr
from ui.theme import MAIN_STYLESHEET, breathe_glow

PADDLE_VENDOR_ID = 0  # TODO: preencher com o vendor_id real do Paddle (D2)

# (id, nome, preço curto, linha extra, destaque)
_PRODUCTS = [
    ("lifetime", "Lifetime", "€39,90", "uma vez · para sempre", True),
    ("subscription", "Subscrição", "€4,99/mês", "€3,49/mês no plano anual", False),
    ("family", "Família", "€59,90", "3 dispositivos", False),
    ("access", "Acessibilidade", "€19,95", "sob validação", False),
]

# (chave nome, chave descrição) — só os mais fortes, para não poluir a tela.
_BENEFITS = [
    ("benefit.snap", "benefit.snap_short"),
    ("benefit.voice", "benefit.voice_short"),
    ("benefit.hands", "benefit.hands_short"),
    ("benefit.ai", "benefit.ai_short"),
]


class _BenefitRow(QLabel):
    """Uma linha de benefício: check verde + nome (bold) + mini descrição."""

    def __init__(self, name_key, desc_key, parent=None):
        super().__init__(parent)
        self.setObjectName("BenefitRow")
        self.setText(
            f'<span style="color:#7DDB8A; font-weight:bold;">✓</span>'
            f'&nbsp; <b>{tr(name_key)}</b>'
            f'<span style="color:#8A9AA6;"> — {tr(desc_key)}</span>'
        )
        self.setWordWrap(True)
        self.setToolTip(tr("license.unlocks_title"))


class _ProductCard(QFrame):
    """Cartão de plano selecionável."""

    selected = Signal(str)

    def __init__(self, plan_id, name, price, extra, highlight=False, parent=None):
        super().__init__(parent)
        self._plan_id = plan_id
        self._highlight = highlight
        self.setObjectName("ProductCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(96)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(2)

        top = QHBoxLayout()
        self._name_lbl = QLabel(name.upper())
        self._name_lbl.setObjectName("ProductName")
        top.addWidget(self._name_lbl)
        if highlight:
            badge = QLabel("POPULAR")
            badge.setObjectName("ProductBadge")
            top.addWidget(badge)
        else:
            top.addStretch()
        lay.addLayout(top)

        self._price_lbl = QLabel(price)
        self._price_lbl.setObjectName("ProductPrice")
        lay.addWidget(self._price_lbl)

        self._extra_lbl = QLabel(extra)
        self._extra_lbl.setObjectName("ProductExtra")
        lay.addWidget(self._extra_lbl)

        self._selected = False
        self._refresh_style()

    def set_selected(self, value: bool):
        self._selected = value
        self._refresh_style()

    def _refresh_style(self):
        if self._selected:
            border = "#FFD766" if self._highlight else "#7DD4FF"
            bg = "rgba(255,215,102,0.10)" if self._highlight else "rgba(80,200,255,0.08)"
        else:
            border = "#1A1A2E"
            bg = "rgba(255,255,255,0.02)"
        hover_bg = "rgba(255,255,255,0.06)" if not self._selected else bg
        self.setStyleSheet(
            f"QFrame#ProductCard {{ background-color:{bg}; border:2px solid {border}; "
            f"border-radius:12px; }}"
            f"QFrame#ProductCard:hover {{ background-color:{hover_bg}; }}"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self._plan_id)
        super().mousePressEvent(event)


class LicenseDialog(QDialog):

    def __init__(self, cfg, license_mgr, parent=None):
        super().__init__(parent)
        self._cfg = cfg
        self._lm = license_mgr
        self._selected_plan = "lifetime"
        self.setWindowTitle("Mãouse Pro — Licença")
        self.setObjectName("SettingsDialog")
        self.setStyleSheet(MAIN_STYLESHEET)

        if self._lm.is_pro:
            self.setFixedSize(560, 340)
            self._build_pro_ui()
        else:
            self.setFixedWidth(700)
            self._build_free_ui()
            self.adjustSize()

    # ── Helpers ───────────────────────────────────────────────────────
    def _make_card(self, plan):
        plan_id, name, price, extra, highlight = plan
        card = _ProductCard(plan_id, name, price, extra, highlight)
        card.selected.connect(self._on_plan_selected)
        card.set_selected(plan_id == self._selected_plan)
        return card

    def _on_plan_selected(self, plan_id):
        self._selected_plan = plan_id
        for i in range(self._cards_grid.count()):
            w = self._cards_grid.itemAt(i).widget()
            if isinstance(w, _ProductCard):
                w.set_selected(w._plan_id == plan_id)
        for plan_id2, _name, price, _extra, _ in _PRODUCTS:
            if plan_id2 == plan_id:
                self._cta.setText(f"⭐  {tr('license.cta')} · {price}")
                break

    # ── Free / upgrade ────────────────────────────────────────────────
    def _build_free_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 24)
        lay.setSpacing(12)

        # Banner de modo FREE — faixa fina, discreta mas sempre visível.
        banner = QFrame()
        banner.setObjectName("FreeBanner")
        b_lay = QHBoxLayout(banner)
        b_lay.setContentsMargins(14, 8, 14, 8)
        b_lay.setSpacing(10)
        b_badge = QLabel("FREE")
        b_badge.setObjectName("FreeBadge")
        b_lay.addWidget(b_badge)
        b_title = QLabel(tr("license.free_badge"))
        b_title.setObjectName("FreeSub")
        b_lay.addWidget(b_title)
        b_lay.addStretch()
        lay.addWidget(banner)
        self._banner_pulse = breathe_glow(
            banner, QColor(255, 138, 60),
            min_alpha=60, max_alpha=170, min_blur=3, max_blur=18, ms=850,
        )

        # Hero com o pitch de nova experiência tecnológica.
        hero = QHBoxLayout()
        badge = QLabel("PRO")
        badge.setObjectName("HeroBadge")
        hero.addWidget(badge)
        hero.addSpacing(10)
        title = QLabel(tr("license.hero"))
        title.setObjectName("HeroTitle")
        hero.addWidget(title)
        hero.addStretch()
        lay.addLayout(hero)
        sub = QLabel(tr("license.hero_sub"))
        sub.setObjectName("HeroSubtitle")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        # Benefícios — uma coluna limpa com os principais, sem ruído.
        lay.addSpacing(4)
        feat_title = QLabel(tr("license.unlocks_title"))
        feat_title.setObjectName("SectionTitle")
        feat_title.setAlignment(Qt.AlignLeft)
        lay.addWidget(feat_title)
        for nk, dk in _BENEFITS:
            lay.addWidget(_BenefitRow(nk, dk))

        # Planos.
        lay.addSpacing(2)
        self._cards_grid = QGridLayout()
        self._cards_grid.setSpacing(10)
        for i, plan in enumerate(_PRODUCTS):
            self._cards_grid.addWidget(self._make_card(plan), i // 2, i % 2)
        lay.addLayout(self._cards_grid)

        # CTA principal — a pulsar (destacado).
        self._cta = QPushButton(f"⭐  {tr('license.cta')} · €39,90")
        self._cta.setObjectName("ProCta")
        self._cta.setCursor(Qt.PointingHandCursor)
        self._cta.setFixedHeight(46)
        self._cta.clicked.connect(self._on_cta)
        lay.addWidget(self._cta)
        self._cta_pulse = breathe_glow(
            self._cta, QColor(255, 215, 102),
            min_alpha=70, max_alpha=200, min_blur=6, max_blur=30, ms=850,
        )

        self._build_key_row(lay)

    def _build_key_row(self, lay):
        divider = QFrame()
        divider.setObjectName("MenuDivider")
        divider.setFixedHeight(1)
        lay.addSpacing(6)
        lay.addWidget(divider)
        key_row = QHBoxLayout()
        self._key_edit = QLineEdit()
        self._key_edit.setPlaceholderText(tr("license.has_key"))
        self._key_edit.setObjectName("KeyEdit")
        key_row.addWidget(self._key_edit, 1)
        activate = QPushButton(tr("license.activate_key"))
        activate.setObjectName("SettingsButton")
        activate.clicked.connect(self._activate_key)
        key_row.addWidget(activate)
        lay.addLayout(key_row)

    def _on_cta(self):
        self._open_checkout(self._selected_plan)

    # ── Pro ativo ─────────────────────────────────────────────────────
    def _build_pro_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 28, 30, 28)
        lay.setSpacing(14)

        hero = QHBoxLayout()
        badge = QLabel("PRO")
        badge.setObjectName("HeroBadge")
        hero.addWidget(badge)
        hero.addSpacing(10)
        title = QLabel(tr("license.pro_active_title"))
        title.setObjectName("HeroTitle")
        hero.addWidget(title)
        hero.addStretch()
        lay.addLayout(hero)

        sub = QLabel(tr("license.pro_active_sub"))
        sub.setObjectName("HeroSubtitle")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        lay.addStretch()
        remover = QPushButton(tr("license.remove"))
        remover.setObjectName("SettingsButton")
        remover.clicked.connect(self._deactivate)
        lay.addWidget(remover)

    # ── Ações ─────────────────────────────────────────────────────────
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


class BlockDialog(QDialog):
    """Pop-up urgente de bloqueio total.

    Aparece UMA vez por sessão quando o trial/lease esgotou (o gate de
    ``process_frame`` já impediu o movimento). Sem âncora: título + subtítulo
    sóbrios, CTA claro \"ATIVAR PRO AGORA\" (checkout) e ativação por chave.
    """

    def __init__(self, cfg, license_mgr, parent=None):
        super().__init__(parent)
        self._cfg = cfg
        self._lm = license_mgr
        self.setWindowTitle("Mãouse Pro")
        self.setObjectName("SettingsDialog")
        self.setStyleSheet(MAIN_STYLESHEET)
        self.setModal(True)
        self.setFixedWidth(460)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(12)

        title = QLabel(tr("license.trial_ended"))
        title.setObjectName("HeroTitle")
        title.setWordWrap(True)
        lay.addWidget(title)

        sub = QLabel(tr("license.trial_ended_sub"))
        sub.setObjectName("HeroSubtitle")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        # CTA principal — abre o checkout Paddle (lifetime por omissão).
        cta = QPushButton(f"⭐  {tr('license.activate_now')}")
        cta.setObjectName("ProCta")
        cta.setCursor(Qt.PointingHandCursor)
        cta.setFixedHeight(44)
        cta.clicked.connect(lambda: self._open_checkout("lifetime"))
        lay.addWidget(cta)

        divider = QFrame()
        divider.setObjectName("MenuDivider")
        divider.setFixedHeight(1)
        lay.addSpacing(4)
        lay.addWidget(divider)

        # Ativação por chave (quem já comprou).
        key_row = QHBoxLayout()
        self._key_edit = QLineEdit()
        self._key_edit.setPlaceholderText(tr("license.has_key"))
        self._key_edit.setObjectName("KeyEdit")
        self._key_edit.returnPressed.connect(self._activate_key)
        key_row.addWidget(self._key_edit, 1)
        activate = QPushButton(tr("license.activate_key"))
        activate.setObjectName("SettingsButton")
        activate.clicked.connect(self._activate_key)
        key_row.addWidget(activate)
        lay.addLayout(key_row)

        self._error_lbl = QLabel()
        self._error_lbl.setObjectName("ErrorLabel")
        self._error_lbl.setWordWrap(True)
        self._error_lbl.hide()
        lay.addWidget(self._error_lbl)

        lay.addStretch()

    def _open_checkout(self, product):
        if not self._lm.open_checkout(product, PADDLE_VENDOR_ID):
            self._error_lbl.setText(tr("license.needs_connection"))
            self._error_lbl.show()

    def _activate_key(self):
        key = self._key_edit.text().strip()
        if not key:
            self._error_lbl.setText(tr("license.enter_key"))
            self._error_lbl.show()
            return
        if self._lm.activate(key):
            self._cfg.license_tier = Tier.PRO.value
            self.accept()
        else:
            self._error_lbl.setText(tr("license.activate_failed"))
            self._error_lbl.show()
