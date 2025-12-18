import threading
import time
import win32gui
from PySide6.QtCore import QObject, Signal
from ...modules.window_capture import WindowCapture
from ...modules.auto_clicker import AutoClicker
from ...ui.core.logger import logger

class TaskRunner(QObject):
    """
    任务执行器：负责在独立线程中执行任务列表，处理暂停、停止和循环逻辑。
    逻辑已对齐 TaskModel 的实现。
    """
    # 信号定义
    started = Signal()
    finished = Signal()
    stopped = Signal()
    paused = Signal()
    resumed = Signal()
    
    status_msg_changed = Signal(str)        # 状态文字更新 (如 "运行中", "等待中")
    progress_changed = Signal(int)          # 总进度 (0-100)
    current_task_changed = Signal(str, int) # 当前任务名, 索引
    
    def __init__(self, log_mode: int = 0):
        super().__init__()
        # 线程控制
        self._thread = None
        self._stop_event = threading.Event()
        self._pause_condition = threading.Condition()
        self._is_paused = False
        self._is_running = False
        self.log_mode = log_mode
        self._current_hwnd = None
        self._current_task = None
        
        # 核心能力模块
        self.wincap = WindowCapture()
        self.clicker = AutoClicker()

    def is_running(self) -> bool:
        """
        获取当前任务队列是否正在运行
        Returns:
            bool: 是否正在运行
        """
        return self._is_running

    def start(self, tasks: list, hwnd: int, loop_count: int = 1, timeout: int = 600):
        """
        启动任务队列
        Args:
            tasks(list): 任务实例列表 (Task objects)
            hwnd(int): 目标窗口句柄
            loop_count(int): 循环次数
            timeout(int): 单个任务超时时间
        """
        if self._is_running:
            logger.warning("任务队列已在运行中", mode=self.log_mode)
            return

        if not tasks:
            logger.warning("任务列表为空，无法启动", mode=self.log_mode)
            return
        
        if not self._check_window_valid(hwnd):
            logger.error("无效的窗口句柄，无法启动", mode=self.log_mode)
            self.status_msg_changed.emit("启动失败:窗口无效")
            return

        # 初始化状态
        self._stop_event.clear()
        self._is_paused = False
        self._is_running = True
        self._current_hwnd = hwnd
        self._current_task = None
        
        # 设置底层模块的句柄
        self.wincap.set_hwnd(hwnd)
        self.clicker.set_hwnd(hwnd)
        self.clicker.connect_window() # 确保连接

        # 启动工作线程
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(tasks, loop_count, timeout),
            daemon=True
        )
        self._thread.start()
        
        self.started.emit()
        self.status_msg_changed.emit("运行中")
        logger.info("任务队列已启动...", mode=self.log_mode)

    def stop(self):
        """
        停止执行
        """
        if not self._is_running:
            return
            
        logger.info("正在停止任务队列...", mode=1)
        # 设置停止事件
        self._stop_event.set()
        
        # 如果处于暂停状态，需要唤醒线程让它去检测 stop_event
        with self._pause_condition:
            self._is_paused = False
            self._pause_condition.notify_all()

        if self._current_task:
                self._current_task.stop()

        

    def pause(self):
        """
        暂停执行
        """
        if self._is_running and not self._is_paused:
            self._is_paused = True
            self.status_msg_changed.emit("已暂停")
            self.paused.emit()
            logger.info("任务队列已暂停", mode=1)

    def resume(self):
        """
        恢复执行
        """
        if self._is_running and self._is_paused:
            with self._pause_condition:
                self._is_paused = False
                self._pause_condition.notify_all()
            self.status_msg_changed.emit("运行中")
            self.resumed.emit()
            logger.info("任务队列已恢复", mode=1)

    def _check_window_valid(self, hwnd) -> bool:
        """
        检查窗口句柄是否有效且可见
        """
        if not hwnd:
            return False
        return bool(win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd))

    def _run_loop(self, tasks, loop_count, timeout):
        """
        核心工作循环（运行在子线程）
        """
        total_tasks_count = len(tasks)
        current_loop = 0
        all_loop_start_time = time.time()

        try:
            # 外部循环：控制总的运行次数
            while current_loop < loop_count and not self._stop_event.is_set():
                logger.info(f"--- 开始第 {current_loop + 1} 次循环 (共 {loop_count} 次) ---", mode=self.log_mode)
                loop_start_time = time.time()
                
                # 内部循环：迭代任务列表
                for task_idx, task in enumerate(tasks):
                    # 窗口有效性检查
                    if not self._check_window_valid(self._current_hwnd):
                        logger.error("窗口失效，任务队列中止", mode=self.log_mode)
                        self.status_msg_changed.emit("窗口失效")
                        return # 直接退出线程

                    # 暂停/停止检查
                    with self._pause_condition:
                        while self._is_paused:
                            self.status_msg_changed.emit("已暂停")
                            self._pause_condition.wait()
                            if self._stop_event.is_set():
                                logger.info("接收到停止信号，任务队列中止。", mode=self.log_mode)
                                return

                    if self._stop_event.is_set():
                        logger.info("接收到停止信号，任务队列中止。", mode=self.log_mode)
                        return

                    # 任务准备
                    task_name = task.get_task_name()
                    self.current_task_changed.emit(task_name, task_idx)
                    logger.info(f"开始运行任务: {task_name} (超时限制: {timeout}秒)", mode=self.log_mode)
                    
                    task_start_time = time.time()
                    self._current_task = task

                    # 注入依赖
                    try:
                        task.configure_window_access(
                            self.wincap, 
                            self.clicker, 
                            self._pause_condition, 
                            lambda: self._is_paused
                        )
                        # 设置超时
                        if hasattr(task, 'set_timeout'):
                            task.set_timeout(timeout)
                        # 设置日志模式
                        if hasattr(task, 'set_log_mode'):
                            task.set_log_mode(self.log_mode)
                            
                        # 执行任务 (阻塞调用)
                        if hasattr(task, 'run'):
                            task.run()
                        else:
                            task.start()
                        
                    except Exception as e:
                        logger.error(f"任务 {task_name} 执行出错: {e}", mode=self.log_mode)
                    finally:
                        task.stop() # 确保清理任务内部状态
                        self._current_task = None

                    # 更新进度与统计
                    task_duration = time.time() - task_start_time
                    logger.info(f"任务 {task_name} 完成。耗时: {task_duration:.2f}秒", mode=self.log_mode)
                    
                    progress = int((task_idx + 1) / total_tasks_count * 100)
                    self.progress_changed.emit(progress)

                # 循环结束处理
                if not self._stop_event.is_set():
                    current_loop += 1
                    self.progress_changed.emit(100)
                    loop_total_duration = time.time() - loop_start_time
                    logger.info(f"第 {current_loop} 次循环完成，耗时: {loop_total_duration:.2f}秒", mode=self.log_mode)
                    
                    # 循环间歇，重置进度
                    if current_loop < loop_count:
                        time.sleep(1) 
                        self.progress_changed.emit(0)

            # 所有循环结束
            if not self._stop_event.is_set():
                total_time = time.time() - all_loop_start_time
                logger.info(f"所有任务执行完毕，共运行 {current_loop} 次，总耗时 {total_time:.2f}秒", mode=self.log_mode)
                self.status_msg_changed.emit("已完成")
                self.finished.emit()
            else:
                self.status_msg_changed.emit("已停止")
                self.stopped.emit()

        except Exception as e:
            logger.error(f"任务队列发生未捕获异常: {e}", mode=self.log_mode)
            self.status_msg_changed.emit("异常终止")
        finally:
            self._is_running = False
            self._stop_event.clear()
            self._current_hwnd = None
            self._current_task = None
            self.current_task_changed.emit("无", -1)
            self.progress_changed.emit(0)
            # 确保在退出线程时，唤醒 Condition，防止其他线程在此等待
            with self._pause_condition:
                self._is_paused = False
                self._pause_condition.notify_all()