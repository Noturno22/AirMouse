"""Camera feed display with hand skeleton overlay."""
import cv2
import numpy as np

from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QBrush
from PySide6.QtWidgets import QWidget

from core.tracker import HAND_CONNECTIONS
from core.gestures import Gesture
from ui.theme import (
    TEXT_SECONDARY, BG_PRIMARY,
    gesture_color,
)


class CameraView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self._scale = 1.0
        self._offset = QPoint(0, 0)
        self._all_frames = {}
        self._active_side = None
        self._flash = 0
        self._frame_w = 0
        self._frame_h = 0
        self.setMinimumSize(320, 240)

    def update_frame(self, frame_bgr, all_frames, active_side, flash):
        if frame_bgr is None:
            return
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        self._frame_w = w
        self._frame_h = h
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        self._pixmap = QPixmap.fromImage(qimg)
        self._all_frames = all_frames or {}
        self._active_side = active_side
        self._flash = flash
        self._recalc()
        self.update()

    def _recalc(self):
        if self._pixmap.isNull():
            return
        pw, ph = self._pixmap.width(), self._pixmap.height()
        ww, wh = self.width(), self.height()
        self._scale = min(ww / max(pw, 1), wh / max(ph, 1))
        sw, sh = int(pw * self._scale), int(ph * self._scale)
        self._offset = QPoint((ww - sw) // 2, (wh - sh) // 2)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recalc()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self._pixmap.isNull():
            src = QRect(0, 0, self._pixmap.width(), self._pixmap.height())
            dst = QRect(self._offset, self._pixmap.size() * self._scale)
            painter.drawPixmap(dst, self._pixmap, src)
        else:
            painter.fillRect(self.rect(), BG_PRIMARY)

        if self._all_frames:
            self._paint_hands(painter)

        if self._flash > 0:
            painter.fillRect(self.rect(), QColor(90, 220, 90, 40))
            pen = QPen(QColor(90, 220, 90), 6)
            painter.setPen(pen)
            painter.drawRect(3, 3, self.width() - 6, self.height() - 6)

        painter.end()

    def _paint_hands(self, painter):
        for side, hf in self._all_frames.items():
            color = gesture_color(hf.gesture)
            if side != self._active_side:
                self._draw_skeleton(painter, hf, TEXT_SECONDARY, 120)
            else:
                self._draw_skeleton(painter, hf, color, 255)
                self._draw_crosshair(painter, hf, color)

                if hf.gesture == Gesture.PINCH:
                    thumb = self._to_w(hf.points_px[4])
                    tip = self._to_w(hf.index_tip)
                    painter.setPen(QPen(QColor(90, 220, 90), 2))
                    painter.drawLine(thumb, tip)

                if hf.gesture == Gesture.PEACE:
                    mid = self._to_w(hf.points_px[12])
                    painter.setPen(QPen(QColor(255, 80, 200), 2))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(mid, 7, 7)

                self._draw_pinch_bar(painter, hf)

    def _draw_skeleton(self, painter, hf, color, alpha=255):
        c = QColor(color)
        c.setAlpha(alpha)
        painter.setPen(QPen(c, 1))
        for a, b in HAND_CONNECTIONS:
            pa = self._to_w(hf.points_px[a])
            pb = self._to_w(hf.points_px[b])
            painter.drawLine(pa, pb)

    def _draw_crosshair(self, painter, hf, color):
        px, py = self._to_w(hf.palm_center)
        painter.setPen(QPen(color, 2))
        painter.drawLine(px - 14, py, px + 14, py)
        painter.drawLine(px, py - 14, px, py + 14)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPoint(px, py), 9, 9)

    def _draw_pinch_bar(self, painter, hf):
        w, h = self.width(), self.height()
        ratio = min(hf.pinch_ratio / 1.2, 1.0)
        bar_w = int(ratio * (w - 24))
        color = gesture_color(hf.gesture) if hf.gesture == Gesture.PINCH else TEXT_SECONDARY
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawRect(12, h - 30, bar_w, 6)

    def _to_w(self, point):
        if self._pixmap.isNull():
            return QPoint(int(point[0]), int(point[1]))
        x = int(point[0] * self._scale + self._offset.x())
        y = int(point[1] * self._scale + self._offset.y())
        return QPoint(x, y)
