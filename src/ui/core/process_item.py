from ..models.task_model import TaskModel
from multiprocessing.connection import Connection
from PySide6.QtCore import QObject, Signal

# 继承 QObject 以便转发单开模式下的信号
class ProcessItem(QObject):
    status_signal = Signal(str) # hwnd_str, status
    task_model_status_signal = Signal(int, object) # hwnd, task_model_status

    def __init__(self, handle: int, name: str = "", multi_run=False, tasks: list[str] = []):
        super().__init__()
        self.handle = handle
        self.name = name
        self.multi_run = multi_run

        # 这里只是个占位或者用于获取配置，真正运行的是子进程里的 TaskModel
        self.task_model: TaskModel = self.create_task_model(handle, name, multi_run, tasks) # type: ignore

        self.process = None
        self.conn: Connection = None # type: ignore # 管道连接，用于给子进程发指令
        self.log_queue = None
        self.is_connected = False

        # 状态信息
        self.status = "未运行"
        self.running = False
        self.paused = False

        self.task_model_status = {
            "overall_status": "未运行", # TaskModel 的整体状态 (e.g., "空闲", "运行中")
            "current_task": "无",       # 当前运行的任务名称
            "progress": 0,              # 当前任务的进度 (0-100)
            "is_paused": False          # 队列是否暂停
        }

    def create_task_model(self, hwnd: int, name: str = "", multi_run=False, tasks: list[str] = []):
        try:
            model = TaskModel(hwnd=hwnd, name=name, multi_run_mode=multi_run)
            model.add_task_multiple(tasks)
            return model
        except Exception as e:
            print(f"创建 TaskModel 失败: {e}")
            return None
        
    def update_task_model_status(self, status_data: dict):
        """
        接收并处理从子进程 TaskModel 传来的实时状态更新。
        status_data 格式: {"type": "...", "data": ...}
        """
        status_type = status_data.get("type")
        data = status_data.get("data")
        
        # 根据类型更新内部状态字典
        if status_type == "status_changed":
            self.task_model_status["overall_status"] = data
            # 同时更新外部的进程状态，保持一致性
            if self.status != data:
                self.status = data 
                self.status_signal.emit(self.status)
                
        elif status_type == "running_task_changed":
            self.task_model_status["current_task"] = data.get("task_name", "无") # type: ignore
            self.task_model_status["progress"] = data.get("progress", 0) # type: ignore
            
        elif status_type == "queue_paused_changed":
            self.task_model_status["is_paused"] = data

        # 发射详细状态信号，通知所有连接的 UI 组件
        self.task_model_status_signal.emit(self.handle, self.task_model_status)


    def stop_process(self):
        """
        统一停止接口：支持单开和多开
        """
        try:
            if self.multi_run:
                if self.conn: self.conn.send("stop")
                self.status = "已停止"
                self.status_signal.emit(self.status)
                
        except Exception as e:
            print(f"Stop process error: {e}")

    def pause_process(self):
        """
        统一暂停接口
        """
        try:
            if self.multi_run:
                if self.conn: self.conn.send("pause")
                self.status = "暂停中"
                self.status_signal.emit(self.status)
        except Exception as e:
            pass

    def resume_process(self):
        """
        统一恢复接口
        """
        try:
            if self.multi_run:
                if self.conn: self.conn.send("resume")
                self.status = "运行中"
                self.status_signal.emit(self.status)
        except Exception as e:
            pass

    def start_process(self):
        """
        统一启动接口
        """
        try:
            if self.multi_run:
                if self.conn: self.conn.send("start")
                self.status = "运行中"
                self.status_signal.emit(self.status)
        except Exception as e:
            pass

    def kill_process(self):
        """
        统一终止接口
        """
        try:
            if self.multi_run:
                if self.conn: self.conn.send("kill")
                self.status = "已终止"
                self.status_signal.emit(self.status)

                # 等待进程结束
                if self.process and self.process.is_alive():
                    self.process.join(timeout=1)
                    if self.process.is_alive():
                        self.process.terminate() # 强杀
        except Exception as e:
            pass

    def change_task(self, tasks: list[str] = []):
        """
        改变当前进程的任务列表.
        """
        if self.task_model:
            self.task_model.add_task_multiple(tasks)
