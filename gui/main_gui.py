import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTextEdit, QStackedLayout, QFormLayout, 
    QSpinBox, QComboBox, QProgressBar, QCheckBox, QScrollArea
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YMJH Script")
        self.setGeometry(200, 100, 1200, 800)
        self.current_theme = "light"  # 默认主题

        # === 主布局 ===
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # === 左侧导航栏 ===
        self.nav_widget = QWidget()
        self.nav_widget.setFixedWidth(180)
        self.nav_layout = QVBoxLayout(self.nav_widget)
        self.nav_layout.setSpacing(15)
        self.nav_layout.setContentsMargins(10, 20, 10, 20)

        self.btn_dir = QPushButton("使用说明")
        self.btn_script = QPushButton("脚本执行")
        self.btn_setting = QPushButton("设置")

        for btn in [self.btn_dir, self.btn_script, self.btn_setting]:
            btn.setMinimumHeight(40)
            self.nav_layout.addWidget(btn)
        self.nav_layout.addStretch()
        self.main_layout.addWidget(self.nav_widget)

        # === 右侧内容区 ===
        self.content_widget = QWidget()
        self.stack_layout = QStackedLayout(self.content_widget)
        self.main_layout.addWidget(self.content_widget, 1)

        # 页面
        self.page_dir = self.create_dir_page()
        self.page_script = self.create_script_page()
        self.page_setting = self.create_setting_page()

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

        # 默认浅色主题
        self.apply_light_theme()

    # 页面切换
    def switch_page(self, name):
        page, btn = self.page_dict[name]
        index = self.stack_layout.indexOf(page)
        self.stack_layout.setCurrentIndex(index)
        for _, b in self.page_dict.values():
            b.setEnabled(True)
            b.setStyleSheet("")
        btn.setEnabled(False)
        btn.setStyleSheet("background-color: #0078D7; color: white; font-weight: bold;")

    # --- 页面内容 ---
    def create_dir_page(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("YMJH Script 使用说明"))
        v.addWidget(QLabel("1. 点击左侧“脚本执行”进入脚本控制页面。\n2. 在“设置”页可调整主题等参数。"))
        v.addStretch()
        return w

    def create_script_page(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("脚本执行区域"))
        form = QFormLayout()
        time_spin = QSpinBox()
        mode_combo = QComboBox()
        mode_combo.addItems(["普通模式", "快速模式", "安全模式"])
        form.addRow("运行时间（秒）:", time_spin)
        form.addRow("运行模式:", mode_combo)
        v.addLayout(form)
        v.addWidget(QProgressBar())
        v.addWidget(QTextEdit("脚本日志输出区域"))
        v.addStretch()
        return w

    def create_setting_page(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        form = QFormLayout(inner)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题"])
        self.theme_combo.currentIndexChanged.connect(self.toggle_theme)

        font_spin = QSpinBox()
        font_spin.setRange(8, 32)
        font_spin.setValue(12)

        form.addRow("界面主题:", self.theme_combo)
        form.addRow("字体大小:", font_spin)
        form.addRow(QCheckBox("自动保存日志"))
        form.addRow(QCheckBox("自动重启脚本"))
        scroll.setWidget(inner)
        v = QVBoxLayout(w)
        v.addWidget(QLabel("🔧 设置"))
        v.addWidget(scroll)
        return w

    # --- 浅/深主题切换 ---
    def toggle_theme(self):
        if self.theme_combo.currentText() == "浅色主题":
            self.apply_light_theme()
        else:
            self.apply_dark_theme()

    def apply_light_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#f0f0f0"))
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Base, QColor("#ffffff"))
        palette.setColor(QPalette.AlternateBase, QColor("#f7f7f7"))
        palette.setColor(QPalette.ToolTipBase, Qt.black)
        palette.setColor(QPalette.ToolTipText, Qt.black)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.Button, QColor("#e0e0e0"))
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.Highlight, QColor("#0078D7"))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(palette)

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#2b2b2b"))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor("#3c3f41"))
        palette.setColor(QPalette.AlternateBase, QColor("#2b2b2b"))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor("#3c3f41"))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Highlight, QColor("#0078D7"))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(palette)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
