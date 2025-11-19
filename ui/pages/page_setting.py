from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QSpinBox, QComboBox, QProgressBar, QTextEdit, QScrollArea, QCheckBox
from models.settings_model import SettingsModel

class PageSetting(QWidget):
    """
    设置页面类，包含界面主题、字体大小、自动保存日志、自动重启脚本等设置.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.v = QVBoxLayout(self)
        self.v.addWidget(QLabel("设置"))
        self.inner = QWidget()
        self.form = QFormLayout(self.inner)
        # 控制器
        self.settings_model = SettingsModel(main_window=self.main_window)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题"])
        current_theme = self.settings_model.get_current_theme()
        self.theme_combo.setCurrentText("浅色主题" if current_theme == "light" else "深色主题")
        self.theme_combo.currentIndexChanged.connect(self.apply_theme)

        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 32)
        self.font_spin.setValue(self.settings_model.get_current_font_size())
        self.font_spin.valueChanged.connect(
            lambda value: self.settings_model.set_current_font_size(value)
        )

        self.form.addRow("界面主题:", self.theme_combo)
        self.form.addRow("字体大小:", self.font_spin)
        self.v.addWidget(self.inner)
        self.v.addStretch()
        
    def apply_theme(self):
        # 切换主题
        if self.theme_combo.currentText() == "浅色主题":
            self.settings_model.apply_theme("light")
        else:
            self.settings_model.apply_theme("dark")