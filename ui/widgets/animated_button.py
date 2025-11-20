from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QPainter, QBrush, QColor, Qt
from PySide6.QtCore import QRectF


class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None, radius=12):
        super().__init__(text, parent)

        self.radius = radius
        self.scale = 1.0  # 添加缩放变量

        self.bg_color = QColor("#47a0e4")
        self.text_color = QColor("#ffffff")

        # 动画作用在 self.scale
        self._anim = QPropertyAnimation(self, b"scaleValue")
        self._anim.setDuration(120)
        self._anim.setEasingCurve(QEasingCurve.OutQuad)

        self.setFlat(True)

    # ---------- scale 属性 ----------
    def getScale(self):
        return self.scale

    def setScale(self, value):
        self.scale = value
        self.update()

    scaleValue = Property(float, getScale, setScale)

    # ---------- 动画 ----------
    def mousePressEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self.scale)
        self._anim.setEndValue(0.92)
        self._anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self.scale)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().mouseReleaseEvent(event)

    # ---------- 绘制 ----------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # 根据 scale 计算缩放后的大小与偏移
        new_w = w * self.scale
        new_h = h * self.scale
        dx = (w - new_w) / 2
        dy = (h - new_h) / 2

        rect = QRectF(dx, dy, new_w, new_h)

        # 背景
        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self.radius, self.radius)

        # 文字
        painter.setPen(self.text_color)
        painter.drawText(rect, Qt.AlignCenter, self.text())

    # ---------- 主题 ----------
    def apply_light(self):
        self.bg_color = QColor("#30aee3")
        self.text_color = QColor("#ffffff")
        self.update()

    def apply_dark(self):
        self.bg_color = QColor("#003B94")
        self.text_color = QColor("#ffffff")
        self.update()
