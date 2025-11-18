from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QRectF
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QPainter, QBrush, QColor, Qt


class AnimatedButton(QPushButton):
    """
    动画按钮类，继承自 QPushButton.
    """
    def __init__(self, text="", parent=None, radius=12):
        super().__init__(text, parent)
        self.radius = radius

        # 默认按钮配色，可由主题更改
        self.bg_color = QColor("#47a0e4")
        self.text_color = QColor("#ffffff")

        # 缩放动画
        self._anim = QPropertyAnimation(self, b"geometry", self)
        self._anim.setDuration(120)
        self._anim.setEasingCurve(QEasingCurve.OutQuad)
        self._orig_rect = None

        # 不使用系统样式
        self.setFlat(True)

    # ---------------- 动画效果 ----------------
    def mousePressEvent(self, event):
        self._orig_rect = self.geometry()

        w, h = self._orig_rect.width(), self._orig_rect.height()
        new_w, new_h = int(w * 0.92), int(h * 0.92)
        dx, dy = (w - new_w) // 2, (h - new_h) // 2

        self._anim.stop()
        self._anim.setStartValue(self._orig_rect)
        self._anim.setEndValue(QRect(
            self._orig_rect.x() + dx,
            self._orig_rect.y() + dy,
            new_w,
            new_h
        ))
        self._anim.start()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._orig_rect:
            self._anim.stop()
            self._anim.setStartValue(self.geometry())
            self._anim.setEndValue(self._orig_rect)
            self._anim.start()

        super().mouseReleaseEvent(event)

    # ---------------- 绘制按钮 ----------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect())

        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self.radius, self.radius)

        # 绘制文字
        painter.setPen(self.text_color)
        painter.drawText(rect, Qt.AlignCenter, self.text())

    # ---------------- 主题相关接口 ----------------
    def apply_light(self):
        self.bg_color = QColor("#30aee3")
        self.text_color = QColor("#ffffff")
        self.repaint()

    def apply_dark(self):
        self.bg_color = QColor("#003B94")
        self.text_color = QColor("#ffffff")
        self.repaint()
