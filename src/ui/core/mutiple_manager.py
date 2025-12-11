import win32gui
import re
from PySide6.QtCore import QObject, Signal
from .process_item import ProcessItem
from ..core.logger import logger

class MultipleProcessManager(QObject):
    """
    多进程管理类，用于管理多个窗口任务模型.
    """
    process_item_changed = Signal(object)  # 进程项变化信号
    task_status_changed = Signal(int, object) # 任务状态变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: dict[int, ProcessItem] = {} # hwnd -> ProcessItem
        self.log_mode: int = 3

    def add_item(self, hwnd, name="", tasks: list=[]):
        """
        添加一个新的窗口任务模型
        """
        if hwnd in self.items:
            logger.warning(f"{hwnd} 已存在，不重复创建", mode=self.log_mode)
            return self.items[hwnd]
        
        try:
            # 创建 ProcessItem
            item = ProcessItem(hwnd, name, multi_run=True, tasks=tasks)
            # 连接任务状态变化信号
            item.task_model_status_signal.connect(self._emit_task_status_changed)
            logger.info(f"添加任务线程成功: {item.handle} - {item.name}", mode=4)
        except Exception as e:
            logger.error(f"创建 ProcessItem 实例时出错: {e}", mode=self.log_mode)
            return None
            
        self.items[hwnd] = item
        self.process_item_changed.emit(self.get_all_items())
        return item

    def remove_item(self, hwnd: int):
        if hwnd in self.items:
            name = self.items[hwnd].name
            self.items[hwnd].kill_process() # 停止并销毁线程
            del self.items[hwnd]
            self.process_item_changed.emit(self.get_all_items())
            logger.info(f"移除成功: {hwnd} - {name}", mode=self.log_mode)
        else:
            logger.warning(f"窗口句柄: {hwnd} 不存在", mode=self.log_mode)

    def clear_items(self):
        """
        清空所有已添加的窗口任务模型.
        """
        if not self.items:
            return
        for item in self.items.values():
            item.kill_process()
        self.items.clear()
        self.process_item_changed.emit(self.get_all_items())
        logger.info(f"已清空所有任务", mode=self.log_mode)

    def get_item(self, hwnd: int) -> ProcessItem | None:
        """
        获取指定窗口句柄的 ProcessItem 实例.

        Args:
            hwnd (int): 窗口句柄.

        Returns:
            ProcessItem | None: 对应的 ProcessItem 实例，如果不存在则返回 None.
        """
        return self.items.get(hwnd, None)

    def get_all_items(self) -> dict:
        """
        获取所有已添加的 ProcessItem 实例.

        Returns:
            dict: 所有 ProcessItem 实例，键为窗口句柄，值为 ProcessItem 实例.
        """
        return self.items

    def get_target_window_handles(self, target_title_part: str) -> list:
        """
        获取所有标题包含指定部分的可见窗口句柄.

        Args:
            target_title_part (str): 窗口标题的部分字符串.

        Returns:
            list: 所有匹配的窗口句柄列表.
        """
        # 这个方法保持不变，因为它只是查找窗口句柄
        target_handles = []
        def callback(hwnd, extra):
            window_title = win32gui.GetWindowText(hwnd)
            if win32gui.IsWindowVisible(hwnd) and window_title:
                if re.search(target_title_part, window_title, re.IGNORECASE):
                    target_handles.append(hwnd)
            return True
        win32gui.EnumWindows(callback, None)
        return target_handles

    # --- 数据获取接口 ---
    
    def get_process_task_list(self, hwnd: int) -> list[str]:
        """
        直接从对象获取数据
        """
        item = self.get_item(hwnd)
        if item and item.task_model:
            return item.task_model.get_run_task_list_names()
        return []

    def set_process_task_list(self, hwnd: int, new_task_names: list[str]):
        """
        直接调用对象方法修改配置
        """
        item = self.get_item(hwnd)
        if item:
            item.change_task_list(new_task_names)
            logger.info(f"{hwnd} 的任务列表已更新", mode=self.log_mode)
    
    def _emit_task_status_changed(self, hwnd: int, status: dict):
        """
        任务状态变化信号处理函数.

        Args:
            hwnd (int): 窗口句柄.
            status (dict): 任务状态字典，键为任务名称，值为任务状态.
        """
        self.task_status_changed.emit(hwnd, status)
            
    # 下面这些 start/stop item 只是转发调用
    def start_item(self, item: ProcessItem):
        """
        启动指定 ProcessItem 实例关联的任务线程.

        Args:
            item (ProcessItem): 要启动的 ProcessItem 实例.
        """
        if item: item.start_process()
        
    def stop_item(self, item: ProcessItem):
        """
        停止指定 ProcessItem 实例关联的任务线程.

        Args:
            item (ProcessItem): 要停止的 ProcessItem 实例.
        """
        if item: item.stop_process()
