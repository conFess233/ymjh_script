from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QSpinBox, QDoubleSpinBox, QGridLayout, QLineEdit
from ..models.task_cfg_model import task_cfg_model

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
        accept_btn = QPushButton("确定")
        accept_btn.clicked.connect(self.apply_task_cfg)
        # 创建各项配置标签
        self.window_title = QLabel("目标窗口标题：")                        # 目标窗口标题
        self.base_window_size = QLabel("基准窗口大小：")                    # 基准窗口大小，用于尺寸比例换算
        self.match_threshold = QLabel("模板匹配阈值(0.1-1.0):")             # 模板匹配阈值
        self.click_delay = QLabel("点击后的等待时间(秒):")                  # 点击后的等待时间（秒）
        self.capture_retry_delay = QLabel("捕获失败重试延迟(秒):")          # 捕获失败重试延迟（秒）
        self.template_retry_delay = QLabel("模板匹配失败重试延迟(秒):")      # 模板匹配失败重试延迟（秒）
        self.match_loop_delay = QLabel("模板匹配循环等待时间(秒):")          # 模板匹配循环等待时间（秒）
        self.loop_count = QLabel("循环次数：")                              # 循环次数
        self.timeout = QLabel("任务超时时间(秒):")                          # 任务超时时间（秒）

        # 创建目标窗口标题输入框，默认"一梦江湖"
        self.window_title_input = QLineEdit()
        self.window_title_input.setText("一梦江湖")
        
        # 创建基准窗口宽度输入框，范围1-10000，步长10，默认2560
        self.bws_width_input = QSpinBox()
        self.bws_width_input.setRange(1, 10000)
        self.bws_width_input.setSingleStep(10)
        self.bws_width_input.setValue(2560)
        # 创建基准窗口高度输入框，范围1-10000，步长10，默认1440
        self.bws_height_input = QSpinBox()
        self.bws_height_input.setRange(1, 10000)
        self.bws_height_input.setSingleStep(10)
        self.bws_height_input.setValue(1440)

        # 创建默认模板匹配阈值输入框，范围0.1-1.0，步长0.1，默认0.6
        self.mt_input = QDoubleSpinBox()
        self.mt_input.setRange(0.1, 1.0)
        self.mt_input.setSingleStep(0.05)
        self.mt_input.setValue(0.6)

        # 创建点击后等待时间输入框，范围0.1-10.0，步长0.1，默认3.0
        self.cd_input = QDoubleSpinBox()
        self.cd_input.setRange(0.1, 10.0)
        self.cd_input.setSingleStep(0.5)
        self.cd_input.setValue(3.0)

        # 创建捕获失败重试延迟输入框，范围0.1-10.0，步长0.1，默认3.0
        self.crd_input = QDoubleSpinBox()
        self.crd_input.setRange(0.1, 10.0)
        self.crd_input.setSingleStep(0.5)
        self.crd_input.setValue(3.0)

        # 创建模板匹配失败重试延迟输入框，范围0.1-10.0，步长0.1，默认0.1
        self.trd_input = QDoubleSpinBox()
        self.trd_input.setRange(0.1, 10.0)
        self.trd_input.setSingleStep(0.1)
        self.trd_input.setValue(0.5)

        # 创建模板匹配循环等待时间输入框，范围0.1-10.0，步长0.1，默认1.0
        self.mld_input = QDoubleSpinBox()
        self.mld_input.setRange(0.1, 10.0)
        self.mld_input.setSingleStep(0.5)
        self.mld_input.setValue(2.0)

        # 创建循环次数输入框，范围1-10000，步长1，默认1
        self.loop_count_input = QSpinBox()
        self.loop_count_input.setRange(1, 10000)
        self.loop_count_input.setSingleStep(1)
        self.loop_count_input.setValue(1)

        # 创建任务超时时间输入框，范围1-10000，步长100，默认600
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(1, 10000)
        self.timeout_input.setSingleStep(10)
        self.timeout_input.setValue(600)

        # 将各控件添加到主布局的指定位置
        self.main_layout.addWidget(self.base_window_size, 0, 0)
        self.main_layout.addWidget(self.bws_width_input, 0, 1)
        self.main_layout.addWidget(self.bws_height_input, 0, 2)

        self.main_layout.addWidget(self.match_threshold, 1, 0)
        self.main_layout.addWidget(self.mt_input, 1, 1, 1, 2)

        self.main_layout.addWidget(self.click_delay, 2, 0)
        self.main_layout.addWidget(self.cd_input, 2, 1, 1, 2)

        self.main_layout.addWidget(self.capture_retry_delay, 3, 0)
        self.main_layout.addWidget(self.crd_input, 3, 1, 1, 2)

        self.main_layout.addWidget(self.template_retry_delay, 4, 0)
        self.main_layout.addWidget(self.trd_input, 4, 1, 1, 2)

        self.main_layout.addWidget(self.match_loop_delay, 5, 0)
        self.main_layout.addWidget(self.mld_input, 5, 1, 1, 2)

        self.main_layout.addWidget(self.loop_count, 6, 0)
        self.main_layout.addWidget(self.loop_count_input, 6, 1, 1, 2)

        self.main_layout.addWidget(self.timeout, 7, 0)
        self.main_layout.addWidget(self.timeout_input, 7, 1, 1, 2)

        self.main_layout.addWidget(self.window_title, 8, 0)
        self.main_layout.addWidget(self.window_title_input, 8, 1, 1, 2)

        self.main_layout.addWidget(accept_btn, 9, 2)

        self.load_task_cfg()


    def load_task_cfg(self):
        """
        从任务配置模型加载当前任务配置到输入框中.
        """
        task_cfg = task_cfg_model.get_task_cfg()
        self.window_title_input.setText(task_cfg["window_title"])
        self.bws_width_input.setValue(task_cfg["base_window_size"][0])
        self.bws_height_input.setValue(task_cfg["base_window_size"][1])
        self.mt_input.setValue(task_cfg["match_threshold"])
        self.cd_input.setValue(task_cfg["click_delay"])
        self.crd_input.setValue(task_cfg["capture_retry_delay"])
        self.trd_input.setValue(task_cfg["template_retry_delay"])
        self.mld_input.setValue(task_cfg["match_loop_delay"])
        self.loop_count_input.setValue(task_cfg["loop_count"])
        self.timeout_input.setValue(task_cfg["timeout"])
    
    def apply_task_cfg(self):
        """
        应用任务配置，将输入框中的值更新到任务配置模型中.
        """
        task_cfg_model.update_task_cfg({
            "window_title": self.window_title_input.text(),
            "base_window_size": (self.bws_width_input.value(), self.bws_height_input.value()),
            "match_threshold": self.mt_input.value(),
            "click_delay": self.cd_input.value(),
            "capture_retry_delay": self.crd_input.value(),
            "template_retry_delay": self.trd_input.value(),
            "match_loop_delay": self.mld_input.value(),
            "loop_count": self.loop_count_input.value(),
            "timeout": self.timeout_input.value(),
        })
        self.accept()
