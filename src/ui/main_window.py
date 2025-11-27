import sys
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTextEdit, QStackedLayout, QFormLayout, 
    QSpinBox, QComboBox, QProgressBar, QCheckBox, QScrollArea
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
from .pages.page_dir import PageDir
from .pages.page_task import PageScript
from .pages.page_setting import PageSetting
from .core.theme_manager import theme_manager
from .models.settings_model import SettingsModel

class MainWindow(QMainWindow):
    """
    主窗口类，包含导航栏和内容区域.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YMJH Script")
        self.setGeometry(200, 100, 1200, 800)

        # 主布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # 左侧导航栏
        self.nav_widget = QWidget()
        self.nav_widget.setFixedWidth(180)
        self.nav_layout = QVBoxLayout(self.nav_widget)
        self.nav_layout.setSpacing(20)
        self.nav_layout.setContentsMargins(10, 20, 10, 20)

        self.btn_dir = QPushButton("使用说明")
        self.btn_script = QPushButton("脚本执行")
        self.btn_setting = QPushButton("设置")

        for btn in [self.btn_dir, self.btn_script, self.btn_setting]:
            btn.setMinimumHeight(40)
            self.nav_layout.addWidget(btn)
        self.nav_layout.addStretch()
        self.main_layout.addWidget(self.nav_widget)

        # 右侧内容区
        self.content_widget = QWidget()
        self.stack_layout = QStackedLayout(self.content_widget)
        self.main_layout.addWidget(self.content_widget, 1)

        # 页面
        self.page_dir = PageDir()
        self.page_script = PageScript()
        self.page_setting = PageSetting(main_window=self)

        self.stack_layout.addWidget(self.page_dir)
        self.stack_layout.addWidget(self.page_script)
        self.stack_layout.addWidget(self.page_setting)

        # 映射
        self.page_dict = {
            "dir": (self.page_dir, self.btn_dir),
            "script": (self.page_script, self.btn_script),
            "setting": (self.page_setting, self.btn_setting)
        }

        # 按钮绑定
        self.btn_dir.clicked.connect(lambda: self.switch_page("dir"))
        self.btn_script.clicked.connect(lambda: self.switch_page("script"))
        self.btn_setting.clicked.connect(lambda: self.switch_page("setting"))
        self.switch_page("dir")

        # 控制器
        # 设置
        self.settings_model = SettingsModel()
        current_theme = self.settings_model.get_current_theme() if self.settings_model.get_current_theme() else "light"
        theme_manager.apply_theme(current_theme)

    # 页面切换
    def switch_page(self, name):
        """
        切换到指定页面.
        Args:
            name (str): 页面名称，必须在 self.page_dict 中
        """
        page, btn = self.page_dict[name]
        index = self.stack_layout.indexOf(page)
        self.stack_layout.setCurrentIndex(index)
        for _, b in self.page_dict.values():
            b.setEnabled(True)
            b.setStyleSheet("")
        btn.setEnabled(False)
        btn.setStyleSheet("background-color: #0078D7; color: white; font-weight: bold;")


def main():
    """
    主函数，启动应用.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
