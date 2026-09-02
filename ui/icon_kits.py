"""SVG icon kit for AirMouse menu buttons."""
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer


def _root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def icon_path(name):
    return os.path.join(_root(), "assets", "brand", "icons", f"{name}.svg")


def _svg_pixmap(path, size, dpr=1.0):
    renderer = QSvgRenderer(path)
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.fill(Qt.transparent)
    pm.setDevicePixelRatio(dpr)
    painter = _qpainter_for(pm)
    renderer.render(painter)
    painter.end()
    return pm


def _qpainter_for(pm):
    from PySide6.QtGui import QPainter
    return QPainter(pm)


def menu_icon(name, size=20):
    """Loaded QIcon sized for a menu button."""
    pm = _svg_pixmap(icon_path(name), size)
    icon = QIcon(pm)
    # Also register the @2x pixmap for HiDPI menus.
    pm2 = _svg_pixmap(icon_path(name), size * 2, 2.0)
    icon.addPixmap(pm2)
    return icon
