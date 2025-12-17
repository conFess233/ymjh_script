from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QProgressBar, QTextEdit, QVBoxLayout, QPushButton
from PySide6.QtGui import QColor, QBrush, QTextCursor
from PySide6.QtCore import Qt
from ..models.task_model import TaskModel
from ..widgets.task_list import TaskList
from .script_cfg_window import ScriptCfgWindow
from ..core.logger import logger
from ..core.theme_manager import theme_manager

class PageScript(QWidget):
    """
    任务执行页面类，包含任务运行列表，任务设置、运行按钮、进度条、日志输出区域等.
    """
    def __init__(self):
        # 调用父类的初始化方法
        super().__init__()
        # 创建任务数据模型
        self.model = TaskModel()
        # 创建主网格布局，并设置间距和边距
        self.main_layout = QGridLayout(self)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        # 创建任务列表垂直布局
        self.slist_vbox = QVBoxLayout()
        # 创建左侧容器并设置宽度和布局
        self.container = QWidget()
        self.container.setFixedWidth(210)
        self.container.setLayout(self.slist_vbox)
        # 创建脚本配置网格布局，并设置间距和边距
        self.scfg_grid = QGridLayout()
        self.scfg_grid.setSpacing(15)
        self.scfg_grid.setContentsMargins(10, 10, 10, 10)

        # 创建任务列表控件
        self.task_list = TaskList(self.model, "点击右侧“添加”按钮以添加任务")
        # 创建日志输出区域
        self.log_area = QTextEdit()
        self.log_area.setPlaceholderText("日志输出区域")
        self.log_area.setReadOnly(True)
        self.log_area.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)

        # 创建状态标签并设置样式
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-weight: bold; color: #2ecc71;")
        self.update_status()

        # 创建当前运行任务标签及内容标签，并设置样式
        self.running_task = QLabel("")
        self.running_task.setStyleSheet("font-weight: bold; color: #2ecc71;")

        # 创建当前窗口标签及内容标签，并设置样式
        self.window_title = QLabel("无")
        self.window_title.setStyleSheet("font-weight: bold; color: #2ecc71;")

        # 创建进度条并设置高度和样式
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(10)

        # 创建“运行任务”、“脚本配置”、“添加”按钮，并设置点击事件
        self.run_btn = QPushButton("开始运行")
        self.script_cfg_btn = QPushButton("脚本配置")
        self.add_task_btn = QPushButton("添加")
        self.find_window_btn = QPushButton("查找窗口")
        self.connect_window_btn = QPushButton("连接窗口")
        self.show_window_btn = QPushButton("显示窗口")
        self.clear_run_list_btn = QPushButton("清空列表")
        self.pause_btn = QPushButton("暂停任务")

        # 设置按钮宽度
        self.find_window_btn.setFixedWidth(100)
        self.add_task_btn.setFixedWidth(100)
        self.script_cfg_btn.setFixedWidth(100)
        self.run_btn.setFixedWidth(100)
        self.connect_window_btn.setFixedWidth(100)
        self.show_window_btn.setFixedWidth(100)
        self.pause_btn.setFixedWidth(100)

        # 按钮初始状态
        self.pause_btn.setEnabled(False)

        # 创建脚本选择下拉框，并添加任务名
        self.task_box = QComboBox()
        self.task_box.addItems(self.model.get_task_names())
        self.task_box.setFixedWidth(200)
        self.hwnd_box = QComboBox()
        self.hwnd_box.setFixedWidth(200)
        self.hwnd_box.addItem("无")

        # 设置任务列表宽度
        self.task_list.setFixedWidth(200)
        self.clear_run_list_btn.setFixedWidth(200)
        
        # 将任务列表控件添加到左侧垂直布局
        self.slist_vbox.addWidget(QLabel("任务列表"))
        self.slist_vbox.addWidget(self.task_list)
        self.slist_vbox.addWidget(self.clear_run_list_btn)
        # 将各控件添加到脚本配置网格布局的指定位置
        self.scfg_grid.addWidget(QLabel("添加任务到任务列表:"), 0, 0, 1, 1)
        self.scfg_grid.addWidget(self.task_box, 0, 1, 1, 1)
        self.scfg_grid.addWidget(self.add_task_btn, 0, 2, 1, 1)
        self.scfg_grid.addWidget(self.script_cfg_btn, 0, 3, 1, 1)
        self.scfg_grid.addWidget(self.run_btn, 0, 4, 1, 1)
        self.scfg_grid.addWidget(QLabel("当前连接窗口:"), 1, 0, 1, 1)
        self.scfg_grid.addWidget(self.window_title, 1, 1, 1, 1)
        self.scfg_grid.addWidget(self.pause_btn, 1, 4, 1, 1)
        self.scfg_grid.addWidget(QLabel("窗口句柄:"), 2, 0, 1, 1)
        self.scfg_grid.addWidget(self.hwnd_box, 2, 1, 1, 1)
        self.scfg_grid.addWidget(self.find_window_btn, 2, 2, 1, 1)
        self.scfg_grid.addWidget(self.connect_window_btn, 2, 3, 1, 1)
        self.scfg_grid.addWidget(self.show_window_btn, 2, 4, 1, 1)
        self.scfg_grid.addWidget(QLabel("当前状态:"), 3, 0, 1, 1)
        self.scfg_grid.addWidget(self.status_label, 3, 1, 1, 1)
        self.scfg_grid.addWidget(QLabel("当前运行任务:"), 3, 2, 1, 1)
        self.scfg_grid.addWidget(self.running_task, 3, 3, 1, 1)
        self.scfg_grid.addWidget(self.progress_bar, 4, 0, 1, 5)
        self.scfg_grid.addWidget(QLabel("日志"), 5, 0, 1, 1)
        self.scfg_grid.addWidget(self.log_area, 6, 0, 1, 5)

        # 将左侧容器和脚本配置布局添加到主布局
        self.main_layout.addWidget(self.container, 0, 0)
        self.main_layout.addLayout(self.scfg_grid, 0, 1)

        self._setup_connections() # 连接信号与槽

    def update_status(self):
        """
        更新当前状态标签.
        """
        self.status_label.setText(self.model.get_status())
    
    def open_script_cfg(self):
        """
        打开脚本配置窗口.
        """
        cfg_window = ScriptCfgWindow(self)
        cfg_window.exec()
            
    def get_color_for_type(self, log_type: str) -> str:
        """
        根据日志类型返回对应的 HTML 颜色字符串。
        """
        if log_type == "ERROR":
            # 红色
            return "red"
        elif log_type == "WARN":
            # 橙色
            return "orange"
        elif log_type == "INFO":
            # 默认颜色
            if theme_manager.is_dark_theme():
                return "white"
            else:
                return "black"
        else:
            # 其他类型或默认颜色
            return "black"

    def display_log_message(self, message: str, log_type: str):
        """
        接收日志并以不同的颜色显示。
        """
        color = self.get_color_for_type(log_type)
        # 使用 HTML 格式化文本
        html_message = f'<span style="color: {color};">{message}</span>'
        # 将 HTML 文本追加到 QTextEdit
        self.log_area.append(html_message)

        # 限制最大显示块数，防止内存溢出
        if self.log_area.document().blockCount() > 500:
            cursor = self.log_area.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar() # 删除换行符
        # 滚动到底部
        self.log_area.ensureCursorVisible()

    
    def _setup_connections(self):
        """
        连接所有信号与槽.
        """
        # 连接运行按钮到切换运行状态的方法
        self.run_btn.clicked.connect(self._toggle_run_queue)
        
        # 连接 Model 的状态变化信号到 UI 更新方法
        self.model.status_changed.connect(self.update_run_button_state)
        self.model.queue_paused_changed.connect(self._update_pause_button_state)
        
        # 其他信号连接，如更新状态标签、日志等
        self.model.status_changed.connect(self.update_status)
        self.model.progress_changed.connect(self.progress_bar.setValue)
        self.model.running_task_changed.connect(self.set_running_task)
        self.model.connect_window_changed.connect(self.window_title.setText)
        self.add_task_btn.clicked.connect(lambda: self.model.add_task(self.task_box.currentText()))
        self.script_cfg_btn.clicked.connect(lambda: self.open_script_cfg())
        self.find_window_btn.clicked.connect(lambda: self.get_window_handles())
        self.connect_window_btn.clicked.connect(lambda: self.connect_window())
        self.show_window_btn.clicked.connect(lambda: self.show_window(self.get_current_hwnd()))
        self.clear_run_list_btn.clicked.connect(lambda: self.model.clear_run_list())
        self.pause_btn.clicked.connect(lambda: self._toggle_pause_task())
        logger.log_signal.connect(self.display_log_message)


    def get_window_handles(self):
        """
        获取当前所有窗口的句柄并更新下拉框。
        """
        handles = self.model.get_target_window_handles(self.model.window_title)
        self.hwnd_box.clear()
        self.hwnd_box.addItems([str(hwnd) for hwnd in handles])

    def connect_window(self):
        """
        连接到当前选中的窗口句柄。
        """
        if self.hwnd_box.currentText() == "无" or self.hwnd_box.currentText() == "":
            logger.error("请选择一个窗口句柄！")
            return
        self.model.set_hwnd(int(self.hwnd_box.currentText()))
        self.model.connect_window()
    
    def show_window(self, hwnd: int = 0):
        """
        显示当前连接的窗口.
        """
        import win32gui
        import win32con
        try:
            win32gui.SetForegroundWindow(hwnd)

            # 如果窗口最小化，需要先还原它才能带到最前
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # 再次确保它被激活
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            logger.error(f"显示窗口失败，句柄：{hwnd}，{e}")
            return

    def get_current_hwnd(self) -> int:
        """
        获取当前选中的窗口句柄.
        """
        if self.hwnd_box.currentText() == "无" or self.hwnd_box.currentText() == "":
            logger.error("请选择一个窗口句柄！")
            return 0
        try:
            hwnd = int(self.hwnd_box.currentText())
        except ValueError:
            logger.error("当前选中的窗口句柄无效！")
            return 0
        return hwnd
    
    # 处理运行按钮的点击
    def _toggle_run_queue(self):
        """
        根据当前状态切换运行/停止任务队列。
        """
        if self.model.is_queue_running():
            self.model.stop_queue()
        else:
            self.model.start_queue()

    def _toggle_pause_task(self):
        """
        暂停当前运行的任务队列。
        """
        if self.model.is_queue_paused():
            self.model.resume_queue()
        else:
            self.model.pause_queue()

    def update_run_button_state(self, status: str):
        """
        根据 TaskModel 发出的状态信号更新运行按钮的文本和样式。
        """
        # 1. 按钮文本和功能切换
        if status == "运行中" or status == "已暂停":
            self.run_btn.setText("停止运行")
            self.add_task_btn.setEnabled(False) 
            self.task_list.setEnabled(False)
            self.connect_window_btn.setEnabled(False)
            self.script_cfg_btn.setEnabled(False)
            self.find_window_btn.setEnabled(False)
            self.clear_run_list_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
        else: # "未运行", "队列已完成", "发生错误"
            self.run_btn.setText("开始运行")
            self.add_task_btn.setEnabled(True) 
            self.task_list.setEnabled(True)
            self.connect_window_btn.setEnabled(True)
            self.script_cfg_btn.setEnabled(True)
            self.find_window_btn.setEnabled(True)
            self.clear_run_list_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
    
    def _update_pause_button_state(self, is_paused: bool):
        """
        根据任务队列是否暂停更新暂停按钮的文本和样式。
        """
        if is_paused:
            self.pause_btn.setText("继续任务")
        else:
            self.pause_btn.setText("暂停任务")
    
    def set_running_task(self, task_name: str, index: int):
        """
        设置当前运行任务的显示文本.
        """
        if task_name:
            self.running_task.setText(task_name)
            for i in range(self.task_list.count()):
                item = self.task_list.item(i)
                if item.text() == task_name:
                    item.setForeground(QBrush(QColor("orange")))
                    break
                else:
                    item.setForeground(QBrush(QColor("black")))
        else:
            self.running_task.setText("无")