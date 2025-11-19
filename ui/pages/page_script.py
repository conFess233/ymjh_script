from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QFormLayout, QSpinBox, QComboBox, QProgressBar, QTextEdit, QScrollArea, QListWidget, QHBoxLayout, QVBoxLayout, QDialog
from widgets.animated_button import AnimatedButton
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem
from models.script_model import ScriptModel
from widgets.task_list import TaskList
from widgets.script_cfg_window import ScriptCfgWindow
class PageScript(QWidget):
    """
    脚本执行页面类，包含脚本运行列表，脚本设置、运行按钮、进度条、日志输出区域等.
    """
    def __init__(self):
        super().__init__()
        self.model = ScriptModel(self)
        self.main_layout = QGridLayout(self)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.slist_vbox = QVBoxLayout()
        self.container = QWidget()
        self.container.setFixedWidth(200)
        self.container.setLayout(self.slist_vbox)
        self.scfg_grid = QGridLayout()
        self.scfg_grid.setSpacing(15)
        self.scfg_grid.setContentsMargins(10, 10, 10, 10)

        self.task_list = TaskList()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        self.status_label = QLabel("未运行")
        self.status_label.setStyleSheet("font-weight: bold; color: #2ecc71;")
        self.running_task_label = QLabel("当前运行任务:")
        self.running_task_label.setStyleSheet("font-weight: bold; color: #2ecc71;")
        self.running_task = QLabel("")
        self.running_task.setStyleSheet("font-weight: bold; color: #2ecc71;")

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

        self.run_btn = AnimatedButton("运行任务")
        self.script_cfg_btn = AnimatedButton("脚本配置")
        self.add_task_btn = AnimatedButton("添加")
            
        self.add_task_btn.clicked.connect(lambda: self.add_task())
        self.script_cfg_btn.clicked.connect(lambda: self.open_script_cfg())

        self.add_task_btn.setFixedWidth(100)
        self.script_cfg_btn.setFixedWidth(100)
        self.run_btn.setFixedWidth(100)

        self.script_box = QComboBox()
        self.script_box.addItems(self.model.get_task_names())
        self.script_box.setFixedWidth(200)

        self.task_list.setFixedWidth(200)
        
        self.slist_vbox.addWidget(QLabel("任务列表"))
        self.slist_vbox.addWidget(self.task_list)
        self.scfg_grid.addWidget(QLabel("添加任务到任务列表:"), 0, 0, 1, 1)
        self.scfg_grid.addWidget(self.script_box, 0, 1, 1, 1)
        self.scfg_grid.addWidget(self.add_task_btn, 0, 2, 1, 1)
        self.scfg_grid.addWidget(self.script_cfg_btn, 0, 3, 1, 1)
        self.scfg_grid.addWidget(self.run_btn, 0, 4, 1, 1)
        self.scfg_grid.addWidget(QLabel("当前状态:"), 1, 0, 1, 1)
        self.scfg_grid.addWidget(self.status_label, 1, 1, 1, 1)
        self.scfg_grid.addWidget(self.running_task_label, 1, 2, 1, 1)
        self.scfg_grid.addWidget(self.running_task, 1, 3, 1, 1)
        self.scfg_grid.addWidget(self.progress_bar, 2, 0, 1, 5)


        self.scfg_grid.addWidget(QLabel("日志"), 3, 0, 1, 1)
        self.scfg_grid.addWidget(self.log_area, 4, 0, 1, 5)

        self.main_layout.addWidget(self.container, 0, 0)
        self.main_layout.addLayout(self.scfg_grid, 0, 1)


    def update_status(self):
        self.status_label.setText(self.model.get_status())

    def add_task(self):
        task = self.script_box.currentText()
        if task:
            self.model.run_list.append(task)
            self.task_list.addItem(QListWidgetItem(task))
    
    def open_script_cfg(self):
        cfg_window = ScriptCfgWindow()
        result = cfg_window.exec()
        if result == QDialog.DialogCode.Accepted:
            print("用户点击了确定")