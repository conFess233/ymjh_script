from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QSpinBox, QComboBox, QProgressBar, QTextEdit, QScrollArea, QCheckBox
from widgets.animated_button import AnimatedButton

class PageScript(QWidget):
    """
    脚本执行页面类，包含运行时间、运行模式、运行按钮、进度条、日志输出区域等.
    """
    def __init__(self):
        super().__init__()
        self.v = QVBoxLayout(self)
        self.v.addWidget(QLabel("脚本执行区域"))
        self.form = QFormLayout()
        self.time_spin = QSpinBox()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["普通模式", "快速模式", "安全模式"])
        self.run_btn = AnimatedButton("运行脚本")
        self.run_btn.setStyleSheet("""
    QPushButton {
        background-color: #3498db;
        border: none;
        border-radius: 12px;
        padding: 8px 16px;
        color: white;
    }
    QPushButton:hover {
        background-color: #2980b9;
    }
    QPushButton:pressed {
        background-color: #2471a3;
    }
""")
        self.form.addRow("运行时间（秒）:", self.time_spin)
        self.form.addRow("运行模式:", self.mode_combo)
        self.form.addRow(self.run_btn)
        
        self.v.addLayout(self.form)
        self.v.addWidget(QProgressBar())
        self.v.addWidget(QTextEdit("脚本日志输出区域"))
        self.v.addStretch()
