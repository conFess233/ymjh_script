import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTextEdit, QStackedLayout, QFormLayout, 
    QSpinBox, QComboBox, QProgressBar, QCheckBox, QScrollArea
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
from widgets.animated_button import AnimatedButton
from pages.page_dir import PageDir
from pages.page_script import PageScript
from pages.page_setting import PageSetting
from widgets.animated_button import AnimatedButton
from controllers.theme_controller import ThemeController
from models.settings_model import SettingsModel



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

        self.btn_dir = AnimatedButton("使用说明")
        self.btn_script = AnimatedButton("脚本执行")
        self.btn_setting = AnimatedButton("设置")

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
        # 主题控制器
        self.theme_controller = ThemeController(self)
        # 设置
        self.settings_model = SettingsModel(main_window=self)
        # 上次设置的主题
        self.settings_model.apply_theme()

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

    def apply_light_theme(self):
        """
        应用浅色主题.
        """
        palette = QPalette()

        # Window
        palette.setColor(QPalette.Window, QColor("#f0f0f0"))
        palette.setColor(QPalette.WindowText, Qt.black)

        # Input / text areas
        palette.setColor(QPalette.Base, QColor("#ffffff"))
        palette.setColor(QPalette.AlternateBase, QColor("#f7f7f7"))
        palette.setColor(QPalette.Text, Qt.black)

        # Buttons
        palette.setColor(QPalette.Button, QColor("#e0e0e0"))
        palette.setColor(QPalette.ButtonText, Qt.black)

        # Highlight / selection
        palette.setColor(QPalette.Highlight, QColor("#0078D7"))
        palette.setColor(QPalette.HighlightedText, Qt.white)

        # Links / tooltip
        palette.setColor(QPalette.Link, QColor("#2980b9"))
        palette.setColor(QPalette.ToolTipBase, QColor("#ffffdc"))
        palette.setColor(QPalette.ToolTipText, Qt.black)

        # Disabled text
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#808080"))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#808080"))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#808080"))
        
        for btn in self.findChildren(AnimatedButton):
            btn.apply_light()
            
        self.setPalette(palette)
        self.update()
        self.repaint()
        self.refresh_widgets()

    def apply_dark_theme(self):
        """
        应用深色主题.
        """
        palette = QPalette()

        # Window
        palette.setColor(QPalette.Window, QColor("#2b2b2b"))
        palette.setColor(QPalette.WindowText, Qt.white)

        # Input areas
        palette.setColor(QPalette.Base, QColor("#3c3f41"))
        palette.setColor(QPalette.AlternateBase, QColor("#2b2b2b"))
        palette.setColor(QPalette.Text, Qt.white)
        
        # combo box
        for combo in self.findChildren(QComboBox):
            combo_palette = combo.palette()

            # 设置文字颜色
            combo_palette.setColor(QPalette.Text, QColor("#000000"))

            # 设置下拉文字颜色
            combo_palette.setColor(QPalette.ButtonText, QColor("#000000"))

            combo.setPalette(combo_palette)

        # Buttons
        palette.setColor(QPalette.Button, QColor("#3c3f41"))
        palette.setColor(QPalette.ButtonText, Qt.white)

        # Highlight
        palette.setColor(QPalette.Highlight, QColor("#367bf5"))
        palette.setColor(QPalette.HighlightedText, Qt.white)

        # Links / tooltip
        palette.setColor(QPalette.Link, QColor("#64b5ff"))
        palette.setColor(QPalette.ToolTipBase, QColor("#3c3f41"))
        palette.setColor(QPalette.ToolTipText, QColor("#7a7a7a"))

        # Disabled text
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#7a7a7a"))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#7a7a7a"))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#7a7a7a"))
        
        for btn in self.findChildren(AnimatedButton):
         btn.apply_dark()

        self.setPalette(palette)
        self.update()
        self.repaint()
        self.refresh_widgets()

    def refresh_widgets(self):
        """
        刷新所有子widget的显示.
        """
        for w in self.findChildren(QWidget):
                w.repaint()  
    
    def closeEvent(self, event):
        # 在退出前保存当前 GUI 设置
        font_size = self.font().pointSize()
        theme = self.settings_model.get_current_theme()
        self.settings_model.set_settings(theme=theme, font_size=font_size)
        super().closeEvent(event)
        
    

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
