"""Design tokens and styles from IDENTIDADE_VISUAL.md."""
from PySide6.QtCore import QEasingCurve, QVariantAnimation
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QGraphicsDropShadowEffect

BG_PRIMARY = QColor(0, 0, 0)
BG_SECONDARY = QColor(10, 10, 18)
BG_OVERLAY = QColor(0, 0, 0, 217)
BG_TOAST = QColor(0, 0, 0, 230)

TEXT_PRIMARY = QColor(240, 244, 248)
TEXT_SECONDARY = QColor(150, 150, 150)
TEXT_DIM = QColor(100, 100, 100)

ACCENT = QColor(80, 200, 255)
ACCENT_GLOW = QColor(80, 200, 255, 77)

SUCCESS = QColor(90, 220, 90)
WARNING = QColor(255, 170, 60)
ERROR = QColor(255, 80, 80)

GESTURE_COLORS = {}
GESTURE_LABELS = {}


def init_gesture_colors():
    from core.gestures import Gesture
    mapping = {
        Gesture.NONE:      (QColor(150, 150, 150), "SEM MÃO"),
        Gesture.OPEN:      (QColor(80, 200, 255),  "MOVER"),
        Gesture.ONE:       (QColor(80, 200, 255),  "MOVER 1D"),
        Gesture.PINCH:     (QColor(90, 220, 90),   "CLIQUE ESQ"),
        Gesture.PINCH_MID: (QColor(60, 60, 235),   "CLIQUE DIR"),
        Gesture.FIST:      (QColor(255, 80, 200),   "SCROLL"),
        Gesture.PEACE:     (QColor(70, 130, 255),   "DOIS DEDOS"),
        Gesture.THREE:     (QColor(255, 170, 60),  "VOLUME"),
        Gesture.THUMB_UP:  (QColor(140, 225, 225), "PLAY/PAUSA"),
        Gesture.THUMB_DOWN: (QColor(255, 120, 120), "DESLIKE"),
        Gesture.PINKY:     (QColor(180, 120, 255), "COPIAR"),
        Gesture.SHAKA:     (QColor(120, 200, 180), "COLAR"),
    }
    for gest, (color, label) in mapping.items():
        GESTURE_COLORS[gest] = color
        GESTURE_LABELS[gest] = label


def gesture_color(gesture):
    from core.gestures import Gesture
    return GESTURE_COLORS.get(gesture, GESTURE_COLORS.get(Gesture.NONE, TEXT_SECONDARY))


def gesture_label(gesture):
    return GESTURE_LABELS.get(gesture, "SEM MAO")


def make_font(family, size, weight=QFont.Normal):
    f = QFont(family, size)
    f.setWeight(weight)
    return f


FONT_PRIMARY = make_font("Segoe UI", 14)
FONT_PRIMARY_BOLD = make_font("Segoe UI", 14, QFont.DemiBold)
FONT_MONO = make_font("Consolas", 11)
FONT_MONO_BOLD = make_font("Consolas", 11, QFont.DemiBold)
FONT_DISPLAY = make_font("Segoe UI", 32, QFont.Bold)
FONT_BADGE = make_font("Consolas", 12, QFont.DemiBold)
FONT_HELP = make_font("Consolas", 12)
FONT_STATUS = make_font("Consolas", 11)


MAIN_STYLESHEET = """
QWidget#MainWindow {
    background-color: #000000;
}
QLabel#GestureBadge {
    background-color: rgba(0, 0, 0, 204);
    border: 2px solid #50C8FF;
    border-radius: 6px;
    color: #50C8FF;
    font-family: 'Consolas';
    font-size: 22px;
    font-weight: bold;
    padding: 8px 16px;
}
QLabel#StatusBadge {
    background-color: rgba(0, 0, 0, 204);
    border: 1px solid #969696;
    border-radius: 4px;
    color: #F0F4F8;
    font-family: 'Consolas';
    font-size: 12px;
    padding: 4px 10px;
}
QLabel#VoiceIndicator {
    background-color: rgba(0, 0, 0, 204);
    border: 1px solid #969696;
    border-radius: 4px;
    color: #969696;
    font-family: 'Consolas';
    font-size: 12px;
    padding: 4px 10px;
}
QLabel#Toast {
    background-color: rgba(0, 0, 0, 230);
    border: 2px solid #5ADC5A;
    border-radius: 8px;
    color: #5ADC5A;
    font-family: 'Consolas';
    font-size: 16px;
    font-weight: bold;
    padding: 10px 24px;
}
QLabel#ToastLocked {
    background-color: rgba(0, 0, 0, 230);
    border: 2px solid #FF4D4D;
    border-radius: 8px;
    color: #FF4D4D;
    font-family: 'Consolas';
    font-size: 16px;
    font-weight: bold;
    padding: 10px 24px;
}
QLabel#StatusBar {
    background-color: rgba(0, 0, 0, 220);
    color: #F0F4F8;
    font-family: 'Consolas';
    font-size: 12px;
    padding: 4px 12px;
}
QWidget#HelpPanel {
    background-color: #0C0C18;
    border: 1px solid #2A2A45;
    border-radius: 12px;
}
QWidget#HelpPanelHeader {
    background-color: #12121F;
    border-bottom: 1px solid #23233B;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}
CameraView#CameraPreview {
    background-color: #000000;
    border: 2px solid #50C8FF;
    border-radius: 10px;
}
QWidget#MenuPanel {
    background-color: rgba(0, 0, 0, 235);
    border: 1px solid #50C8FF;
    border-radius: 12px;
}
QPushButton#MenuLangBtn {
    background-color: rgba(80, 200, 255, 0.08);
    color: #7DD4FF;
    border: 1px solid #2A3B4A;
    border-radius: 8px;
    padding: 4px 10px;
    font-family: 'Consolas';
    font-size: 11px;
    font-weight: bold;
}
QPushButton#MenuLangBtn:hover {
    background-color: rgba(80, 200, 255, 0.22);
    border-color: #50C8FF;
    color: #FFFFFF;
}
QPushButton#MenuLangBtn:pressed {
    background-color: #50C8FF;
    color: #0A0A12;
}
QLabel#HelpTitle {
    color: #FFFFFF;
    font-family: 'Segoe UI';
    font-size: 15px;
    font-weight: bold;
}
QLabel#HelpSubtitle {
    color: #8A9AA6;
    font-family: 'Segoe UI';
    font-size: 10px;
}
QLabel#HelpSection {
    color: #7DD4FF;
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#HelpRow {
    color: #F0F4F8;
    font-family: 'Consolas';
    font-size: 12px;
}
QLabel#MenuSection {
    color: #7DD4FF;
    font-family: 'Segoe UI';
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 2px;
}
QFrame#MenuDivider {
    background-color: #1A1A2E;
    border: none;
    max-height: 1px;
}
QPushButton#MenuBtn {
    background-color: transparent;
    color: #F0F4F8;
    border: 1px solid #1A1A2E;
    border-left: 3px solid #50C8FF;
    border-radius: 6px;
    padding: 6px 12px;
    font-family: 'Consolas';
    font-size: 12px;
    font-weight: bold;
    text-align: left;
}
QPushButton#MenuBtn:hover {
    background-color: #1A1A2E;
    border-left-color: #7DD4FF;
    color: #FFFFFF;
}
QPushButton#MenuBtn:pressed {
    background-color: #50C8FF;
    color: #0A0A12;
}
QPushButton#MenuBtn:checked {
    background-color: #50C8FF;
    color: #0A0A12;
    border-color: #7DD4FF;
}
QPushButton#MenuBtnUpgrade {
    background-color: rgba(214, 175, 60, 0.12);
    color: #FFD766;
    border: 1px solid #B8860B;
    border-left: 3px solid #FFD766;
    border-radius: 6px;
    padding: 6px 12px;
    font-family: 'Consolas';
    font-size: 12px;
    font-weight: bold;
    text-align: center;
}
QPushButton#MenuBtnUpgrade:hover {
    background-color: #B8860B;
    color: #0A0A12;
    border-color: #FFD766;
}
QPushButton#MenuBtnUpgrade:disabled {
    background-color: transparent;
    color: #6A7B8A;
    border: 1px solid #1A1A2E;
    border-left: 3px solid #2A3B4A;
}
QDialog#SettingsDialog {
    background-color: #000000;
    color: #F0F4F8;
}
QLabel#HeroBadge {
    background-color: #FFD766;
    color: #0A0A12;
    border: none;
    border-radius: 6px;
    padding: 3px 10px;
    font-family: 'Segoe UI';
    font-size: 13px;
    font-weight: bold;
}
QLabel#HeroTitle {
    color: #FFFFFF;
    font-family: 'Segoe UI';
    font-size: 20px;
    font-weight: bold;
}
QLabel#HeroSubtitle {
    color: #969696;
    font-family: 'Segoe UI';
    font-size: 12px;
}
QLabel#SectionTitle {
    color: #7DD4FF;
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
}
QFrame#ProductCard {
    background-color: rgba(255,255,255,0.02);
    border: 2px solid #1A1A2E;
    border-radius: 12px;
}
QFrame#ProductCard:hover {
    border-color: #2A3B4A;
}
QLabel#ProductName {
    color: #7DD4FF;
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: bold;
}
QLabel#ProductBadge {
    background-color: #FFD766;
    color: #0A0A12;
    border: none;
    border-radius: 4px;
    padding: 1px 6px;
    font-family: 'Segoe UI';
    font-size: 9px;
    font-weight: bold;
}
QLabel#ProductPrice {
    color: #FFFFFF;
    font-family: 'Segoe UI';
    font-size: 17px;
    font-weight: bold;
}
QLabel#ProductExtra {
    color: #969696;
    font-family: 'Consolas';
    font-size: 10px;
}
QLabel#FeatureRow {
    color: #F0F4F8;
    font-family: 'Consolas';
    font-size: 12px;
    padding: 1px 0;
}
QPushButton#ProCta {
    background-color: #FFD766;
    color: #1A1A1F;
    border: none;
    border-radius: 8px;
    padding: 12px 20px;
    font-family: 'Segoe UI';
    font-size: 15px;
    font-weight: bold;
}
QPushButton#ProCta:hover {
    background-color: #FFE28A;
}
QPushButton#ProCta:pressed {
    background-color: #E8A93A;
}
QLineEdit#KeyEdit {
    background-color: #12121E;
    color: #F0F4F8;
    border: 1px solid #1A1A2E;
    border-radius: 8px;
    padding: 8px 12px;
    font-family: 'Consolas';
}
QLineEdit#KeyEdit:focus {
    border-color: #50C8FF;
}
QFrame#FreeBanner {
    background-color: #2A1208;
    border: 2px solid #FF8A3C;
    border-radius: 10px;
}
QLabel#FreeBadge {
    background-color: #FF8A3C;
    color: #1A0D00;
    border: none;
    border-radius: 6px;
    padding: 5px 12px;
    font-family: 'Segoe UI';
    font-size: 13px;
    font-weight: bold;
}
QLabel#FreeTitle {
    color: #FFB27D;
    font-family: 'Segoe UI';
    font-size: 14px;
    font-weight: bold;
}
QLabel#FreeSub {
    color: #F0D8C0;
    font-family: 'Segoe UI';
    font-size: 11px;
}
QLabel#BenefitRow {
    color: #EAF3F8;
    font-family: 'Segoe UI';
    font-size: 12px;
    background: transparent;
}
QLabel#SettingsLabel {
    color: #F0F4F8;
    font-family: 'Segoe UI';
    font-size: 13px;
}
QSlider::groove:horizontal {
    border: 1px solid #1A1A2E;
    height: 6px;
    background: #1A1A2E;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #50C8FF;
    border: none;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #7DD4FF;
}
QPushButton#SettingsButton {
    background-color: #50C8FF;
    color: #0A0A12;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-family: 'Segoe UI';
    font-size: 13px;
    font-weight: bold;
}
QPushButton#SettingsButton:hover {
    background-color: #7DD4FF;
}
QPushButton#SettingsButton:pressed {
    background-color: #3AA8E0;
}
QCheckBox {
    color: #F0F4F8;
    font-family: 'Segoe UI';
    font-size: 13px;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #969696;
    border-radius: 4px;
    background: #1A1A2E;
}
QCheckBox::indicator:checked {
    background: #50C8FF;
    border-color: #50C8FF;
}
QComboBox {
    background-color: #1A1A2E;
    color: #F0F4F8;
    border: 1px solid #969696;
    border-radius: 4px;
    padding: 6px 12px;
    font-family: 'Segoe UI';
    font-size: 13px;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #1A1A2E;
    color: #F0F4F8;
    selection-background-color: #50C8FF;
    selection-color: #0A0A12;
}
QGroupBox {
    color: #F0F4F8;
    font-family: 'Segoe UI';
    font-size: 14px;
    font-weight: bold;
    border: 1px solid #1A1A2E;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
"""


def apply_glow(widget, color=ACCENT_GLOW, radius=20):
    glow = QGraphicsDropShadowEffect(widget)
    glow.setBlurRadius(radius)
    glow.setColor(color)
    glow.setOffset(0, 0)
    widget.setGraphicsEffect(glow)
    return glow


def breathe_glow(widget, color=ACCENT_GLOW, min_alpha=60, max_alpha=160,
                 min_blur=6, max_blur=28, ms=900):
    """Aplica um brilho pulsante (\"respiração\") a um widget para o destacar.

    Devolve a animação ativa (perde-se CV em widget se o objetivo for GC, mas
    a app mantém os widgets vivos enquanto o dialogo/menu existir, pelo que um
    destruidor/GC normal nunca ocorre aqui).
    """
    base = QColor(color)
    glow = QGraphicsDropShadowEffect(widget)
    glow.setOffset(0, 0)
    glow.setColor(base)
    # Substitui qualquer efeito anterior (o glow é o efeito gráfico do widget).
    widget.setGraphicsEffect(glow)

    anim = QVariantAnimation(widget)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setDuration(ms)
    anim.setLoopCount(-1)
    anim.setEasingCurve(QEasingCurve.InOutSine)

    def tick(t):
        base.setAlpha(int(min_alpha + (max_alpha - min_alpha) * t))
        glow.setColor(base)
        glow.setBlurRadius(int(min_blur + (max_blur - min_blur) * t))

    anim.valueChanged.connect(tick)
    tick(0.0)
    anim.start()
    return anim
