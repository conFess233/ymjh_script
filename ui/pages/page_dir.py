from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class PageDir(QWidget):
    """
    目录页面类，包含使用说明.
    """
    def __init__(self):
        super().__init__()
        self.v = QVBoxLayout(self)
        self.v.addWidget(QLabel("YMJH Script 使用说明"))
        self.v.addWidget(QLabel("1. 点击左侧“脚本执行”进入脚本控制页面。\n2. 在“设置”页可调整主题等参数。"))
        self.v.addStretch()
