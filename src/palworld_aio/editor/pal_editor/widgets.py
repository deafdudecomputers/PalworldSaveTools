import math
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget
from PySide6.QtCore import Qt, QTimer, QEvent, QPoint, QPointF, QRectF, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QPainterPath, QPen, QBrush, QFontMetrics, QColor, QLinearGradient
from i18n import t
from palworld_aio import constants
from resource_resolver import resource_path
from palworld_aio.ui.chrome.styles import TOOLTIP_STYLE

PAL_SLOT_MIME = 'application/x-pst-pal-slot'


class FramelessDialog(QDialog):

    def __init__(self, title_key='edit_pals.title', parent=None):

        super().__init__(parent)

        self.setWindowTitle(t(title_key))

        self.setMinimumSize(400, 300)

        self.container = QWidget(self)

        self.container.setObjectName('editPalsContainer')

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self.container)

        container_layout = QVBoxLayout(self.container)

        container_layout.setContentsMargins(0, 0, 0, 0)

        container_layout.setSpacing(0)

        self.content_widget = QWidget(self.container)

        self.content_widget.setObjectName('editPalsContent')

        self.content_layout = QVBoxLayout(self.content_widget)

        self.content_layout.setContentsMargins(16, 12, 16, 16)

        container_layout.addWidget(self.content_widget)

        self._apply_styles()

    def _apply_styles(self):

        self.setStyleSheet(TOOLTIP_STYLE + '''
            QWidget#editPalsContainer {
                background: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:1,
                            stop:0 rgba(12,14,18,0.98),stop:0.5 rgba(10,16,22,0.98),stop:1 rgba(8,12,18,0.98));
                border: 1px solid rgba(125,211,252,0.2);
                border-radius: 12px;
            }
            QWidget#editPalsContent {
                background: transparent;
                border: none;
            }
        ''')

class StarButton(QPushButton):

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            super().mouseReleaseEvent(event)

        else:

            event.ignore()

class StrokedLabel(QLabel):

    def __init__(self, text='', parent=None):

        super().__init__(text, parent)

        self._text_color = Qt.white

    def setStyleSheet(self, style):

        super().setStyleSheet(style)

        if 'color:' in style:

            try:

                import re

                color_match = re.search('color:\\s*([^;]+)', style)

                if color_match:

                    color_str = color_match.group(1).strip()

                    if color_str.startswith('#'):

                        self._text_color = QColor(color_str)

                    elif color_str in ['white', 'black', 'red', 'blue', 'green', 'yellow', 'purple', 'pink']:

                        color_map = {'white': Qt.white, 'black': Qt.black, 'red': Qt.red, 'blue': Qt.blue, 'green': Qt.green, 'yellow': Qt.yellow, 'purple': QColor('#7DD3FC'), 'pink': QColor('#FB7185')}

                        self._text_color = color_map.get(color_str, Qt.white)

            except:

                pass

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)

        bg = QColor(0, 0, 0, 180)

        border = QColor(125, 211, 252, 64)

        painter.setBrush(bg)

        painter.setPen(QPen(border, 1))

        painter.drawRoundedRect(rect, 3, 3)

        path = QPainterPath()

        font = self.font()

        pen = QPen(Qt.black, 2)

        pen.setJoinStyle(Qt.RoundJoin)

        metrics = QFontMetrics(font)

        text_w = metrics.horizontalAdvance(self.text())

        x = (self.width() - text_w) // 2

        y = (self.height() + metrics.ascent() - metrics.descent()) // 2

        path.addText(x, y, font, self.text())

        painter.strokePath(path, pen)

        painter.fillPath(path, QBrush(self._text_color))



class _ShinyStar(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self._filled = True

        self._shining = False

        self._phase = 0.0

        self.setFixedSize(16, 16)

        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setStyleSheet('background: transparent;')

    def set_filled(self, filled):

        self._filled = filled

        self.update()

    def set_phase(self, phase):

        self._phase = phase

        if self._shining:

            self.update()

    def start_shine(self):

        self._shining = True

        self.update()

    def stop_shine(self):

        self._shining = False

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        painter.setRenderHint(QPainter.TextAntialiasing)

        font = QFont()

        font.setPixelSize(14)

        painter.setFont(font)

        rect = self.rect()

        if not self._filled:

            painter.setPen(QColor(255, 215, 0, 40))

            painter.drawText(rect, Qt.AlignCenter, '★')

            painter.end()

            return

        painter.setPen(QColor('#FFD700'))

        painter.drawText(rect, Qt.AlignCenter, '★')

        if self._shining:

            w = rect.width()

            h = rect.height()

            text_path = QPainterPath()

            text_path.addText(0, 0, font, '★')

            br = text_path.boundingRect()

            ox = (w - br.width()) / 2 - br.x()

            oy = (h - br.height()) / 2 - br.y()

            text_path.translate(ox, oy)

            painter.setClipPath(text_path)

            sweep_x = self._phase * w * 1.4 - w * 0.2

            band = w * 0.14

            grad = QLinearGradient(sweep_x, rect.bottom(), sweep_x + band, rect.top())

            grad.setColorAt(0, QColor(255, 255, 200, 0))

            grad.setColorAt(0.5, QColor(255, 255, 255, 200))

            grad.setColorAt(1, QColor(255, 255, 200, 0))

            painter.fillRect(rect, grad)

        painter.end()

class _CircularIcon(QWidget):

    def __init__(self, size=80, parent=None):

        super().__init__(parent)

        self._pixmap = None

        self.setFixedSize(size, size)

    def setPixmap(self, pixmap):

        self._pixmap = pixmap

        self.update()

    def clear(self):

        self._pixmap = None

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        path = QPainterPath()

        r = self.rect()

        path.addEllipse(r.adjusted(2, 2, -2, -2))

        painter.setClipPath(path)

        if self._pixmap and (not self._pixmap.isNull()):

            scaled = self._pixmap.scaled(r.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            x = (r.width() - scaled.width()) // 2

            y = (r.height() - scaled.height()) // 2

            painter.drawPixmap(x, y, scaled)

        else:

            painter.fillPath(path, QBrush(QColor(30, 35, 45)))

            painter.setPen(QPen(QColor(100, 110, 130), 1))

            painter.setFont(QFont('Segoe UI', 16))

            painter.drawText(r, Qt.AlignCenter, '?')



class CornerBracketWidget(QFrame):

    def __init__(self, border_color='#7DD3FC', parent=None):

        super().__init__(parent)

        self._border_color = QColor(border_color)

        self.setObjectName('cornerBracket')

        self.setStyleSheet('QFrame#cornerBracket { background: rgba(10,14,20,0.95); border: none; }')

        self.setFixedSize(56, 64)

    def paintEvent(self, event):

        super().paintEvent(event)

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(self._border_color, 2)

        pen.setCapStyle(Qt.FlatCap)

        painter.setPen(pen)

        w, h = (self.width(), self.height())

        bl = 10

        painter.drawLine(0, bl, 0, 0)

        painter.drawLine(0, 0, bl, 0)

        painter.drawLine(w - bl, 0, w, 0)

        painter.drawLine(w, 0, w, bl)

        painter.drawLine(0, h - bl, 0, h)

        painter.drawLine(0, h, bl, h)

        painter.drawLine(w - bl, h, w, h)

        painter.drawLine(w, h, w, h - bl)

class PortraitBracketWidget(QWidget):

    def __init__(self, corner_color='#7DD3FC', parent=None):

        super().__init__(parent)

        self._corner_color = QColor(corner_color)

        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):

        super().paintEvent(event)

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(self._corner_color, 1.5)

        pen.setCapStyle(Qt.FlatCap)

        painter.setPen(pen)

        w, h = (self.width(), self.height())

        bl = 14

        painter.drawLine(0, bl, 0, 0)

        painter.drawLine(0, 0, bl, 0)

        painter.drawLine(w - bl, 0, w, 0)

        painter.drawLine(w, 0, w, bl)

        painter.drawLine(0, h - bl, 0, h)

        painter.drawLine(0, h, bl, h)

        painter.drawLine(w - bl, h, w, h)

        painter.drawLine(w, h, w, h - bl)

class SANTrackerWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self._value = 100

        self.setFixedHeight(10)

        self.setMinimumWidth(50)

        self.setAttribute(Qt.WA_TranslucentBackground)

    def setValue(self, value):

        self._value = max(0, min(100, int(value)))

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        w, h = (self.width(), self.height())

        bar_h = 2

        y = (h - bar_h) // 2

        painter.setPen(Qt.NoPen)

        painter.setBrush(QColor(20, 35, 30))

        painter.drawRoundedRect(0, y, w, bar_h, 1, 1)

        gradient = QLinearGradient(0, 0, w, 0)

        gradient.setColorAt(0, QColor('#10B981'))

        gradient.setColorAt(1, QColor('#34D399'))

        painter.setBrush(gradient)

        fill_w = int(w * self._value / 100)

        if fill_w > 0:

            painter.drawRoundedRect(0, y, fill_w, bar_h, 1, 1)

        painter.setPen(QPen(QColor(16, 185, 129, 40), 1))

        for i in range(1, 5):

            tx = w * i // 5

            painter.drawLine(tx, y - 1, tx, y + bar_h + 1)

class SkillSlotFrame(QFrame):

    activated = Signal(object)

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton:

            self.activated.emit(self)

            event.accept()

            return

        super().mousePressEvent(event)

    def paintEvent(self, event):

        super().paintEvent(event)

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        w, h = (self.width(), self.height())

        d = int(h * 0.2679)

        painter.setPen(Qt.NoPen)

        painter.setBrush(QColor(20, 25, 35, 40))

        painter.drawRoundedRect(0, 0, w, h, 3, 3)

        path = QPainterPath()

        path.moveTo(w - d, 0)

        path.lineTo(w, 0)

        path.lineTo(w, h)

        path.closeSubpath()

        painter.setBrush(QColor(30, 38, 50, 60))

        painter.drawPath(path)

class GlowRing(QFrame):

    def __init__(self, parent=None):

        super().__init__(parent)

        self._phase = 0.0

        self._awakened = False

        self._timer = QTimer(self)

        self._timer.timeout.connect(self._animate)

        self._timer.setInterval(33)

        self.setStyleSheet('QFrame { background: transparent; border: none; }')

    def set_awakened(self, awakened):

        self._awakened = awakened

        if awakened:

            self._timer.start()

        else:

            self._timer.stop()

        self.update()

    def _animate(self):

        self._phase = (self._phase + 0.06) % (2 * math.pi)

        self.update()

    def paintEvent(self, event):

        super().paintEvent(event)

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        w, h = (self.width(), self.height())

        cx, cy = (w / 2.0, h / 2.0)

        radius = min(w, h) / 2.0 - 1.5

        if self._awakened:

            pulse = (math.sin(self._phase) + 1.0) / 2.0

            for i in range(4, 0, -1):

                r = radius + i * 0.8

                alpha = int((28 + 30 * pulse) / i)

                hue_shift = int(30 * pulse) - i * 5

                red = min(255, 255)

                green = min(255, max(0, 160 - hue_shift))

                blue = min(255, max(0, 0))

                painter.setPen(QPen(QColor(red, green, blue, alpha), 1.0 + i * 0.4))

                painter.setBrush(Qt.NoBrush)

                painter.drawEllipse(QPointF(cx, cy), r, r)

            painter.setPen(QPen(QColor('#FFB800'), 2.2))

            painter.setBrush(Qt.NoBrush)

            painter.drawEllipse(QPointF(cx, cy), radius, radius)

        else:

            painter.setPen(QPen(QColor(125, 211, 252, 115), 2))

            painter.setBrush(Qt.NoBrush)

            painter.drawEllipse(QPointF(cx, cy), radius, radius)

class RotatingCircleWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self._angle = 0.0

        self._pixmap = None

        base_dir = constants.get_base_path()

        path = resource_path(base_dir, 'outer_frame_circle.webp')

        self._pixmap = QPixmap(path)

        self._timer = QTimer(self)

        self._timer.timeout.connect(self._tick)

        self._timer.setInterval(33)

        self._timer.start()

        self.setStyleSheet('background: transparent; border: none;')

    def _tick(self):

        self._angle = (self._angle - 1.8) % 360.0

        self.update()

    def paintEvent(self, event):

        if self._pixmap.isNull():

            return

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        pw, ph = (self._pixmap.width(), self._pixmap.height())

        scaled = self._pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        sw, sh = (scaled.width(), scaled.height())

        cx, cy = (self.width() / 2.0, self.height() / 2.0)

        painter.translate(cx, cy)

        painter.rotate(self._angle)

        painter.drawPixmap(int(-sw / 2), int(-sh / 2), scaled)

        painter.end()

class PassiveEffectOverlay(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self._anim_mode = None

        self._phase = 0.0

        self._timer = QTimer(self)

        self._timer.timeout.connect(self._tick)

        self._timer.setInterval(33)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setStyleSheet('background: transparent; border: none;')

        self.hide()

    def set_mode(self, mode):

        self._anim_mode = mode

        self._phase = 0.0

        if mode:

            self._timer.start()

            self.show()

        else:

            self._timer.stop()

            self.hide()

        self.update()

    def _tick(self):

        self._phase = (self._phase + 0.03) % 10000.0

        self.update()

    def paintEvent(self, event):

        if not self._anim_mode:

            return

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        w, h = (self.width(), self.height())

        painter.setClipRect(QRectF(2, 2, w - 4, h - 4).toAlignedRect())

        if self._anim_mode == 'world_tree':

            cols = 6

            col_w = w / cols

            trail_h = h * 0.55

            cycle = h + trail_h

            speed = h * 0.9

            for c in range(cols):

                cx = c * col_w + 2

                head_y = (cycle - (self._phase * speed + c * h * 0.18)) % cycle

                for i in range(15):

                    y = head_y - i * 5.5

                    if y < 0:

                        y += cycle

                    if 0 <= y < h:

                        alpha = max(0, 160 - i * 13)

                        painter.fillRect(QRectF(cx, y, col_w - 3, 2.2), QColor(168, 85, 247, alpha))

                for i in range(4):

                    y = head_y + i * 3.5

                    if y >= cycle:

                        y -= cycle

                    if 0 <= y < h:

                        alpha = 180 - i * 45

                        painter.fillRect(QRectF(cx, y, col_w - 3, 2.2), QColor(192, 132, 252, alpha))

        elif self._anim_mode == 'legend':

            sweep_x = self._phase * 1.04 * w % (w * 1.4) - w * 0.2

            grad = QLinearGradient(sweep_x, 0, sweep_x + w * 0.35, 0)

            grad.setColorAt(0, QColor(125, 211, 252, 0))

            grad.setColorAt(0.5, QColor(125, 211, 252, 50))

            grad.setColorAt(1, QColor(125, 211, 252, 0))

            painter.fillRect(QRectF(0, 0, w, h), grad)

        painter.end()
