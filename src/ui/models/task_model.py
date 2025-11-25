from PySide6.QtCore import QObject, Signal
from src.tasks.ri_chang_fu_ben import RiChangFuBen
from src.tasks.lun_jian import LunJian
from ..core.logger import logger
import threading
from time import sleep
from typing import Optional # 用于类型提示



class TaskModel(QObject): 
    """
    任务模型类，继承 QObject 以使用信号机制，包含任务列表、任务设置等。
    """

    # --- 1. 新增：定义信号，用于通知 UI 状态变化 ---
    status_changed = Signal(str)      # 状态（如“运行中”，“已停止”）变化时发送
    progress_changed = Signal(int)     # 进度条数值变化时发送
    running_task_changed = Signal(str) # 当前运行任务变化时发送
    run_list_changed = Signal()        # 运行列表增删改时发送（通知 UI 刷新列表）

    # 任务名称到任务类的映射 (任务工厂)
    TASK_MAP = {
        "日常副本": RiChangFuBen,
        "论剑": LunJian
    }
    
    def __init__(self, window_title: str = "一梦江湖", parent=None): # 允许传入父对象
        super().__init__(parent)
        self.window_title = window_title # 实际游戏窗口标题，后续会注入到任务实例
        self._run_list = []              # 私有变量，存储任务实例 (Task Instances)
        self._running_task_name = "无"
        self._status = "未运行"
        self._progress = 0
        self._is_queue_running = False   # 队列是否在运行

        # ⚡ 新增：用于任务队列多线程控制
        self._queue_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._current_task_index = -1 # 当前正在运行的任务在列表中的索引
    
    # --- 2. 改进：任务工厂方法重命名和依赖注入 ---
    
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
                task_instance = task_class() 
            # 更好的做法：task_instance = task_class(window_title=self.window_title, config=self.get_settings(task_name))
            return task_instance
        except Exception as e:
            logger.error(f"创建任务实例时出错: {task_name}, 错误: {e}")
            return None

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
    
    # ⚡ 新增核心方法：启动/停止队列

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
        在单独的线程中执行任务队列。
        """
        self.set_queue_running(True)
        total_tasks = len(self._run_list)
        
        try:
            for index, task in enumerate(self._run_list):
                # 检查停止信号
                if self._stop_event.is_set():
                    logger.info("接收到停止信号，任务队列中止。")
                    break

                self._current_task_index = index
                task_name = task.get_task_name()
                logger.log(f"开始运行任务: {task_name}")
                self.set_running_task(task_name)

                # 1. 任务启动：设置任务内部运行状态
                task.start() 
                
                # 2. 任务执行（假设 task.run() 是阻塞的）
                # 假设任务实例有一个 run() 方法执行其主逻辑
                try:
                    if hasattr(task, 'run'):
                        task.run() 
                    else:
                        # 如果任务没有 run() 方法，则调用 start() 并希望它阻塞
                        task.start()
                        
                except Exception as e:
                    logger.error(f"任务 {task_name} 运行时发生错误: {e}")
                    # 错误不影响队列继续
                
                # 3. 任务结束/清理 (确保任务停止)
                task.stop()

                # 4. 更新进度
                progress_value = int((index + 1) / total_tasks * 100)
                self.set_progress(progress_value)
                logger.log(f"任务 {task_name} 完成。")

            # 队列自然完成
            if not self._stop_event.is_set():
                self.set_status("队列已完成")
                logger.info("所有任务执行完毕。")
            else:
                self.set_status("已停止")
                logger.info("任务队列已停止。")

        except Exception as e:
            logger.error(f"任务队列发生未知错误: {e}")
            self.set_status("发生错误")
        
        finally:
            self.set_queue_running(False) # 最终设置为未运行
            self.set_progress(0)
            self.set_running_task("无")
            self._current_task_index = -1
            self._queue_thread = None # 清理线程引用