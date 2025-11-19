from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton, QSpinBox, QDoubleSpinBox, QGridLayout

class ScriptCfgWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("脚本配置")
        self.resize(250, 150)

        self.main_layout = QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        btn = QPushButton("确定")
        btn.clicked.connect(self.accept)

        self.base_window_size = QLabel("基准窗口大小：")                    # 基准窗口大小，用于尺寸比例换算
        self.default_match_threshold = QLabel("默认模板匹配阈值(0.1-1.0):")        # 默认模板匹配阈值
        self.default_click_delay = QLabel("点击后的默认等待时间(秒):")  # 点击后的默认等待时间（秒）
        self.default_capture_retry_delay = QLabel("捕获失败重试延迟(秒):") # 捕获失败重试延迟（秒）
        self.default_template_retry_delay = QLabel("模板匹配失败重试延迟(秒):") # 模板匹配失败重试延迟（秒）
        self.default_max_retry_attempts = QLabel("最大模板匹配重试次数：")  # 最大模板匹配重试次数

        self.bws_width_input = QSpinBox()
        self.bws_width_input.setRange(1, 10000)
        self.bws_width_input.setSingleStep(100)
        self.bws_width_input.setValue(2560)
        self.bws_height_input = QSpinBox()
        self.bws_height_input.setRange(1, 10000)
        self.bws_height_input.setSingleStep(100)
        self.bws_height_input.setValue(1440)

        self.dmt_input = QDoubleSpinBox()
        self.dmt_input.setRange(0.1, 1.0)
        self.dmt_input.setSingleStep(0.1)
        self.dmt_input.setValue(0.6)

        self.dcd_input = QSpinBox()
        self.dcd_input.setRange(0, 10)
        self.dcd_input.setSingleStep(1)
        self.dcd_input.setValue(3)

        self.dcrd_input = QSpinBox()
        self.dcrd_input.setRange(0, 10)
        self.dcrd_input.setSingleStep(1)
        self.dcrd_input.setValue(3)

        self.dtrd_input = QSpinBox()
        self.dtrd_input.setRange(0, 10)
        self.dtrd_input.setSingleStep(1)
        self.dtrd_input.setValue(3)

        self.dmra_input = QSpinBox()
        self.dmra_input.setRange(0, 10)
        self.dmra_input.setSingleStep(1)
        self.dmra_input.setValue(3)

        self.main_layout.addWidget(self.base_window_size, 0, 0)
        self.main_layout.addWidget(self.bws_width_input, 0, 1)
        self.main_layout.addWidget(self.bws_height_input, 0, 2)

        self.main_layout.addWidget(self.default_match_threshold, 1, 0)
        self.main_layout.addWidget(self.dmt_input, 1, 1, 1, 2)

        self.main_layout.addWidget(self.default_click_delay, 2, 0)
        self.main_layout.addWidget(self.dcd_input, 2, 1, 1, 2)

        self.main_layout.addWidget(self.default_capture_retry_delay, 3, 0)
        self.main_layout.addWidget(self.dcrd_input, 3, 1, 1, 2)

        self.main_layout.addWidget(self.default_template_retry_delay, 4, 0)
        self.main_layout.addWidget(self.dtrd_input, 4, 1, 1, 2)

        self.main_layout.addWidget(self.default_max_retry_attempts, 5, 0)
        self.main_layout.addWidget(self.dmra_input, 5, 1, 1, 2)

        self.main_layout.addWidget(btn, 6, 2)

        
