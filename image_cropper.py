import sys
import os
import cv2
import numpy as np
import win32gui
import win32ui
import win32con
from PIL import Image
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QInputDialog, QMessageBox, QSizePolicy, QSpacerItem)
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont, QAction

from src.modules.window_capture import WindowCapture

SAVE_DIR = "template_img"

class ImageCanvas(QWidget):
    """
    画布控件：负责显示图片、处理鼠标画框
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cv_image = None
        self.pixmap = None
        self.begin = QPoint()
        self.end = QPoint()
        self.is_selecting = False
        
        # 确保保存目录存在
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)

        # 设置策略，允许控件随内容调整大小
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def load_image(self, cv_image):
        """加载新的OpenCV图片"""
        self.cv_image = cv_image
        self.h, self.w = cv_image.shape[:2]
        
        # 转换 OpenCV -> QPixmap
        height, width, channel = cv_image.shape
        bytesPerLine = 3 * width
        qImg = QImage(cv_image.data, width, height, bytesPerLine, QImage.Format.Format_BGR888)
        self.pixmap = QPixmap.fromImage(qImg)
        
        # 调整自身大小以适应图片
        self.setFixedSize(width, height)
        self.update()

    def paintEvent(self, event):
        if self.pixmap is None:
            return

        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)

        if self.is_selecting or (self.begin != self.end):
            # 绘制选区矩形
            rect = QRect(self.begin, self.end).normalized()
            painter.fillRect(rect, QColor(0, 255, 0, 50)) # 半透明绿
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.drawRect(rect)
            
            # 显示坐标信息
            info_text = f"X:{rect.x()} Y:{rect.y()} W:{rect.width()} H:{rect.height()}"
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            painter.drawText(rect.topLeft() - QPoint(0, 5), info_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.pixmap:
            self.begin = event.pos()
            self.end = event.pos()
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting and self.pixmap:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.pixmap:
            self.is_selecting = False
            self.end = event.pos()
            self.update()
            self.confirm_selection()

    def confirm_selection(self):
        rect = QRect(self.begin, self.end).normalized()
        if rect.width() < 5 or rect.height() < 5:
            return 

        text, ok = QInputDialog.getText(self, '保存模板', '输入模板名称 (key):')
        
        if ok and text:
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
            
            # 裁剪图片
            crop_img = self.cv_image[y:y+h, x:x+w] # type: ignore
            
            # 保存
            filename = f"{text}.png"
            save_path = os.path.join(SAVE_DIR, filename)
            is_success, im_buf = cv2.imencode(".png", crop_img)
            if is_success:
                im_buf.tofile(save_path)
            
            # 生成代码
            code_snippet = (
                f"    '{text}': {{'path': '{SAVE_DIR}/{filename}', \n"
                f"                  'rect': ({x}, {y}, {x+w}, {y+h}), \n"
                f"                  'base_size': ({self.w}, {self.h})}},"
            )
            
            print(f"--- 生成成功: {text} ---")
            print(code_snippet)
            
            clipboard = QApplication.clipboard()
            clipboard.setText(code_snippet)
            
            QMessageBox.information(self, "成功", f"模板 [{text}] 已保存！\n代码已复制到剪贴板。")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("模板截取工具")
        
        # 主布局
        self.layout = QVBoxLayout(self) # type: ignore
        self.layout.setContentsMargins(0, 0, 0, 0) # type: ignore # 去除边缘空白
        self.cap = WindowCapture()
        hwnd = win32gui.FindWindow(None, "一梦江湖")
        self.cap.set_hwnd(hwnd)
        
        # --- 顶部工具栏 ---
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        self.btn_capture = QPushButton("📸 捕捉/刷新游戏窗口")
        self.btn_capture.setMinimumHeight(40)
        self.btn_capture.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #4CAF50; color: white;")
        self.btn_capture.clicked.connect(self.capture_game)
        
        self.lbl_info = QPushButton("当前状态: 等待截图")
        self.lbl_info.setFlat(True)
        self.lbl_info.setStyleSheet("text-align: left; color: gray;")
        
        self.toolbar_layout.addWidget(self.btn_capture)
        self.toolbar_layout.addWidget(self.lbl_info)
        self.toolbar_layout.addStretch() # 弹簧
        
        self.layout.addLayout(self.toolbar_layout) # type: ignore
        
        # --- 下方画布 ---
        self.canvas = ImageCanvas(self)
        self.layout.addWidget(self.canvas) # type: ignore
        
        # 尝试进行一次初始截图
        self.capture_game()

    def capture_game(self):
        try:
            self.btn_capture.setText("正在截图...")
            QApplication.processEvents() # 刷新UI显示
            
            img = self.cap.capture()
            self.canvas.load_image(img)
            
            h, w = img.shape[:2] # type: ignore
            self.lbl_info.setText(f"当前分辨率: {w} x {h}")
            self.btn_capture.setText("📸 刷新截图")
            
            # 调整窗口大小以适应图片+工具栏
            # 注意：如果图片太大超过屏幕，这里可能需要改成 ScrollArea，但为了保持 1:1 坐标准确，通常不建议缩放显示
            self.resize(w, h + 60) 
            
        except Exception as e:
            QMessageBox.warning(self, "截图失败", str(e))
            self.btn_capture.setText("📸 重试截图")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())