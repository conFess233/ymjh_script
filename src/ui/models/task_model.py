import threading
import win32gui
import re
import time
from multiprocessing import Process, Queue
from typing import Optional
from PySide6.QtCore import QObject, Signal
from src.tasks.ri_chang_fu_ben import RiChangFuBen
from src.tasks.lun_jian import LunJian
from ...modules.auto_clicker import AutoClicker
from ...modules.window_capture import WindowCapture
from .task_cfg_model import task_cfg_model
from ..core.logger import logger

class TaskModel(QObject): 
    """
    任务模型类，继承 QObject 以使用信号机制，包含任务列表、任务设置等。
    """

    # 定义信号，用于通知 UI 状态变化
    status_changed = Signal(str)            # 状态（如“运行中”，“已停止”）变化时发送
    progress_changed = Signal(int)          # 进度条数值变化时发送
    running_task_changed = Signal(str, int) # 当前运行任务变化时发送
    run_list_changed = Signal()             # 运行列表增删改时发送（通知 UI 刷新列表）
    connect_window_changed = Signal(str)    # 连接窗口信号，参数为窗口标题
    queue_paused_changed = Signal(bool)     # 队列暂停状态变化时发送，参数为暂停状态（True/False）
    test_signal = Signal(str)

    # 任务名称到任务类的映射
    TASK_MAP = {
        "日常副本": RiChangFuBen,
        "论剑": LunJian
    }
    
    def __init__(self, parent=None, log_mode: int = 0, multi_run_mode: bool = False, hwnd=None, name: str = ""):
        super().__init__(parent)
        self._run_list = []                                         # 私有变量，存储任务实例
        self._running_task_name = "无"                              # 当前正在运行的任务名称
        self.name = name                                            # 任务模型名称, 仅用于多开区分
        self._status = "待机"                                       # 当前任务状态
        self._progress = 0                                          # 当前任务进度
        self._is_queue_running = False                              # 队列是否在运行
        self._is_queue_paused = False                               # 队列是否暂停
        
        self.window_title = task_cfg_model.task_cfg["window_title"] # 游戏窗口标题
        self.thread_timeout = task_cfg_model.task_cfg["timeout"]    # 线程超时时间，单位秒
        self.loop_count = task_cfg_model.task_cfg["loop_count"]     # 循环次数

        self.wincap = WindowCapture()                               # 窗口捕获器
        self.clicker = AutoClicker()                                # 自动点击器
        self.hwnd = hwnd                                            # 窗口句柄
        self.log_mode = log_mode                                    # 日志模式
        self.multi_run_mode = multi_run_mode                        # 多开模式

        # 用于任务队列多线程控制
        self._queue_thread: Optional[threading.Thread] = None       # 任务队列线程
        self._stop_event = threading.Event()                        # 停止事件，用于控制任务队列线程
        self._pause_condition = threading.Condition()               # 暂停条件变量，用于暂停/恢复任务队列线程
        self._current_task_index = -1                               # 当前正在运行的任务在列表中的索引

        task_cfg_model.task_cfg_updated.connect(self.load_task_cfg) # 任务配置更新时加载任务配置
    
    # --- 初始化/配置相关 ---
    def load_task_cfg(self):
        """
        加载任务配置.
        """
        self.window_title = task_cfg_model.task_cfg["window_title"]
        self.thread_timeout = task_cfg_model.task_cfg["timeout"]
        self.loop_count = task_cfg_model.task_cfg["loop_count"]
        self.update_task_cfg(task_cfg_model.task_cfg)

    def connect_window(self) -> bool:
        """
        尝试查找并连接到目标窗口，并更新状态.
        """
        if self.multi_run_mode:
            if not self.hwnd:
                logger.error("多开模式下未指定窗口句柄", mode=self.log_mode)
                print(f"多开模式下未指定窗口句柄: {self.hwnd}")
                return False
            try:
                self.wincap.set_hwnd(self.hwnd)
                self.clicker.set_hwnd(self.hwnd)
                self.clicker.connect_window()
                window_name = win32gui.GetWindowText(self.hwnd)
                return True
            except Exception as e:
                error_msg = f"多开模式下连接窗口失败: {e}"
                logger.error(error_msg, mode=self.log_mode)
                return False
            
        logger.info(f"正在尝试连接窗口: {self.window_title}, 句柄: {self.hwnd}...", mode=1)
        
        if self.hwnd:
            self.wincap.set_hwnd(self.hwnd)
            self.clicker.set_hwnd(self.hwnd)
            self.clicker.connect_window()
            window_name = win32gui.GetWindowText(self.hwnd)
            if self.clicker.window: 
                logger.info(f"窗口连接成功: {window_name}, 句柄: {self.hwnd}", mode=self.log_mode)
                self.connect_window_changed.emit(window_name) # 发送连接成功信号
                return True
            else:
                logger.error(f"窗口句柄找到，但 AutoClicker 无法连接。", mode=self.log_mode)
                return False
        else:
            self.set_status("未找到窗口")
            logger.error(f"未找到目标窗口: {self.window_title}", mode=self.log_mode)
            return False

    def get_target_window_handles(self, target_title_part: str) -> list:
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
        win32gui.EnumWindows(callback, None)
        
        logger.info(f"找到 {len(target_handles)} 个匹配窗口: {target_handles}", mode=self.log_mode)
        return target_handles

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
                # 创建任务实例
                task_instance = task_class(config=task_cfg_model.task_cfg, log_mode=self.log_mode) 
            return task_instance
        except Exception as e:
            logger.error(f"创建任务实例时出错: {task_name}, 错误: {e}", mode=self.log_mode)
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
            logger.info(f"已同步更新列表中所有任务配置.", mode=self.log_mode)
        except Exception as e:
            logger.error(f"更新任务配置时出错: {e}", mode=self.log_mode)

    def wait_for_stop(self, timeout=2.0):
        """
        等待内部任务线程完全退出
        """
        if self._queue_thread and self._queue_thread.is_alive():
            self._queue_thread.join(timeout)

    # --- 运行列表管理 ---

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
                logger.info(f"添加任务: {task_name}", mode=1)
                self.run_list_changed.emit() # 通知 UI 刷新列表
        except Exception as e:
            logger.error(f"添加任务时出错: {task_name}, 错误: {e}", mode=self.log_mode)

    def add_task_multiple(self, task_list: list):
        """
        添加多个任务实例到运行列表。
        """
        try:
            self._run_list.clear()
            for task_name in task_list:
                task = self.create_task_instance(task_name)
                if task:
                    self._run_list.append(task)
        except Exception as e:
            logger.error(f"添加多个任务时出错: {task_list}, 错误: {e}", mode=self.log_mode)

    def remove_task_by_index(self, index: int):
        """
        根据索引从运行列表中移除任务。UI 列表组件通常提供索引。
        """
        try:
            if 0 <= index < len(self._run_list):
                task_name = self._run_list[index].get_task_name()
                self._run_list.pop(index)
                logger.info(f"移除任务: {task_name}", mode=1)
                self.run_list_changed.emit() # 通知 UI 刷新列表
        except Exception as e:
            logger.error(f"移除任务时出错: {index}, 错误: {e}", mode=self.log_mode)

    def clear_run_list(self):
        """
        清空运行列表中的所有任务实例。
        """
        try:
            self._run_list.clear()
            logger.info("已清空运行列表中的所有任务实例。", mode=1)
            self.run_list_changed.emit() # 通知 UI 刷新列表
        except Exception as e:
            logger.error(f"清空运行列表时出错: {e}", mode=self.log_mode)
    
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
                logger.info(f"移动任务: {from_name} -> {to_name}", mode=1)
                self.run_list_changed.emit() # 通知 UI 刷新列表
        except Exception as e:
            logger.error(f"移动任务时出错: {from_index} -> {to_index}, 错误: {e}", mode=self.log_mode)
    
    # --- 任务队列相关 ---
    def start_queue(self):
        """
        开始运行任务队列。
        """
        if self._is_queue_running:
            logger.warning("任务队列已在运行中。", mode=self.log_mode)
            return

        if not self._run_list:
            logger.warning("任务列表为空，无法启动。", mode=self.log_mode)
            self.set_status("未运行")
            return
        
        if self.hwnd is None:
            logger.warning("窗口句柄为空，尝试连接窗口...", mode=self.log_mode)
            if not self.connect_window():
                self.set_status("启动失败：窗口未连接")
            return
            
        # 重置停止事件
        self._stop_event.clear()
        
        # 创建并启动线程
        self._queue_thread = threading.Thread(target=self._run_task_queue, daemon=True)
        self._queue_thread.start()
        logger.info("任务队列已启动...", mode=1)

    def stop_queue(self):
        """
        停止运行任务队列。
        """
        if not self._is_queue_running:
            return
            
        # 设置停止事件
        self._stop_event.set()
        with self._pause_condition:
            self.set_queue_paused(False) 
            self._pause_condition.notify_all() # 唤醒等待的线程
        
        # 尝试停止当前正在运行的任务实例
        if 0 <= self._current_task_index < len(self._run_list):
            current_task = self._run_list[self._current_task_index]
            current_task.stop() 

        logger.info("任务队列正在停止...", mode=1)


    def _run_task_queue(self):
        """
        在单独的线程中执行任务队列，支持循环次数控制和任务超时监控。
        """
        self.set_queue_running(True)
        total_tasks = len(self._run_list)
        
        current_loop = 0 # 记录当前循环次数
        all_loop_start_time = time.time() # 记录所有循环的开始时间
        all_loop_total_time = 0 # 记录所有循环的总耗时
        
        try:
            # 外部循环：控制总的运行次数
            while current_loop < self.loop_count and not self._stop_event.is_set():
                logger.info(f"--- 开始第 {current_loop + 1} 次循环 (共 {self.loop_count} 次) ---", mode=self.log_mode)
                # 计时器开始，用于计算每轮任务执行消耗的时间
                loop_start_time = time.time()
                total_time = 0 # 累计每轮任务总耗时
                
                # 内部循环：迭代任务列表
                for index, task in enumerate(self._run_list):

                    # 暂停检查点：在每个任务开始前检查是否需要暂停
                    with self._pause_condition:
                        while self._is_queue_paused:
                            self.set_status("已暂停") # 确保状态更新到 UI
                            # 线程在此阻塞，直到 resume_queue() 调用 notify() 
                            # 并且 _is_queue_paused 被设置为 False
                            self._pause_condition.wait()
                            if self._stop_event.is_set():
                                logger.info("接收到停止信号，任务队列中止。", mode=self.log_mode)
                                break 
                            
                    # 检查总停止信号
                    if self._stop_event.is_set():
                        logger.info("接收到停止信号，任务队列中止。", mode=self.log_mode)
                        break 

                    self._current_task_index = index
                    task_name = task.get_task_name()
                    
                    try:
                        task.configure_window_access(self.wincap, self.clicker, self._pause_condition, lambda: self._is_queue_paused)
                        
                        # 注入超时时间
                        if hasattr(task, 'set_timeout'):
                            task.set_timeout(self.thread_timeout)

                    except Exception as e:
                        logger.error(f"任务 {task_name} 依赖配置失败: {e}", mode=self.log_mode)
                        continue

                    logger.info(f"开始运行任务: {task_name} (超时限制: {self.thread_timeout}秒)", mode=self.log_mode)
                    self.set_running_task(task_name, index)
                    task_start_time = time.time()

                    # 任务执行
                    try:
                        if hasattr(task, 'run'):
                            task.run() 
                        else:
                            task.start()
                            
                    except Exception as e:
                        logger.error(f"任务 {task_name} 运行时发生错误: {e}", mode=self.log_mode)
                    
                    # 任务结束/清理 (确保任务停止)
                    task.stop() # 清理任务内部状态
                    
                    # 更新进度
                    progress_value = int((index + 1) / total_tasks * 100)
                    self.set_progress(progress_value)
                    task_end_time = time.time()
                    task_duration = task_end_time - task_start_time
                    logger.info(f"任务 {task_name} 完成。耗时: {task_duration:.2f}秒", mode=self.log_mode)

                # 队列自然完成一次循环
                if not self._stop_event.is_set():
                    current_loop += 1
                    self.set_progress(0) # 每轮结束后重置进度条
                    loop_total_duration = time.time() - loop_start_time
                    logger.info(f"第 {current_loop} 次循环完成，耗时: {loop_total_duration:.2f}秒", mode=self.log_mode)                
            # 循环结束后的状态处理
            if not self._stop_event.is_set():
                self.set_status("队列已完成")
                logger.info(f"所有任务执行完毕，共运行 {current_loop} 次。", mode=self.log_mode)
            else:
                self.set_status("已停止")
                logger.info(f"任务队列已停止，共运行 {current_loop} 次。", mode=self.log_mode)
        
        finally:
            self.set_queue_running(False) # 最终设置为未运行
            # 确保在退出线程时，唤醒 Condition，防止其他线程在此等待
            all_loop_total_time = time.time() - all_loop_start_time
            logger.info(f"总耗时: {all_loop_total_time:.2f}秒", mode=self.log_mode)
            with self._pause_condition:
             self._pause_condition.notify_all()
            self.set_queue_paused(False) # 重置暂停状态
            self.set_progress(0)
            self.set_running_task("无", -1)
            self._current_task_index = -1
            self._queue_thread = None # 清理线程引用
        
    def pause_queue(self):
        """
        暂停任务队列的执行.
        """
        if self._is_queue_running and not self._is_queue_paused:
            self._is_queue_paused = True
            logger.info("任务队列已暂停...", mode=1)
            self.queue_paused_changed.emit(True)
            self.set_status("已暂停")
        else:
            logger.warning("任务未运行或已暂停，无法执行暂停操作。", mode=self.log_mode)

    def resume_queue(self):
        """
        恢复任务队列的执行.
        """
        if self._is_queue_running and self._is_queue_paused:
            # 必须在 Condition 锁内修改状态并通知
            with self._pause_condition:
                self._is_queue_paused = False
                logger.info("任务队列已恢复运行...", mode=1)
                self.queue_paused_changed.emit(False)
                self.set_status("运行中")
                # set_status 会在 _run_task_queue 恢复后更新
                self._pause_condition.notify_all() # 唤醒等待的线程
        else:
            logger.warning("任务未运行或未处于暂停状态，无法执行恢复操作。", mode=self.log_mode)

    # --- getters/setters ---
    def set_progress(self, progress: int):
        """
        设置脚本运行进度，并发送信号。
        """
        if self._progress != progress:
            self._progress = progress
            self.progress_changed.emit(progress)
    
    def get_progress(self) -> int:
        """
        返回当前运行进度.
        """
        return self._progress
    
    def set_status(self, status: str):
        """
        设置脚本运行状态，并发送信号。
        """
        if self._status != status:
            self._status = status
            self.status_changed.emit(status)
    
    def get_status(self) -> str:
        """
        返回当前运行状态.
        """
        return self._status
    
    def get_window_title(self) -> str:
        """
        返回当前窗口标题.
        """
        return self.window_title
    
    def set_running_task(self, task_name: str, index: int):
        """
        设置当前运行任务，并发送信号。
        """
        if self._running_task_name != task_name or self._current_task_index != index:
            self._running_task_name = task_name
            self._current_task_index = index
            self.running_task_changed.emit(task_name, index)
    
    def get_running_task(self) -> str:
        """
        返回当前运行任务名称.
        """
        return self._running_task_name

    def is_queue_running(self) -> bool:
        """
        返回任务队列是否正在运行.
        """
        return self._is_queue_running
    
    def is_queue_paused(self) -> bool:
        """
        返回任务队列是否处于暂停状态.
        """
        return self._is_queue_paused

    def set_queue_paused(self, state: bool):
        """
        设置任务队列的暂停状态
        """
        self._is_queue_paused = state
        if self.multi_run_mode:
            return
        self.queue_paused_changed.emit(state)

    def set_queue_running(self, state: bool):
        """
        设置任务队列的运行状态
        """
        self._is_queue_running = state
        self.set_status("运行中" if state else "已停止")

    def get_task_names(self) -> list:
        """
        获取任务名称列表.
        """
        return list(self.TASK_MAP.keys())
    
    def set_hwnd(self, hwnd: int):
        """
        设置窗口句柄.
        
        Args:
            hwnd (int): 窗口句柄.
        """
        self.hwnd = hwnd

    def set_log_mode(self, log_mode: int):
        """
        设置日志模式。
        
        Args:
            log_mode (int): 新的日志模式。
        """
        if self.log_mode != log_mode:
            self.log_mode = log_mode
            logger.info(f"日志模式已设置为 {log_mode}", mode=self.log_mode)
            self.set_all_task_log_mode(log_mode)

    def set_all_task_log_mode(self, log_mode: int):
        """
        设置运行列表中所有任务的日志模式。
        
        Args:
            log_mode (int): 新的日志模式。
        """
        try:
            for task in self._run_list:
                if hasattr(task, 'set_log_mode'):
                    task.set_log_mode(log_mode)
            logger.info(f"已同步更新列表中所有任务的日志模式为 {log_mode}.", mode=self.log_mode)
        except Exception as e:
            logger.error(f"更新任务日志模式时出错: {e}", mode=self.log_mode)

    def set_multi_run_mode(self, state: bool):
        """
        设置多开模式.
        
        Args:
            state (bool): 是否启用多开模式.
        """
        self.multi_run_mode = state

    def get_run_task_list_names(self) -> list[str]:
            """
            获取当前任务运行列表中的任务名称（用于序列化传输）.
            """
            return [task.get_task_name() for task in self._run_list]
    
