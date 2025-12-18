from PySide6.QtCore import QObject, Signal
from ..core.task_runner import TaskRunner
from ..core.window_manager import WindowManager
from ..models.task_data_model import TaskDataModel
from ..core.logger import logger

class ProcessItem(QObject):
    """
    进程项控制器
    """
    # 定义控制信号，用于跨线程调用 TaskModel 的方法
    sig_start = Signal()
    sig_stop = Signal()
    sig_pause = Signal()
    sig_resume = Signal()
    sig_update_config = Signal(dict)
    
    # 定义状态信号，用于通知 UI 更新进程项状态
    status_signal = Signal(str)  
    # 定义任务状态信号，用于通知 UI 更新任务状态
    task_model_status_signal = Signal(int, object) 

    def __init__(self, handle: int, name: str = "", tasks: list[str] = [], multi_run: bool = False):
        super().__init__()
        self.handle = handle
        self.name = name
        self.multi_run = multi_run
        
        self.window_manager = WindowManager()
        self.data_model = TaskDataModel()
        self.runner = TaskRunner()

        # 初始配置
        self.data_model.add_tasks_by_names(tasks)

        self._status_cache = {
            "overall_status": "未运行",
            "current_task": "无",
            "progress": 0,
            "is_paused": False
        }

        self._bind_signals()

        # 自动连接窗口
        self.window_manager.connect_by_hwnd(handle)

    def _bind_signals(self):
        """
        连接各组件的信号到内部处理函数
        """
        # Runner -> ProcessItem -> UI
        self.runner.started.connect(lambda: self._update_status(overall="运行中", paused=False))
        self.runner.stopped.connect(lambda: self._update_status(overall="已停止", paused=False))
        self.runner.finished.connect(lambda: self._update_status(overall="已完成", paused=False))
        self.runner.paused.connect(lambda: self._update_status(overall="已暂停", paused=True))
        self.runner.resumed.connect(lambda: self._update_status(overall="运行中", paused=False))
        
        # 状态文字更新 (用于日志或简单显示)
        self.runner.status_msg_changed.connect(self.status_signal.emit)
        
        # 进度与当前任务
        self.runner.progress_changed.connect(lambda p: self._update_status(progress=p))
        self.runner.current_task_changed.connect(lambda name, idx: self._update_status(task=name))

    def _update_status(self, overall=None, task=None, progress=None, paused=None):
        """
        统一更新状态缓存并发送信号给 UI
        """
        if overall is not None:
            self._status_cache["overall_status"] = overall
            self.status_signal.emit(overall)
            
        if task is not None:
            self._status_cache["current_task"] = task
            
        if progress is not None:
            self._status_cache["progress"] = progress
            
        if paused is not None:
            self._status_cache["is_paused"] = paused
            # 如果暂停状态改变，文字状态也相应改变
            if paused:
                self._status_cache["overall_status"] = "已暂停"
                self.status_signal.emit("已暂停")
            elif overall is None and self.runner.is_running(): 
                # 恢复且没有传入新的overall状态时，设回运行中
                self._status_cache["overall_status"] = "运行中"
                self.status_signal.emit("运行中")

        # 发送完整的状态对象给 PageMultiple
        self.task_model_status_signal.emit(self.handle, self._status_cache)

    def start_process(self):
        """
        启动任务
        """
        if not self.window_manager.is_active():
            logger.error(f"[{self.name}] 窗口无效，尝试重新连接...")
            if not self.window_manager.connect_by_hwnd(self.handle):
                self.status_signal.emit("窗口丢失")
                return

        # 获取当前最新的任务配置实例
        tasks = self.data_model.get_tasks()
        if not tasks:
            logger.warning(f"[{self.name}] 任务列表为空")
            return

        # 启动 Runner (传入任务列表和句柄)
        self.runner.start(tasks, self.handle)

    def stop_process(self):
        """
        停止.
        """
        self.runner.stop()

    def pause_process(self):
        """
        暂停.
        """
        self.runner.pause()
        
    def resume_process(self):
        """
        恢复.
        """
        self.runner.resume()
    def kill_process(self):
        """
        终止.
        """
        self.stop_process()

    def change_task_list(self, tasks: list[str] = []):
        """
        动态修改任务列表 (通常在未运行状态下调用)
        """
        self.data_model.clear_tasks() # 假设 DataModel 有这个方法
        
        # 重新添加
        if hasattr(self.data_model, 'add_tasks_by_names'):
            self.data_model.add_tasks_by_names(tasks)
        else:
            for t in tasks:
                self.data_model.add_task(t)
        
        logger.info(f"[{self.name}] 任务列表已更新: {tasks}", mode=1)

    def log_msg(self, msg: str, level: str):
        """
        记录日志消息到总日志
        """
        logger.log(level, f"[{self.name}] {msg}")