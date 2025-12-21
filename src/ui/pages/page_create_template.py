import os
import cv2
import win32gui
import win32con
import ctypes
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                               QPushButton, QInputDialog, QMessageBox, QSizePolicy,  QScrollArea, QGridLayout, QLineEdit, QSpinBox)
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont

from src.modules.window_capture import WindowCapture

class PageCreateTemplate(QWidget):
    """
    模板截取工具
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user32 = ctypes.windll.user32

        self.setWindowTitle("模板截取工具")
        self.cap = WindowCapture()
        self.canvas = ImageCanvas(self)
        self.hwnd = None

        # 主布局
        self.layout = QVBoxLayout(self) # type: ignore
        self.layout.setContentsMargins(0, 0, 0, 0) # type: ignore

        self._setup_ui()

    def _setup_ui(self):
        """
        设置用户界面元素
        """
        # --- 顶部工具栏 ---
        self.toolbar_layout = QGridLayout()
        self.toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        self.btn_capture = QPushButton("捕捉/刷新游戏窗口")
        self.btn_capture.clicked.connect(self.capture_game)
        
        self.lbl_info = QPushButton("当前状态: 等待截图")
        self.lbl_info.setFlat(True)
        self.lbl_info.setStyleSheet("text-align: left; color: gray;")

        self.padding_input = QSpinBox()
        self.padding_input.setMinimum(0)
        self.padding_input.setMaximum(50)
        self.padding_input.setValue(5)
        self.padding_input.setSingleStep(1)
        self.padding_input.setToolTip("设置截图区域内边距")
        self.padding_input.valueChanged.connect(self.canvas.set_padding)

        self.title_input = QLineEdit("一梦江湖")
        self.title_input.setPlaceholderText("请输入窗口名称")
        self.title_input.setMinimumWidth(80)

        self.dir_input = QLineEdit("template_img")
        self.dir_input.setPlaceholderText("请输入保存目录")
        self.dir_input.textChanged.connect(self.canvas.set_dir)

        self.width_input = QSpinBox()
        self.width_input.setMinimum(0)
        self.width_input.setMaximum(self.user32.GetSystemMetrics(0))
        self.width_input.setValue(1920)
        self.width_input.setSingleStep(1)
        self.width_input.setToolTip("设置游戏窗口宽度")

        self.height_input = QSpinBox()
        self.height_input.setMinimum(0)
        self.height_input.setMaximum(self.user32.GetSystemMetrics(1))
        self.height_input.setValue(1080)
        self.height_input.setSingleStep(1)
        self.height_input.setToolTip("设置游戏窗口高度")

        self.connect_btn = QPushButton("连接游戏窗口")
        self.connect_btn.clicked.connect(self.connect_game)

        self.apply_btn = QPushButton("应用窗口大小")
        self.apply_btn.clicked.connect(self.apply_window_size)
        
        self.toolbar_layout.addWidget(self.btn_capture, 0, 0, 1, 1)
        self.toolbar_layout.addWidget(self.lbl_info, 0, 1, 1, 1)
        self.toolbar_layout.addWidget(self.padding_input, 0, 2, 1, 1)
        self.toolbar_layout.addWidget(self.dir_input, 0, 3, 1, 1)
        self.toolbar_layout.addWidget(self.title_input, 0, 3, 1, 1)
        self.toolbar_layout.addWidget(self.connect_btn, 0, 4, 1, 1)
        self.toolbar_layout.addWidget(self.width_input, 0, 5, 1, 1)
        self.toolbar_layout.addWidget(self.height_input, 0, 6, 1, 1)
        self.toolbar_layout.addWidget(self.apply_btn, 0, 7, 1, 1)
        
        self.layout.addLayout(self.toolbar_layout) # type: ignore
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) # 允许内容适应
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter) # 图片居中显示
        self.scroll_area.setWidget(self.canvas)
        
        self.layout.addWidget(self.scroll_area) # type: ignore

        self.canvas.set_padding(int(self.padding_input.text().strip()))
        self.canvas.set_dir(self.dir_input.text().strip())
    
    def connect_game(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "输入错误", "请输入窗口名称")
            return
        self.hwnd = win32gui.FindWindow(None, title)
        if not self.hwnd:
            QMessageBox.warning(self, "窗口未找到", f"未找到窗口名称为 '{title}' 的游戏窗口")
            return
        self.cap.set_hwnd(self.hwnd)
        self.lbl_info.setText(f"已连接窗口: {title}")

    def capture_game(self):
        """
        捕捉游戏窗口截图
        """
        try:
            self.btn_capture.setText("正在截图...")
            QApplication.processEvents() # 刷新UI显示
            
            img = self.cap.capture()
            self.canvas.load_image(img)
            
            h, w = img.shape[:2] # type: ignore
            self.lbl_info.setText(f"当前分辨率: {w} x {h}")
            self.btn_capture.setText("刷新截图")
            
        except Exception as e:
            QMessageBox.warning(self, "截图失败", str(e))
            self.btn_capture.setText("重试截图")
    
    def apply_window_size(self):
        """
        设置游戏窗口大小
        """
        if not self.hwnd:
            QMessageBox.warning(self, "窗口未连接", "请先连接游戏窗口")
            return

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        # 恢复窗口
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)

        # 获取窗口样式
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)
        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)

        # 目标客户端大小
        client_width = int(self.width_input.text().strip())
        client_height = int(self.height_input.text().strip())

        if client_width <= 0 or client_height <= 0:
            QMessageBox.warning(self, "输入错误", "请输入有效的窗口宽度和高度")
            return

        # 构造 RECT
        rect = RECT(0, 0, client_width, client_height)

        # 调用 Win32 API
        self.user32.AdjustWindowRectEx(
            ctypes.byref(rect),
            style,
            False,      # 是否有菜单
            ex_style
        )

        # 计算窗口大小
        window_width = rect.right - rect.left
        window_height = rect.bottom - rect.top

        # 设置窗口
        win32gui.MoveWindow(
            self.hwnd,
            0, 0,
            window_width,
            window_height,
            True
        )

class ImageCanvas(QWidget):
    """
    画布控件：负责显示图片、处理鼠标画框
    """
    def __init__(self, parent=None, save_dir: str = "", padding: int = 0):
        super().__init__(parent)
        self.cv_image = None
        self.pixmap = None
        self.begin = QPoint()
        self.end = QPoint()
        self.is_selecting = False
        self.save_dir = save_dir
        self.padding = padding

        # 设置画布的最小尺寸策略
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def load_image(self, cv_image):
        """
        加载新的OpenCV图片
        """
        self.cv_image = cv_image
        self.h, self.w = cv_image.shape[:2]
        
        # 转换 OpenCV -> QPixmap
        height, width, channel = cv_image.shape
        bytesPerLine = 3 * width
        qImg = QImage(cv_image.data, width, height, bytesPerLine, QImage.Format.Format_BGR888)
        self.pixmap = QPixmap.fromImage(qImg)
        
        # 强制画布大小等于图片大小，保证滚动条能正确工作
        self.setFixedSize(width, height)
        self.update()

    def paintEvent(self, event):
        if self.pixmap is None:
            return

        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)

        if self.is_selecting or (self.begin != self.end):
            rect = QRect(self.begin, self.end).normalized()
            painter.fillRect(rect, QColor(0, 255, 0, 50)) 
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.drawRect(rect)
            
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
            
            crop_img = self.cv_image[y:y+h, x:x+w] # type: ignore
            
            filename = f"{text}.png"
            save_path = os.path.join(self.save_dir, filename)
            is_success, im_buf = cv2.imencode(".png", crop_img)
            if is_success:
                im_buf.tofile(save_path)
            
            code_snippet = (
                f"    '{text}': {{'path': '{self.save_dir}/{filename}', \n"
                f"                  'rect': ({x+self.padding}, {y+self.padding}, {x+w-self.padding}, {y+h-self.padding}), \n"
                f"                  'base_size': ({self.w}, {self.h})}},"
            )
            
            print(f"--- 生成成功: {text} ---")
            print(code_snippet)
            
            clipboard = QApplication.clipboard()
            clipboard.setText(code_snippet)
            
            QMessageBox.information(self, "成功", f"模板 [{text}] 已保存！\n代码已复制到剪贴板。")

    def set_dir(self, dir_path):
        self.save_dir = dir_path
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def set_padding(self, padding: int):
        self.padding = padding
