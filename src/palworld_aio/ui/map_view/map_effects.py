import math
import random
from PySide6.QtWidgets import QGraphicsObject
from PySide6.QtCore import Qt, QRectF, QPointF, Property, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QRadialGradient
class EffectItem(QGraphicsObject):
    def __init__(self, x, y, duration=1000):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.duration = duration
        self._progress = 0.0
        self.setPos(x, y)
    @Property(float)
    def progress(self):
        return self._progress
    @progress.setter
    def progress(self, value):
        self._progress = value
        self.update()
    def boundingRect(self):
        return QRectF(-200, -200, 400, 400)
class DeleteEffect(EffectItem):
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        radius = self._progress * 150
        alpha = int(255 * (1 - self._progress))
        painter.setPen(QPen(QColor(255, 80, 80, alpha), 5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), radius, radius)
        if radius > 30:
            painter.setPen(QPen(QColor(255, 150, 0, alpha), 3))
            painter.drawEllipse(QPointF(0, 0), radius - 30, radius - 30)
        if self._progress < 0.3:
            flash_alpha = int(200 * (1 - self._progress / 0.3))
            painter.setBrush(QColor(255, 200, 0, flash_alpha))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(0, 0), 40, 40)
class ImportEffect(EffectItem):
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        for i in range(3):
            phase = (self._progress + i * 0.33) % 1.0
            radius = phase * 100
            alpha = int(180 * (1 - phase))
            painter.setPen(QPen(QColor(0, 255, 150, alpha), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0, 0), radius, radius)
        if self._progress < 0.7:
            painter.setBrush(QColor(100, 255, 200, int(255 * (1 - self._progress))))
            painter.setPen(Qt.NoPen)
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                dist = 60 + self._progress * 40
                x = math.cos(rad) * dist
                y = math.sin(rad) * dist
                size = 8 - self._progress * 6
                painter.drawEllipse(QPointF(x, y), size, size)
class CalibrationEffect(QGraphicsObject):
    def __init__(self, x, y):
        super().__init__()
        self.setPos(x, y)
        self._phase = 0.0
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)
    def _tick(self):
        self._phase = (self._phase + 0.04) % 1.0
        self.update()
    def stop(self):
        self._timer.stop()
    def boundingRect(self):
        return QRectF(-120, -120, 240, 240)
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        r1 = 20 + self._phase * 60
        r2 = 20 + (1 - self._phase) * 60
        a1 = int(200 * (1 - self._phase))
        a2 = int(200 * self._phase)
        painter.setPen(QPen(QColor(255, 136, 0, a1), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), r1, r1)
        painter.setPen(QPen(QColor(255, 180, 0, a2), 3))
        painter.drawEllipse(QPointF(0, 0), r2, r2)
        painter.setPen(QPen(QColor(255, 136, 0, 180), 1))
        painter.drawLine(-25, 0, 25, 0)
        painter.drawLine(0, -25, 0, 25)
class CoordChangeEffect(QGraphicsObject):
    def __init__(self, x, y):
        super().__init__()
        self.setPos(x, y)
        self._phase = 0.0
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)
        self._duration = 0
    def _tick(self):
        self._phase = (self._phase + 0.03) % 1.0
        self._duration += 1
        self.update()
        if self._duration > 200:
            self.stop()
    def stop(self):
        self._timer.stop()
        if self.scene():
            self.scene().removeItem(self)
    def boundingRect(self):
        return QRectF(-160, -160, 320, 320)
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        c = QColor(100, 200, 255)
        r = 10 + self._phase * 100
        a = int(220 * (1 - self._phase))
        painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), a), 4))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), r, r)
        r2 = 10 + (1 - self._phase) * 100
        a2 = int(220 * self._phase)
        painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), a2), 3))
        painter.drawEllipse(QPointF(0, 0), r2, r2)
        painter.setPen(QPen(QColor(255, 255, 255, a), 2))
        painter.drawLine(-20, 0, 20, 0)
        painter.drawLine(0, -20, 0, 20)
        for i in range(4):
            angle = math.radians(i * 90 + self._phase * 360)
            dot_r = 12 + self._phase * 30
            dx = math.cos(angle) * dot_r
            dy = math.sin(angle) * dot_r
            da = int(200 * (1 - abs(self._phase - 0.5) * 2))
            painter.setBrush(QColor(100, 200, 255, da))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(dx, dy), 4, 4)
class SwapSourceEffect(QGraphicsObject):
    def __init__(self, x, y):
        super().__init__()
        self.setPos(x, y)
        self._phase = 0.0
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)
    def _tick(self):
        self._phase = (self._phase + 0.035) % 1.0
        self.update()
    def stop(self):
        self._timer.stop()
        if self.scene():
            self.scene().removeItem(self)
    def boundingRect(self):
        return QRectF(-140, -140, 280, 280)
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        outer_r = 30 + self._phase * 80
        outer_a = int(200 * (1 - self._phase))
        painter.setPen(QPen(QColor(255, 180, 50, outer_a), 4))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), outer_r, outer_r)
        inner_r = 30 + (1 - self._phase) * 80
        inner_a = int(200 * self._phase)
        painter.setPen(QPen(QColor(255, 220, 100, inner_a), 3))
        painter.drawEllipse(QPointF(0, 0), inner_r, inner_r)
        dot_angle = self._phase * 360
        for i in range(3):
            a = math.radians(dot_angle + i * 120)
            d = 20 + self._phase * 50
            dx = math.cos(a) * d
            dy = math.sin(a) * d
            da = int(220 * (1 - abs(self._phase - 0.5) * 2))
            painter.setBrush(QColor(255, 200, 80, da))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(dx, dy), 5, 5)
class ExportEffect(EffectItem):
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        beam_height = self._progress * 200
        alpha = int(200 * (1 - self._progress))
        gradient = QRadialGradient(0, -beam_height / 2, 30)
        gradient.setColorAt(0, QColor(100, 200, 255, alpha))
        gradient.setColorAt(1, QColor(100, 200, 255, 0))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRect(QRectF(-20, -beam_height, 40, beam_height))
        for i in range(5):
            particle_y = -(i * 40 + self._progress * 150) % 200
            particle_alpha = int(alpha * (1 - abs(particle_y) / 200))
            painter.setBrush(QColor(150, 220, 255, particle_alpha))
            painter.drawEllipse(QPointF(random.randint(-15, 15), particle_y), 4, 4)