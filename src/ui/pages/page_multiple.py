
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox, QGridLayout, QTextEdit, QTableView, QHeaderView, QAbstractItemView
)
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import QTimer, Qt
from src.ui.core.logger import logger
from src.ui.core.mutiple_manager import MultipleProcessManager
from ..widgets.task_list import MultipleTaskList
from ..widgets.multiple_table_model import MultipleTableModel
from ..core.theme_manager import theme_manager
from .script_cfg_window import ScriptCfgWindow
from ..core.process_item import ProcessItem

class PageMultiple(QWidget):
    """
    多开页面，用于管理多个窗口任务
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = MultipleProcessManager()
        self.initial_tasks = []
        self.log_mode = 3

        self._setup_ui()
        self._setup_connections()


    def _setup_ui(self):
        """
        设置用户界面
        """
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

        # 创建操作布局
        self.operation_layout = QGridLayout()
        self.operation_layout.setSpacing(15)
        self.operation_layout.setContentsMargins(10, 10, 10, 10)

        # 按钮
        self.add_task_btn = QPushButton("添加任务")
        self.clear_task_btn = QPushButton("清空任务")
        self.remove_process_btn = QPushButton("移除选中")
        self.clear_btn = QPushButton("一键清空")
        self.refresh_button = QPushButton("刷新窗口列表")
        self.show_window_button =QPushButton("显示窗口")
        self.control_button = QPushButton("启动选中") 
        self.all_run_btn = QPushButton("全部启动")
        self.all_stop_btn = QPushButton("全部停止")
        self.pause_btn = QPushButton("暂停选中")
        self.resume_btn = QPushButton("恢复选中")
        self.pause_all_btn = QPushButton("暂停全部")
        self.resume_all_btn = QPushButton("恢复全部")
        self.change_task_btn = QPushButton("更新任务列表")
        self.change_task_cfg_btn = QPushButton("修改任务配置")
        self.add_process_btn = QPushButton("添加到列表")

        # 任务选择框
        self.task_box = QComboBox()
        self.task_box.setPlaceholderText("选择任务")
        self.task_box.addItems(["日常副本", "论剑"])
        self.task_box.setCurrentIndex(0)
        # 句柄选择框
        self.handle_box = QComboBox()
        self.handle_box.setPlaceholderText("选择句柄")
        self.handle_box.setFixedWidth(100)
        
        # 进程名称输入框
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("在这里输入任意进程名称(如 小号1)")

        # 窗口标题输入框
        self.window_title = QLineEdit("一梦江湖")
        self.window_title.setPlaceholderText("输入目标窗口标题")
        
        # 按钮设置
        # 大小
        self.add_process_btn.setFixedWidth(100)
        self.remove_process_btn.setFixedWidth(100)
        self.remove_process_btn.setEnabled(False)
        self.clear_btn.setFixedWidth(100)
        self.refresh_button.setFixedWidth(100)
        self.show_window_button.setFixedWidth(100)

        # 初始状态
        self.control_button.setEnabled(False)
        self.remove_process_btn.setEnabled(False)
        self.all_run_btn.setEnabled(False)
        self.all_stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.pause_all_btn.setEnabled(False)
        self.resume_all_btn.setEnabled(False)
        self.change_task_btn.setEnabled(False)
        
        # 日志显示区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("日志输出区域")
        self.log_area.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)

        # 进程列表
        self.process_view = QTableView()
        self.table_model = MultipleTableModel(self.initial_tasks)
        self.process_view.setModel(self.table_model)
        self.process_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.process_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.process_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # 操作按钮布局
        self.op_hbox_layout = QHBoxLayout()
        self.op_hbox_layout.addWidget(self.pause_all_btn)
        self.op_hbox_layout.addWidget(self.resume_all_btn)
        self.op_hbox_layout.addWidget(self.pause_btn)
        self.op_hbox_layout.addWidget(self.resume_btn)
        self.op_hbox_layout.addWidget(self.all_stop_btn)
        self.op_hbox_layout.addWidget(self.all_run_btn)
        self.op_hbox_layout.addWidget(self.control_button)

        # 添加到布局
        self.operation_layout.addWidget(QLabel("进程列表"), 0, 0, 1, 1)
        self.operation_layout.addWidget(QLabel("进程名称:"), 1, 0, 1, 1)
        self.operation_layout.addWidget(self.name_input, 1, 1, 1, 1)
        self.operation_layout.addWidget(self.add_process_btn, 1, 2, 1, 1)
        self.operation_layout.addWidget(self.remove_process_btn, 1, 3, 1, 1)
        self.operation_layout.addWidget(self.clear_btn, 1, 4, 1, 1)
        self.operation_layout.addWidget(QLabel("窗口名称:"), 2, 0, 1, 1)
        self.operation_layout.addWidget(self.window_title, 2, 1, 1, 1)
        self.operation_layout.addWidget(self.handle_box, 2, 2, 1, 1)
        self.operation_layout.addWidget(self.refresh_button, 2, 3, 1, 1)
        self.operation_layout.addWidget(self.show_window_button, 2, 4, 1, 1)
        self.operation_layout.addWidget(self.process_view, 3, 0, 1, 5)
        self.operation_layout.addLayout(self.op_hbox_layout, 4, 0, 1, 5)
        self.operation_layout.addWidget(QLabel("日志"), 5, 0, 1, 1)
        self.operation_layout.addWidget(self.log_area, 6, 0, 1, 5)

        # 任务列表
        self.task_list = MultipleTaskList("任务列表")
        self.slist_vbox.addWidget(QLabel("任务列表"))
        self.slist_vbox.addWidget(self.task_list)
        self.slist_vbox.addWidget(self.change_task_btn)
        self.slist_vbox.addWidget(self.clear_task_btn)
        self.slist_vbox.addWidget(self.task_box)
        self.slist_vbox.addWidget(self.add_task_btn)
        self.slist_vbox.addWidget(self.change_task_cfg_btn)

        # 添加到主布局
        self.main_layout.addWidget(self.container, 0, 0)
        self.main_layout.addLayout(self.operation_layout, 0, 1)

    def _setup_connections(self):
        """
        连接信号和槽
        """
        self.add_process_btn.clicked.connect(lambda: self.add_process())
        self.remove_process_btn.clicked.connect(lambda: self.remove_process())
        self.refresh_button.clicked.connect(lambda: self.refresh_handle_box())
        self.show_window_button.clicked.connect(lambda: self.show_window())
        self.manager.process_item_changed.connect(self._refresh_process_view)
        self.control_button.clicked.connect(lambda: self.control_process())
        self.process_view.selectionModel().selectionChanged.connect(self._update_widget_status)
        self.all_run_btn.clicked.connect(lambda: self.run_all_processes())
        self.all_stop_btn.clicked.connect(lambda: self.stop_all_processes())
        self.pause_all_btn.clicked.connect(lambda: self.pause_all_processes())
        self.resume_all_btn.clicked.connect(lambda: self.resume_all_processes())
        self.pause_btn.clicked.connect(lambda: self.pause_process())
        self.resume_btn.clicked.connect(lambda: self.resume_process())
        self.add_task_btn.clicked.connect(lambda: self.add_task_to_list())
        self.clear_btn.clicked.connect(lambda: self.manager.clear_items())
        self.table_model.data_changed_signal.connect(self._update_button_status)
        self.clear_task_btn.clicked.connect(lambda: self.task_list.clear())
        self.change_task_cfg_btn.clicked.connect(self.open_script_cfg)
        self.change_task_btn.clicked.connect(lambda: self.on_task_list_modified())
        self.manager.task_status_changed.connect(self.handle__status_cache_update)
        logger.log_multiprocess_signal.connect(self.display_log_message)

# --- 辅助方法 ---
    def show_window(self):
        """
        显示当前连接的窗口.
        """
        import win32gui
        import win32con
        handle = int(self.handle_box.currentText()) if self.handle_box.currentText() else 0
        if not handle:
            logger.error("未选择任何进程", mode=self.log_mode)
            return
        try:
            win32gui.SetForegroundWindow(handle)

            # 如果窗口最小化，需要先还原它才能带到最前
            if win32gui.IsIconic(handle):
                win32gui.ShowWindow(handle, win32con.SW_RESTORE)

            # 再次确保它被激活
            win32gui.SetForegroundWindow(handle)
        except Exception as e:
            logger.error(f"显示窗口失败，句柄：{handle}，{e}", mode=self.log_mode)
            return
        
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
            return "black" # 其他类型默认颜色为黑色

    def get_current_handle(self) -> int | None:
        """
        获取当前选中进程的句柄

        Returns:
            handle(int | None): 当前选中进程的句柄，如果未选中或句柄无效则返回 None。
        """
        selected_index = self.table_model.get_selected_row_index(self.process_view)
        if selected_index == None or selected_index == -1:
            return None
        
        handle = self.table_model.get_data(selected_index)["handle"] # type: ignore
        if not handle: 
            return None
        
        return handle

# --- 槽函数 ---
    def handle__status_cache_update(self, handle: int, status_dict: dict):
        """
        接收并处理 TaskModel 的详细状态更新。
        """

        current_task = status_dict.get("current_task", "N/A")
        progress = status_dict.get("progress", 0)
        overall_status = status_dict.get("overall_status", "N/A")
        
        status = {
            "current_run": current_task,
            "progress": progress,
            "status": overall_status
        }
        self._refresh_process_status(handle, status)

    def _update_widget_status(self):
        """
        更新组件状态
        """
        self._update_button_status()
        QTimer.singleShot(50, self.refresh_task_list)
        
        handle = self.get_current_handle()
        self.handle_box.setCurrentText(str(handle))

    def run_all_processes(self):
        """
        运行所有进程
        """
        for item in self.manager.get_all_items().values():
            if item._status_cache["overall_status"] == "已停止" or item._status_cache["overall_status"] == "未运行":
                item.start_process()

    def stop_all_processes(self):
        """
        停止所有进程
        """
        for item in self.manager.get_all_items().values():
            if item._status_cache["overall_status"] == "运行中" or item._status_cache["overall_status"] == "已暂停":
                item.stop_process()
    
    def pause_all_processes(self):
        """
        暂停所有进程
        """
        for item in self.manager.get_all_items().values():
            if item._status_cache["overall_status"] == "运行中":
                item.pause_process()

    def resume_all_processes(self):
        """
        恢复所有进程
        """
        for item in self.manager.get_all_items().values():
            if item._status_cache["overall_status"] == "已暂停":
                item.resume_process()

    def pause_process(self):
        """
        暂停当前选中进程
        """
        handle = self.get_current_handle()
        if not handle:
            logger.warning("未选择任何进程。", mode=self.log_mode)
            return
        
        item = self.manager.get_item(handle)
        if item:
            item.pause_process()
        else:
            logger.warning(f"未找到句柄 {handle} 对应的进程。", mode=self.log_mode)

    def resume_process(self):
        """
        恢复当前选中进程
        """
        handle = self.get_current_handle()
        if not handle:
            logger.warning("未选择任何进程。", mode=self.log_mode)
            return
        
        item = self.manager.get_item(handle)
        if item:
            item.resume_process()
        else:
            logger.warning(f"未找到句柄 {handle} 对应的进程。", mode=self.log_mode)

    def open_script_cfg(self):
        """
        打开脚本配置窗口.
        """
        cfg_window = ScriptCfgWindow(self)
        cfg_window.exec()

    def on_task_list_modified(self):
        """
        当任务列表被用户修改时，将新列表发送回 Manager 和子进程。
        """
        # 获取当前选中的句柄
        handle = self.get_current_handle()
        if not handle:
            logger.warning("未选择任何进程。", mode=self.log_mode)
            return
        

        tasks = self.task_list.get_all_items()
        # 发送新列表给 Manager
        self.manager.set_process_task_list(handle, tasks)

    def refresh_task_list(self):
        """
        刷新当前选中进程的任务列表.
        """
        handle = self.get_current_handle()
        if not handle:
            # logger.warning("未选择任何进程。", mode=self.log_mode)
            return

        tasks = self.manager.get_process_task_list(handle)
        if not tasks:
            logger.warning("任务列表为空", mode=self.log_mode)
            self.task_list.clear_list()
            return

        self.task_list.set_list(tasks)
        logger.info("任务列表已刷新", mode=1)

    def _update_button_status(self):
        """
        根据选择更新按钮状态
        """
        is_no_item = self.table_model.rowCount() == 0
        if not is_no_item:
            self.all_run_btn.setEnabled(True)
            self.all_stop_btn.setEnabled(True)
            self.pause_all_btn.setEnabled(True)
            self.resume_all_btn.setEnabled(True)
            selected = self.table_model.get_selected_row_index(self.process_view)
            if selected == None or selected == -1:
                self.control_button.setEnabled(False)
                self.remove_process_btn.setEnabled(False)
                self.pause_btn.setEnabled(False)
                self.resume_btn.setEnabled(False)
            else:
                handle = self.table_model.get_data(selected)["handle"] # type: ignore
                item = self.manager.get_item(handle)
                if not item:
                    self.control_button.setEnabled(False)
                    self.remove_process_btn.setEnabled(False)
                    self.pause_btn.setEnabled(False)
                    self.resume_btn.setEnabled(False)
                    self.all_run_btn.setEnabled(False)
                    self.all_stop_btn.setEnabled(False)
                    self.pause_all_btn.setEnabled(False)
                    self.resume_all_btn.setEnabled(False)
                    logger.error(f"未找到窗口句柄为 {handle} 的进程项", mode=self.log_mode)
                    return
                
                if item._status_cache["overall_status"] == "运行中":
                    self.control_button.setText("停止选中")
                    self.pause_btn.setEnabled(True)
                    self.add_task_btn.setEnabled(False)
                    self.clear_task_btn.setEnabled(False)
                    self.task_list.setEnabled(False)
                    self.resume_btn.setEnabled(False)
                    self.change_task_btn.setEnabled(False)
                elif item._status_cache["overall_status"] == "已暂停":
                    self.pause_btn.setEnabled(False)
                    self.add_task_btn.setEnabled(False)
                    self.clear_task_btn.setEnabled(False)
                    self.task_list.setEnabled(False)
                    self.resume_btn.setEnabled(True)
                    self.change_task_btn.setEnabled(False)
                else:
                    self.control_button.setText("启动选中")
                    self.pause_btn.setEnabled(False)
                    self.add_task_btn.setEnabled(True)
                    self.clear_task_btn.setEnabled(True)
                    self.task_list.setEnabled(True)
                    self.resume_btn.setEnabled(False)
                    self.change_task_btn.setEnabled(True)

                self.control_button.setEnabled(True)
                self.remove_process_btn.setEnabled(True)
        else:
            self.all_run_btn.setEnabled(False)
            self.all_stop_btn.setEnabled(False)
            self.pause_all_btn.setEnabled(False)
            self.resume_all_btn.setEnabled(False)
            self.control_button.setEnabled(False)
            self.remove_process_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.add_task_btn.setEnabled(True)
            self.clear_task_btn.setEnabled(True)
            self.task_list.setEnabled(True)
            self.change_task_btn.setEnabled(False)


    def remove_process(self):
        """
        从列表中移除选定的进程
        """
        index = self.table_model.get_selected_row_index(self.process_view)
        if index != None and index != -1:
            handle = self.table_model.get_data(index)["handle"] # type: ignore
            self.manager.remove_item(handle)
            self._update_widget_status()
    
        
    def refresh_handle_box(self):
        """
        刷新窗口列表
        """
        title = self.window_title.text().strip()
        handle = self.manager.get_target_window_handles(title) if title else []
        self.handle_box.clear()
        self.handle_box.addItems([str(h) for h in handle])
        self.handle_box.setCurrentIndex(0)

    def _refresh_process_view(self, map: dict[int, ProcessItem]):
        """
        处理窗口任务变化信号,更新列表显示
        """
        self.table_model.clear_data()
        if not map:
            return
        for item in map.values():
            self.table_model.add_data({
                "name": item.name,
                "handle": item.handle,
                "status": item._status_cache["overall_status"],
                "current_run": item._status_cache["current_task"],
                "progress": item._status_cache["progress"],
            })

    def _refresh_process_status(self, handle: int, status: dict):
        """
        刷新指定进程的状态
        """
        index = self.table_model.find_index_by_handle_int(handle)
        if index != None and index != -1:
            self.table_model.update_data(index, 2, status["status"])
            self.table_model.update_data(index, 3, status["current_run"])
            self.table_model.update_data(index, 4, status["progress"])

    def control_process(self):
        """
        控制选中进程的启动/停止
        """
        handle = self.get_current_handle()
        if not handle:
            logger.error("错误：没有选中项", mode=self.log_mode) # 添加错误提示
            return
        
        item = self.manager.get_item(handle)
        if not item:
            logger.error(f"错误：找不到句柄 {handle} 的进程", mode=self.log_mode) # 添加错误提示
            return

        if item._status_cache["overall_status"] == "已停止" or item._status_cache["overall_status"] == "未运行":
            item.start_process()
        else:
            item.stop_process()
        
    def add_process(self):
        """
        添加新进程到列表
        """
        hwnd_str = self.handle_box.currentText()
        if not hwnd_str:
            return
        
        handle = int(hwnd_str)
        process_name = self.name_input.text().strip()
        tasks = self.task_list.get_all_items()

        try:
            self.manager.add_item(handle, process_name, tasks) 
        except Exception as e:
            logger.error(f"添加失败: {e}", mode=self.log_mode)


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

    def add_task_to_list(self):
        """
        添加任务到列表
        """
        self.task_list.addItem(self.task_box.currentText())