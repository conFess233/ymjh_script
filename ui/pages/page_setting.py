from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QSpinBox, QComboBox, QProgressBar, QTextEdit, QScrollArea, QCheckBox
from models.settings_model import SettingsModel

class PageSetting(QWidget):
    """
    设置页面类，包含界面主题、字体大小、自动保存日志、自动重启脚本等设置.
    """
    def __init__(self, main_window):
        # 调用父类的初始化方法
        super().__init__()
        # 保存主窗口引用
        self.main_window = main_window
        # 创建主垂直布局，并添加“设置”标签
        self.v = QVBoxLayout(self)
        self.v.addWidget(QLabel("设置"))
        # 创建内部 QWidget 及表单布局
        self.inner = QWidget()
        self.form = QFormLayout(self.inner)
        # 创建设置数据模型（控制器）
        self.settings_model = SettingsModel(main_window=self.main_window)

        # 创建主题选择下拉框，并设置当前主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题"])
        current_theme = self.settings_model.get_current_theme()
        self.theme_combo.setCurrentText("浅色主题" if current_theme == "light" else "深色主题")
        # 主题切换信号连接到应用主题方法
        self.theme_combo.currentIndexChanged.connect(self.apply_theme)

        # 创建字体大小选择框，并设置范围和当前值
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 32)
        self.font_spin.setValue(self.settings_model.get_current_font_size())
        # 字体大小变化信号连接到设置字体大小方法
        self.font_spin.valueChanged.connect(
            lambda value: self.settings_model.set_current_font_size(value)
        )

        # 将主题和字体控件添加到表单布局
        self.form.addRow("界面主题:", self.theme_combo)
        self.form.addRow("字体大小:", self.font_spin)
        # 将表单布局和弹性空间添加到主布局
        self.v.addWidget(self.inner)
        self.v.addStretch()
        
    def apply_theme(self):
        """
        应用当前设置的主题.
        """
        if self.theme_combo.currentText() == "浅色主题":
            self.settings_model.apply_theme("light")
        else:
            self.settings_model.apply_theme("dark")