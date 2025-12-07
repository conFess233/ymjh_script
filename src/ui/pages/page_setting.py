from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QComboBox, QCheckBox
from ..models.settings_model import SettingsModel
from ..core.logger import logger

class PageSetting(QWidget):
    """
    设置页面类，包含界面主题设置.
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
        self.settings_model = SettingsModel()

        # 创建主题选择下拉框，并设置当前主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题"])
        current_theme = self.settings_model.get_current_theme()
        self.theme_combo.setCurrentText("浅色主题" if current_theme == "light" else "深色主题")
        # 主题切换信号连接到应用主题方法
        self.theme_combo.currentIndexChanged.connect(self.apply_theme)

        self.auto_save_checkbox = QCheckBox()
        self.auto_save_checkbox.setChecked(self.settings_model.get_auto_save())
        self.auto_save_checkbox.stateChanged.connect(self.set_auto_save)

        # 将主题和字体控件添加到表单布局
        self.form.addRow("界面主题:", self.theme_combo)
        self.form.addRow("自动保存日志:", self.auto_save_checkbox)
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

    def set_auto_save(self, state):
        """
        设置自动保存日志.
        """
        self.settings_model.set_auto_save(state == 2)
        logger.set_auto_save(state == 2)