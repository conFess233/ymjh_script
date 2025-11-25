from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton, QSpinBox, QDoubleSpinBox, QGridLayout

class ScriptCfgWindow(QDialog):
    """
    脚本配置窗口类，包含基准窗口大小、默认模板匹配阈值、点击后的默认等待时间、捕获失败重试延迟、模板匹配失败重试延迟、最大模板匹配重试次数等配置项.
    """
    def __init__(self):
        # 调用父类的初始化方法
        super().__init__()
        # 设置窗口标题为“脚本配置”
        self.setWindowTitle("脚本配置")
        # 设置窗口初始大小为 250x150
        self.resize(250, 150)

        # 创建主布局，使用网格布局，并设置间距和边距
        self.main_layout = QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建“确定”按钮，并绑定点击事件为窗口接受
        btn = QPushButton("确定")
        btn.clicked.connect(self.accept)

        # 创建各项配置标签
        self.base_window_size = QLabel("基准窗口大小：")                           # 基准窗口大小，用于尺寸比例换算
        self.default_match_threshold = QLabel("默认模板匹配阈值(0.1-1.0):")        # 默认模板匹配阈值
        self.default_click_delay = QLabel("点击后的默认等待时间(秒):")              # 点击后的默认等待时间（秒）
        self.default_capture_retry_delay = QLabel("捕获失败重试延迟(秒):")          # 捕获失败重试延迟（秒）
        self.default_template_retry_delay = QLabel("模板匹配失败重试延迟(秒):")     # 模板匹配失败重试延迟（秒）
        self.default_max_retry_attempts = QLabel("最大模板匹配重试次数：")          # 最大模板匹配重试次数

        # 创建基准窗口宽度输入框，范围1-10000，步长100，默认2560
        self.bws_width_input = QSpinBox()
        self.bws_width_input.setRange(1, 10000)
        self.bws_width_input.setSingleStep(100)
        self.bws_width_input.setValue(2560)
        # 创建基准窗口高度输入框，范围1-10000，步长100，默认1440
        self.bws_height_input = QSpinBox()
        self.bws_height_input.setRange(1, 10000)
        self.bws_height_input.setSingleStep(100)
        self.bws_height_input.setValue(1440)

        # 创建默认模板匹配阈值输入框，范围0.1-1.0，步长0.1，默认0.6
        self.dmt_input = QDoubleSpinBox()
        self.dmt_input.setRange(0.1, 1.0)
        self.dmt_input.setSingleStep(0.1)
        self.dmt_input.setValue(0.6)

        # 创建点击后等待时间输入框，范围0-10，步长1，默认3
        self.dcd_input = QSpinBox()
        self.dcd_input.setRange(0, 10)
        self.dcd_input.setSingleStep(1)
        self.dcd_input.setValue(3)

        # 创建捕获失败重试延迟输入框，范围0-10，步长1，默认3
        self.dcrd_input = QSpinBox()
        self.dcrd_input.setRange(0, 10)
        self.dcrd_input.setSingleStep(1)
        self.dcrd_input.setValue(3)

        # 创建模板匹配失败重试延迟输入框，范围0-10，步长1，默认3
        self.dtrd_input = QSpinBox()
        self.dtrd_input.setRange(0, 10)
        self.dtrd_input.setSingleStep(1)
        self.dtrd_input.setValue(3)

        # 创建最大模板匹配重试次数输入框，范围0-10，步长1，默认3
        self.dmra_input = QSpinBox()
        self.dmra_input.setRange(0, 10)
        self.dmra_input.setSingleStep(1)
        self.dmra_input.setValue(3)

        # 将各控件添加到主布局的指定位置
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