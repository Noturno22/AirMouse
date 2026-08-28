"""Brand assets and helpers for the AirMouse UI."""
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget


def _root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset(*parts):
    return os.path.join(_root(), "assets", "brand", *parts)


def svg_pixmap(rel_svg, width, height, dpr=1.0):
    """Render an SVG brand asset (list of path parts) to a QPixmap."""
    renderer = QSvgRenderer(asset(*rel_svg))
    pm = QPixmap(int(max(width, 1) * dpr), int(max(height, 1) * dpr))
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    renderer.render(painter)
    painter.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def wordmark_pixmap(width, height, dpr=1.0):
    """Lockup horizontal 'Mãoouse' (logo-dark.svg, ratio 600x200)."""
    return svg_pixmap(("logo-dark.svg",), width, height, dpr)


def symbol_pixmap(width, height, dpr=1.0):
    """Símbolo quadrado da marca (logo-symbol.svg, ratio 1:1)."""
    return svg_pixmap(("logo-symbol.svg",), width, height, dpr)


class BrandHeader(QWidget):
    """Área de marca: símbolo quadrado (default) ou lockup 'Mãoouse'."""

    RATIO = 600.0 / 200.0

    def __init__(self, parent=None, wordmark=False):
        super().__init__(parent)
        self.setObjectName("BrandHeader")
        self.setMinimumHeight(56)
        self._wordmark = wordmark

    def paintEvent(self, event):
        dpr = self.devicePixelRatioF() or 1.0
        painter = QPainter(self)
        if self._wordmark:
            h = max(self.height() - 10, 1)
            w = int(h * self.RATIO)
            pm = wordmark_pixmap(w, h, dpr)
            x = max((self.width() - w) // 2, 0)
            y = (self.height() - h) // 2
            painter.drawPixmap(int(x), int(y), pm)
        else:
            s = max(min(self.height() - 6, self.width() - 6), 1)
            pm = symbol_pixmap(s, s, dpr)
            x = (self.width() - s) // 2
            y = (self.height() - s) // 2
            painter.drawPixmap(int(x), int(y), pm)
        painter.end()
