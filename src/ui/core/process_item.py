from PySide6.QtCore import QObject, Signal, QThread
import time
from ..models.task_model import TaskModel
from ..core.logger import logger

class ProcessItem(QObject):
    """
    进程项模型类，用于管理单个窗口任务模型.
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

    def __init__(self, handle: int, name: str = "", multi_run=False, tasks: list[str] = []):
        super().__init__()
        self.handle = handle
        self.name = name
        self.multi_run = multi_run
        
        # 创建子线程
        self.worker_thread = QThread()
        
        # 创建 TaskModel 实例
        self.task_model = TaskModel(hwnd=handle, name=name, multi_run_mode=True, log_mode=3)

        if not self.task_model.connect_window():
            logger.error(f"窗口 {handle} 配置失败，无法创建任务线程")
            return
        self.task_model.add_task_multiple(tasks)
        
        # 将 TaskModel 移动到子线程
        self.task_model.moveToThread(self.worker_thread)
        
        # 连接控制信号
        self.sig_start.connect(self.task_model.start_queue)
        self.sig_stop.connect(self.task_model.stop_queue)
        self.sig_pause.connect(self.task_model.pause_queue)
        self.sig_resume.connect(self.task_model.resume_queue)
        
        # 连接状态反馈信号
        self.task_model.status_changed.connect(self._on_status_changed)
        self.task_model.running_task_changed.connect(self._on_running_task_changed)
        self.task_model.queue_paused_changed.connect(self._on_paused_changed)
        self.task_model.progress_changed.connect(self._on_progress_changed)
        
        # 线程清理逻辑
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.task_model.deleteLater)
        
        # 启动线程的事件循环（注意：这不会启动任务，只是让 QObject 在线程里活起来）
        self.worker_thread.start()

        # 内部状态缓存
        self.task_model_status = {
            "overall_status": "未运行",
            "current_task": "无",
            "progress": 0,
            "is_paused": False
        }
        self.status = "未运行"

    # --- 信号处理槽函数 ---
    def _on_status_changed(self, status: str):
        """
        处理任务状态变化信号.
        
        Args:
            status (str): 任务状态字符串.
        """
        self.task_model_status["overall_status"] = status
        if self.status != status:
            self.status = status
            self.status_signal.emit(status)
        self._emit_status_update()

    def _on_running_task_changed(self, task_name: str, index: int):
        """
        处理当前运行任务变化信号.
        
        Args:
            task_name (str): 当前运行的任务名称.
            index (int): 当前运行任务在队列中的索引.
        """
        self.task_model_status["current_task"] = task_name
        self.task_model_status["progress"] = self.task_model.get_progress() 
        self._emit_status_update()

    def _on_paused_changed(self, is_paused: bool):
        """
        处理队列暂停状态变化信号.
        
        Args:
            is_paused (bool): 队列是否暂停.
        """
        self.task_model_status["is_paused"] = is_paused
        self._emit_status_update()

    def _on_progress_changed(self, progress: int):
        """
        处理任务进度变化信号.
        
        Args:
            progress (int): 任务进度值.
        """
        self.task_model_status["progress"] = progress
        self._emit_status_update()

    def _emit_status_update(self):
        """
        发送任务状态更新信号.
        """
        self.task_model_status_signal.emit(self.handle, self.task_model_status)

    # --- 统一控制接口 ---
    def start_process(self):
        """
        发送启动信号
        """
        if self.multi_run:
            self.sig_start.emit()

    def stop_process(self):
        """
        发送停止信号
        """
        if self.multi_run:
            self.sig_stop.emit()

    def pause_process(self):
        """
        发送暂停信号
        """
        if self.multi_run:
            self.sig_pause.emit()

    def resume_process(self):
        """
        发送恢复信号
        """
        if self.multi_run:
            self.sig_resume.emit()

    def kill_process(self):
        """
        终止线程
        """
        if self.multi_run:
            if self.task_model:
                self.task_model.stop_queue()

            self.task_model.wait_for_stop(1.0)
            # 退出 QThread 的事件循环
            self.worker_thread.quit()
            
            # 等待线程结束
            if not self.worker_thread.wait(1000): 
                # 强制终止
                print(f"线程 {self.handle} 响应超时，强制清理...")
                self.worker_thread.terminate()
                self.worker_thread.wait()

    def change_task_list(self, tasks: list[str] = []):
        """
        改变当前进程的任务列表. 
        """
        if self.task_model:
            self.task_model.add_task_multiple(tasks)