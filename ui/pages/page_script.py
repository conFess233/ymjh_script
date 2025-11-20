from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QFormLayout, QSpinBox, QComboBox, QProgressBar, QTextEdit, QScrollArea, QListWidget, QHBoxLayout, QVBoxLayout, QDialog
from widgets.animated_button import AnimatedButton
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem
from models.script_model import ScriptModel
from widgets.task_list import TaskList
from widgets.script_cfg_window import ScriptCfgWindow
from core.logger import logger

class PageScript(QWidget):
    """
    脚本执行页面类，包含脚本运行列表，脚本设置、运行按钮、进度条、日志输出区域等.
    """
    def __init__(self):
        # 调用父类的初始化方法
        super().__init__()
        # 创建脚本数据模型
        self.model = ScriptModel(self)
        # 创建主网格布局，并设置间距和边距
        self.main_layout = QGridLayout(self)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        # 创建任务列表垂直布局
        self.slist_vbox = QVBoxLayout()
        # 创建左侧容器并设置宽度和布局
        self.container = QWidget()
        self.container.setFixedWidth(200)
        self.container.setLayout(self.slist_vbox)
        # 创建脚本配置网格布局，并设置间距和边距
        self.scfg_grid = QGridLayout()
        self.scfg_grid.setSpacing(15)
        self.scfg_grid.setContentsMargins(10, 10, 10, 10)

        # 创建任务列表控件
        self.task_list = TaskList("点击右侧“添加”按钮以添加任务")
        # 创建日志输出区域
        self.log_area = QTextEdit()
        self.log_area.setPlaceholderText("日志输出区域")
        self.log_area.setReadOnly(True)
        # 日志信号连接到日志追加方法
        logger.log_signal.connect(self.append_log)

        # 创建状态标签并设置样式
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-weight: bold; color: #2ecc71;")
        self.update_status()
        # 创建当前运行任务标签及内容标签，并设置样式
        self.running_task = QLabel("")
        self.running_task.setStyleSheet("font-weight: bold; color: #2ecc71;")
        # 创建当前窗口标签及内容标签，并设置样式
        self.window_title = QLabel("")
        self.window_title.setStyleSheet("font-weight: bold; color: #2ecc71;")

        # 创建进度条并设置高度和样式
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet("""
        QProgressBar {
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #3498db;
            width: 10px;
        }
""")

        # 创建“运行任务”、“脚本配置”、“添加”按钮，并设置点击事件
        self.run_btn = AnimatedButton("运行任务")
        self.script_cfg_btn = AnimatedButton("脚本配置")
        self.add_task_btn = AnimatedButton("添加")
            
        self.add_task_btn.clicked.connect(lambda: self.add_task())
        self.script_cfg_btn.clicked.connect(lambda: self.open_script_cfg())

        # 设置按钮宽度
        self.add_task_btn.setFixedWidth(100)
        self.script_cfg_btn.setFixedWidth(100)
        self.run_btn.setFixedWidth(100)

        # 创建脚本选择下拉框，并添加任务名
        self.script_box = QComboBox()
        self.script_box.addItems(self.model.get_task_names())
        self.script_box.setFixedWidth(200)

        # 设置任务列表宽度
        self.task_list.setFixedWidth(200)
        
        # 将任务列表控件添加到左侧垂直布局
        self.slist_vbox.addWidget(QLabel("任务列表"))
        self.slist_vbox.addWidget(self.task_list)
        # 将各控件添加到脚本配置网格布局的指定位置
        self.scfg_grid.addWidget(QLabel("添加任务到任务列表:"), 0, 0, 1, 1)
        self.scfg_grid.addWidget(self.script_box, 0, 1, 1, 1)
        self.scfg_grid.addWidget(self.add_task_btn, 0, 2, 1, 1)
        self.scfg_grid.addWidget(self.script_cfg_btn, 0, 3, 1, 1)
        self.scfg_grid.addWidget(self.run_btn, 0, 4, 1, 1)
        self.scfg_grid.addWidget(QLabel("当前窗口:"), 1, 0, 1, 1)
        self.scfg_grid.addWidget(self.window_title, 1, 1, 1, 1)
        self.scfg_grid.addWidget(QLabel("当前状态:"), 2, 0, 1, 1)
        self.scfg_grid.addWidget(self.status_label, 2, 1, 1, 1)
        self.scfg_grid.addWidget(QLabel("当前运行任务:"), 2, 2, 1, 1)
        self.scfg_grid.addWidget(self.running_task, 2, 3, 1, 1)
        self.scfg_grid.addWidget(self.progress_bar, 3, 0, 1, 5)

        self.scfg_grid.addWidget(QLabel("日志"), 4, 0, 1, 1)
        self.scfg_grid.addWidget(self.log_area, 5, 0, 1, 5)

        # 将左侧容器和脚本配置布局添加到主布局
        self.main_layout.addWidget(self.container, 0, 0)
        self.main_layout.addLayout(self.scfg_grid, 0, 1)


    def update_status(self):
        """
        更新当前状态标签.
        """
        self.status_label.setText(self.model.get_status())

    def add_task(self):
        """
        添加当前选中的脚本任务到任务列表.
        """
        task = self.script_box.currentText()
        if task:
            self.model.run_list.append(task)
            self.task_list.addItem(QListWidgetItem(task))
            logger.log(f"添加任务: {task}")
    
    def open_script_cfg(self):
        """
        打开脚本配置窗口.
        """
        cfg_window = ScriptCfgWindow()
        result = cfg_window.exec()
        if result == QDialog.DialogCode.Accepted:
            logger.log("脚本配置已更新")
            
    def append_log(self, text: str):
        """
        追加日志文本到日志区域.

        Args:
            text (str): 要追加的日志文本.
        """
        self.log_area.append(text)