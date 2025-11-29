from PySide6.QtCore import QObject, Signal
from src.tasks.ri_chang_fu_ben import RiChangFuBen
from src.tasks.lun_jian import LunJian
from ..core.logger import logger
import threading
import win32gui
import re
from typing import Optional # 用于类型提示
from ...modules.auto_clicker import AutoClicker
from ...modules.capture_window import WindowCapture
from .task_cfg_model import task_cfg_model

class TaskModel(QObject): 
    """
    任务模型类，继承 QObject 以使用信号机制，包含任务列表、任务设置等。
    """

    # --- 1. 新增：定义信号，用于通知 UI 状态变化 ---
    status_changed = Signal(str)      # 状态（如“运行中”，“已停止”）变化时发送
    progress_changed = Signal(int)     # 进度条数值变化时发送
    running_task_changed = Signal(str) # 当前运行任务变化时发送
    run_list_changed = Signal()        # 运行列表增删改时发送（通知 UI 刷新列表）
    connect_window_changed = Signal(str) # 连接窗口信号，参数为窗口标题

    # 任务名称到任务类的映射 (任务工厂)
    TASK_MAP = {
        "日常副本": RiChangFuBen,
        "论剑": LunJian
    }
    
    def __init__(self, parent=None): # 允许传入父对象
        super().__init__(parent)
        self.window_title = task_cfg_model.task_cfg["window_title"] # 实际游戏窗口标题，后续会注入到任务实例
        self._run_list = []              # 私有变量，存储任务实例 (Task Instances)
        self._running_task_name = "无"
        self._status = "待机"
        self._progress = 0
        self._is_queue_running = False   # 队列是否在运行
        
        self.thread_timeout = task_cfg_model.task_cfg["timeout"] # 线程超时时间，单位秒
        self.loop_count = task_cfg_model.task_cfg["loop_count"] # 循环次数

        self.wincap = WindowCapture()
        self.clicker = AutoClicker()
        self.hwnd = None # 窗口句柄

        # ⚡ 新增：用于任务队列多线程控制
        self._queue_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._current_task_index = -1 # 当前正在运行的任务在列表中的索引

        task_cfg_model.task_cfg_updated.connect(self.load_task_cfg)
    
    # --- 2. 改进：任务工厂方法重命名和依赖注入 ---
    def load_task_cfg(self):
        """
        从任务配置模型加载任务配置.
        """
        self.window_title = task_cfg_model.task_cfg["window_title"]
        self.thread_timeout = task_cfg_model.task_cfg["timeout"]
        self.loop_count = task_cfg_model.task_cfg["loop_count"]
        self.update_task_cfg(task_cfg_model.task_cfg)

    def connect_window(self) -> bool:
        """尝试查找并连接到目标窗口，并更新状态."""
        logger.info(f"正在尝试连接窗口: {self.window_title}, 句柄: {self.hwnd}...")
        
        if self.hwnd:
            self.wincap.set_hwnd(self.hwnd)
            self.clicker.set_hwnd(self.hwnd)
            self.clicker.connect_window()
            window_name = win32gui.GetWindowText(self.hwnd)
            if self.clicker.window: 
                logger.info(f"窗口连接成功: {window_name}, 句柄: {self.hwnd}")
                self.connect_window_changed.emit(window_name) # 发送连接成功信号
                return True
            else:
                logger.error(f"窗口句柄找到，但 AutoClicker 无法连接。")
                return False
        else:
            self.set_status("未找到窗口")
            logger.error(f"未找到目标窗口: {self.window_title}")
            return False

    def get_target_window_handles(self, target_title_part: str):
        """
        查找所有标题中包含指定文本的窗口句柄。

        Args:
            target_title_part (str): 目标窗口标题中包含的文本。

        Returns:
            list: 匹配的目标窗口句柄列表。
        """
        
        # 用于存储找到的句柄
        target_handles = []

        def callback(hwnd, extra):
            """
            EnumWindows 的回调函数。对每个顶级窗口执行。
            """
            # 获取窗口标题
            window_title = win32gui.GetWindowText(hwnd)
            
            # 检查窗口是否可见且有标题
            if win32gui.IsWindowVisible(hwnd) and window_title:
                # 检查标题是否包含目标文本（不区分大小写）
                if re.search(target_title_part, window_title, re.IGNORECASE):
                    # 如果匹配，则将句柄添加到列表中
                    target_handles.append(hwnd)
            
            # 必须返回 True 才能继续枚举下一个窗口
            return True

        # 调用 EnumWindows 开始枚举所有顶级窗口
        # callback 函数是第一个参数，extra 是可选的用户自定义数据 (这里用 None)
        win32gui.EnumWindows(callback, None)
        
        logger.info(f"找到 {len(target_handles)} 个匹配窗口: {target_handles}")
        return target_handles
        
    def set_hwnd(self, hwnd: int):
        """
        设置窗口句柄.
        
        Args:
            hwnd (int): 窗口句柄.
        """
        self.hwnd = hwnd

    def create_task_instance(self, task_name: str):
        """
        根据名称创建任务实例。
        
        Args:
            task_name (str): 任务名称。
        
        Returns:
            Task: 任务实例，或 None。
        """
        try:
            task_class = self.TASK_MAP.get(task_name)
            if task_class:
                # 💡 关键改进：在这里创建任务实例。后续还需要传入配置和窗口标题。
                task_instance = task_class(config=task_cfg_model.task_cfg) 
            return task_instance
        except Exception as e:
            logger.error(f"创建任务实例时出错: {task_name}, 错误: {e}")
            return None
        
    def update_task_cfg(self, cfg: dict):
        """
        更新列表中所有任务配置。
        
        Args:
            cfg (dict): 新的任务配置。
        """
        try:
            for task in self._run_list:
                task.update_config(cfg)
            logger.info(f"已同步更新列表中所有任务配置.")
        except Exception as e:
            logger.error(f"更新任务配置时出错: {e}")

    # --- 3. 改进：运行列表管理，支持列表组件操作 ---

    def get_run_list(self) -> list:
        """返回任务实例列表."""
        return self._run_list

    def add_task(self, task_name: str):
        """
        添加任务实例到运行列表。
        """
        try:
            task = self.create_task_instance(task_name)
            if task:
                self._run_list.append(task)
                logger.info(f"添加任务: {task_name}")
                self.run_list_changed.emit() # 通知 UI 刷新列表
        except Exception as e:
            logger.error(f"添加任务时出错: {task_name}, 错误: {e}")

    def remove_task_by_index(self, index: int):
        """
        根据索引从运行列表中移除任务。UI 列表组件通常提供索引。
        """
        try:
            if 0 <= index < len(self._run_list):
                task_name = self._run_list[index].get_task_name()
                self._run_list.pop(index)
                logger.info(f"移除任务: {task_name}")
                self.run_list_changed.emit() # 通知 UI 刷新列表
        except Exception as e:
            logger.error(f"移除任务时出错: {index}, 错误: {e}")

    def clear_run_list(self):
        """
        清空运行列表中的所有任务实例。
        """
        try:
            self._run_list.clear()
            logger.info("已清空运行列表中的所有任务实例。")
            self.run_list_changed.emit() # 通知 UI 刷新列表
        except Exception as e:
            logger.error(f"清空运行列表时出错: {e}")
    
    def move_task(self, from_index: int, to_index: int):
        """
        移动运行列表中的任务位置（供 UI 列表的上移/下移操作调用）。
        """
        try:
            if 0 <= from_index < len(self._run_list) and 0 <= to_index < len(self._run_list):
                from_name = self._run_list[from_index].get_task_name()
                to_name = self._run_list[to_index].get_task_name()
                task = self._run_list.pop(from_index)
                self._run_list.insert(to_index, task)
                logger.info(f"移动任务: {from_name} -> {to_name}")
                self.run_list_changed.emit() # 通知 UI 刷新列表
        except Exception as e:
            logger.error(f"移动任务时出错: {from_index} -> {to_index}, 错误: {e}")

    # --- 4. 改进：状态/进度更新时发送信号 ---
    
    def set_progress(self, progress: int):
        """设置脚本运行进度，并发送信号。"""
        if self._progress != progress:
            self._progress = progress
            self.progress_changed.emit(progress)
    
    def get_progress(self):
        return self._progress
    
    def set_status(self, status: str):
        """设置脚本运行状态，并发送信号。"""
        if self._status != status:
            self._status = status
            self.status_changed.emit(status)
    
    def get_status(self):
        return self._status
    
    def get_window_title(self):
        return self.window_title
    
    def set_running_task(self, task_name: str):
        """设置当前运行任务名称，并发送信号。"""
        if self._running_task_name != task_name:
            self._running_task_name = task_name
            self.running_task_changed.emit(task_name)
    
    def get_running_task(self):
        return self._running_task_name

    # --- 5. 任务队列控制方法 ---

    def is_queue_running(self) -> bool:
        """返回任务队列是否正在运行."""
        return self._is_queue_running

    def set_queue_running(self, state: bool):
        """设置任务队列的运行状态."""
        self._is_queue_running = state
        self.set_status("运行中" if state else "已停止")

    def get_task_names(self):
        """获取任务名称列表."""
        return list(self.TASK_MAP.keys())
    

    def start_queue(self):
        """
        开始运行任务队列。
        """
        if self._is_queue_running:
            logger.warning("任务队列已在运行中。")
            return

        if not self._run_list:
            logger.warning("任务列表为空，无法启动。")
            self.set_status("未运行")
            return
        
        if not self.connect_window():
            self.set_status("启动失败：窗口未连接")
            return
            
        # 1. 重置停止事件
        self._stop_event.clear()
        
        # 2. 创建并启动线程
        self._queue_thread = threading.Thread(target=self._run_task_queue, daemon=True)
        self._queue_thread.start()
        logger.info("任务队列已启动...")

    def stop_queue(self):
        """
        停止运行任务队列。
        """
        if not self._is_queue_running:
            logger.warning("任务队列未在运行中。")
            return
            
        # 1. 设置停止事件
        self._stop_event.set()
        
        # 2. 尝试停止当前正在运行的任务实例
        if 0 <= self._current_task_index < len(self._run_list):
            current_task = self._run_list[self._current_task_index]
            # 假设 Task 实例的 stop() 方法能中断其 run() 循环
            current_task.stop() 

        logger.info("任务队列正在停止...")


    def _run_task_queue(self):
        """
        在单独的线程中执行任务队列，支持循环次数控制和任务超时监控。
        """
        self.set_queue_running(True)
        total_tasks = len(self._run_list)
        
        current_loop = 0 # 记录当前循环次数
        
        try:
            # 外部循环：控制总的运行次数
            while current_loop < self.loop_count and not self._stop_event.is_set():
                logger.info(f"--- 开始第 {current_loop + 1} 次循环 (共 {self.loop_count} 次) ---")
                
                # 内部循环：迭代任务列表
                for index, task in enumerate(self._run_list):
                    # 检查总停止信号
                    if self._stop_event.is_set():
                        logger.info("接收到停止信号，任务队列中止。")
                        break 

                    self._current_task_index = index
                    task_name = task.get_task_name()
                    
                    try:
                        task.configure_window_access(self.wincap, self.clicker)
                        
                        # ⚡ 注入超时时间 (需要先在 TemplateMatchingTask 中添加 set_timeout 方法)
                        if hasattr(task, 'set_timeout'):
                            task.set_timeout(self.thread_timeout)
                            
                    except Exception as e:
                        logger.error(f"任务 {task_name} 依赖配置失败: {e}")
                        continue

                    logger.info(f"开始运行任务: {task_name} (超时限制: {self.thread_timeout}秒)")
                    self.set_running_task(task_name)

                    # 2. 任务执行
                    try:
                        if hasattr(task, 'run'):
                            # 任务的 run() 方法需要在内部实现超时检查
                            task.run() 
                        else:
                            task.start()
                            
                    except Exception as e:
                        logger.error(f"任务 {task_name} 运行时发生错误: {e}")
                    
                    # 3. 任务结束/清理 (确保任务停止)
                    task.stop() # 这一步很关键，用于清理任务内部状态
                    
                    # 4. 更新进度
                    progress_value = int((index + 1) / total_tasks * 100)
                    self.set_progress(progress_value)
                    logger.info(f"任务 {task_name} 完成。")

                # 队列自然完成一次循环
                if not self._stop_event.is_set():
                    current_loop += 1
                    self.set_progress(0) # 每轮结束后重置进度条
                
            # 循环结束后的状态处理
            if not self._stop_event.is_set():
                self.set_status("队列已完成")
                logger.info(f"所有任务执行完毕，共运行 {current_loop} 次。")
            else:
                self.set_status("已停止")
                logger.info(f"任务队列已停止，共运行 {current_loop} 次。")
        
        finally:
            self.set_queue_running(False) # 最终设置为未运行
            self.set_progress(0)
            self.set_running_task("无")
            self._current_task_index = -1
            self._queue_thread = None # 清理线程引用