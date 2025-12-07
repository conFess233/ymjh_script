import win32gui
import re
import sys
import traceback
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from multiprocessing import Process, Pipe, Queue
from typing import Optional
from queue import Empty
from PySide6.QtCore import QCoreApplication
from .process_item import ProcessItem
from ..models.task_model import TaskModel
from ..core.logger import logger

def run_task_process(hwnd, tasks, conn, log_queue):
    """
    子进程任务执行函数，负责处理任务队列和与主进程通信。

    Args:
        hwnd: 窗口句柄，用于连接到目标窗口。
        tasks: 任务列表，每个任务是一个字典，包含任务名称和参数。
        conn: 子进程与主进程通信的 Pipe 连接。
        log_queue: 用于日志记录的队列，用于将子进程日志发送到主进程。
    """
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)
    # log_queue.put(('INFO', f"子进程已启动 PID: {os.getpid()}"))
    try:
        logger.set_process_queue(log_queue)
        
        model = TaskModel(hwnd=hwnd, multi_run_mode=True, log_mode=3)
        model.add_task_multiple(tasks)

        # 检查窗口是否可以连接
        if not model.connect_window():
            log_queue.put(('ERROR', f"子进程启动失败：窗口句柄 {hwnd} 连接失败。"))
            return # 窗口连接失败直接退出子进程
        
        def send_model_status(status_type: str, data):
            """
            将 TaskModel 的状态信息通过 Pipe 推送回主进程
            """
            try:
                message = {"type": status_type, "data": data}
                conn.send(message)
            except Exception as e:
                # 如果主进程关闭，直接终止程序
                log_queue.put(('ERROR', f"发送TaskModel状态失败: {e}"))
                sys.exit(1) # 主进程关闭，子进程也退出

        # 连接任务状态变化信号
        model.status_changed.connect(lambda status: send_model_status("status_changed", status))
            
        # 连接当前运行任务变化信号 (任务名, 进度)
        model.running_task_changed.connect(
                lambda name, progress: send_model_status("running_task_changed", {"task_name": name, "progress": progress})
            )

        # 连接队列暂停状态变化信号
        model.queue_paused_changed.connect(lambda paused: send_model_status("queue_paused_changed", paused))

        class PipeHandler(QObject):
            # 信号在主进程中用来退出，在子进程中没必要，因为子进程会在模型退出后自动退出
            stop_process = Signal() 

            def __init__(self, conn, model, log_queue, parent=None):
                super().__init__(parent)
                self.conn = conn
                self.model = model
                self.log_queue = log_queue
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.check_pipe)
                self.timer.start(100) # 每 100ms 检查一次 Pipe

            def check_pipe(self):
                try:
                    if self.conn.poll(0):
                        received = self.conn.recv()
                        if isinstance(received, str):
                            cmd = received
                            data = None
                        elif isinstance(received, tuple) and len(received) > 0:
                            cmd = received[0]
                            data = received[1] if len(received) > 1 else None
                        try:
                            if cmd == "start":
                                self.model.start_queue()
                            elif cmd == "stop":
                                self.model.stop_queue()
                            elif cmd == "pause":
                                self.model.pause_queue()
                            elif cmd == "resume":
                                self.model.resume_queue()
                            elif cmd == "kill":
                                self.model.stop_queue()
                                QCoreApplication.quit()
                                self.stop_process.emit()
                            elif cmd == "get_task_list":
                                self.conn.send(self.model.get_run_task_list_names())
                            elif cmd == "set_task_list" and data is not None and isinstance(data, list):
                                model.add_task_multiple(data)
                            else:
                                self.log_queue.put(('WARNING', f"未知命令: {cmd}"))
                        except EOFError:
                            self.log_queue.put(('WARNING', "管道断开，子进程退出。"))
                            QCoreApplication.quit()
                        except Exception as e:
                            self.log_queue.put(('ERROR', f"处理 Pipe 命令失败: {e}"))
                except Exception as e:
                    # 为防止意外情况导致的无限循环，这里如果检查到 Pipe 异常，直接退出子进程
                    self.log_queue.put(('ERROR', f"检查 Pipe 命令失败: {e}, 子进程退出。"))
                    sys.exit(1)
                
        handler = PipeHandler(conn, model, log_queue)
        
        # 强制执行一次 Pipe 检查，以立即响应主进程在启动期间发出的同步请求
        try:
            handler.check_pipe()
        except Exception as e:
            # 忽略或记录首次检查失败，但不要退出
            log_queue.put(('WARNING', f"子进程首次 Pipe 检查失败: {e}"))

        sys.exit(app.exec()) # 运行 Qt 事件循环，阻塞直到收到退出指令
        
    except Exception as e:
        error_msg = f"子进程启动/运行时发生未捕获的致命异常: {e}\n{traceback.format_exc()}"
        log_queue.put(('ERROR', error_msg))
        # 退出子进程
        sys.exit(1)

class MultipleProcessManager(QObject):

    process_item_changed = Signal(object)  # 进程项变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: dict[int, ProcessItem] = {} # hwnd -> ProcessItem
        self.log_mode: int = 3  # 默认日志模式
        self.log_queue = None  # 日志队列，用于多开窗口日志输出

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._poll_all_task_status)
        self.status_timer.start(100) # 每 100ms 检查一次所有管道

        # IPC 线程
        self.ipc_thread = IPCThread(self)
        self.ipc_thread.result_signal.connect(self._on_ipc_result)
        self.ipc_thread.start()

        # 回调缓存
        self.pending_callbacks = {}  # hwnd -> callback

    def request_task_list(self, hwnd, callback):
        """
        请求指定窗口的任务列表.
        Args:
            hwnd (int): 窗口句柄.
            callback (callable): 接收任务列表的回调函数.
        """
        if hwnd not in self.items:
            callback(None)
            return

        self.pending_callbacks[hwnd] = callback
        self.ipc_thread.queue.put((hwnd, "get_task_list"))

    def _on_ipc_result(self, hwnd, data):
        """
        处理 IPC 线程返回的任务列表.
        Args:
            hwnd (int): 窗口句柄.
        """
        cb = self.pending_callbacks.pop(hwnd, None)
        if cb:
            cb(data)

    def stop_all(self):
        if hasattr(self, "ipc_thread"):
            self.ipc_thread.stop()
            self.ipc_thread.wait()

    def get_target_window_handles(self, target_title_part: str) -> list:
        """
        处理 IPC 线程返回的任务列表.
        Args:
            hwnd (int): 窗口句柄.
            data (list): 任务列表.
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
    
    def add_item(self, hwnd, name="", tasks: list=[]):
        """
        添加一个新的窗口任务模型.
        Args:
            hwnd (int): 窗口句柄.
        """
        if hwnd in self.items:
            logger.warning(f"{hwnd} 已存在，不重复创建", mode=self.log_mode)
            return self.items[hwnd]
        try:
            item = ProcessItem(hwnd, name, multi_run=True, tasks=tasks)
            logger.info(f"添加进程成功: {item.handle} - {item.name}", mode=1) # 修改下日志模式，添加成功之类的日志不再显示到ui上
        except Exception as e:
            logger.error(f"创建 ProcessItem 实例时出错: {e}", mode=self.log_mode)
            return None # type: ignore
        self.items[hwnd] = item
        self.start_multiprocess(item, tasks)
        self.process_item_changed.emit(self.get_all_items())
        

    def remove_item(self, hwnd: int):
        """
        移除一个窗口任务模型.
        如果窗口句柄不存在, 则忽略.
        Args:
            hwnd (int): 窗口句柄.
        """
        if hwnd in self.items:
            name = self.items[hwnd].name
            self.items[hwnd].kill_process()
            del self.items[hwnd]
            self.process_item_changed.emit(self.get_all_items())
            logger.info(f"移除成功: {hwnd} - {name}", mode=1)
        else:
            logger.warning(f"窗口句柄: {hwnd} 的 进程不存在，无法移除", mode=self.log_mode)

    def clear_items(self):
        """
        清空所有窗口任务模型.
        """
        if not self.items:
            logger.warning(f"无进程可清空", mode=self.log_mode)
            return
        for item in self.items.values():
            item.kill_process()
        self.items.clear()
        self.process_item_changed.emit(self.get_all_items())
        logger.info(f"已清空所有进程", mode=1)

    def get_item(self, hwnd: int) -> ProcessItem:
        """
        获取指定窗口句柄的任务模型.
        Args:
            hwnd (int): 窗口句柄.
        Returns:
            ProcessItem: 任务模型实例.
        """
        if hwnd in self.items:
            return self.items[hwnd]
        else:
            logger.error(f"窗口句柄: {hwnd} 的进程不存在", mode=self.log_mode)
            return None # type: ignore

    def list_items(self):
        """
        返回当前管理的所有窗口任务模型的句柄列表.
        """
        return list(self.items.keys())


    def start_multiprocess(self, item: ProcessItem, tasks: list[str]):
        """
        启动一个多开进程
        """
        if item.running:
            logger.warning(f"{item.handle} 进程已在运行", mode=self.log_mode)
            return

        # 创建双向管道：parent_conn 给主进程用，child_conn 给子进程用
        parent_conn, child_conn = Pipe()
        
        # 使用传入的 log_queue，如果没有则新建（通常 init 里已经传入了 UI 的 queue）
        target_log_queue = self.log_queue if self.log_queue else Queue()

        p = Process(
            target=run_task_process,
            args=(item.handle, tasks, child_conn, target_log_queue)
        )
        p.daemon = True # 设置为守护进程，主程序关闭时子进程自动关闭
        p.start()

        # 将控制句柄保存到 item 中
        item.process = p  # type: ignore
        item.conn = parent_conn  # type: ignore
        item.log_queue = target_log_queue # type: ignore
        item.running = True
        item.status = "运行中"
        
        logger.info(f"已启动独立进程，PID: {p.pid}, 窗口: {item.handle}, 名称: {item.name}", mode=1)

    def start_item(self, item: ProcessItem):
        """
        统一启动入口：根据 item.multi_run 自动分发
        """
        if item.multi_run:
            item.start_process()
    
        self.process_item_changed.emit(self.get_all_items())
    
    def stop_item(self, item: ProcessItem):
        try:
            logger.info(f"尝试停止进程，PID: {item.process.pid}, 窗口: {item.handle}", mode=1) # type: ignore
            item.stop_process()
        except Exception as e:
            logger.error(f"停止进程时出错: {e}", mode=self.log_mode)
        self.process_item_changed.emit(self.get_all_items())

    def get_item_name(self, hwnd: int) -> str:
        """
        获取指定窗口句柄的任务模型名称.
        Args:
            hwnd (int): 窗口句柄.
        Returns:
            str: 任务模型名称.
        """
        item = self.get_item(hwnd)
        if item:
            return item.name
        else:
            return "未知窗口"
    
    def get_all_items(self) -> dict[int, ProcessItem]:
        """
        获取所有窗口句柄对应的任务模型实例.
        Returns:
            dict[int, ProcessItem]: 窗口句柄到任务模型实例的映射.
        """
        result = {}
        for hwnd, item in self.items.items():
            result[hwnd] = item
        return result
    
    def get_process_task_list(self, hwnd: int) -> Optional[list[str]]:
        """
        通过 Pipe 向子进程请求任务列表数据。
        """
        item = self.get_item(hwnd)
        if not item:
            return None

        # 通过 Pipe 请求
        if item.conn and not item.conn.closed:
            try:
                item.conn.send("get_task_list")
                # 等待响应
                if item.conn.poll(1.0): 
                    data = item.conn.recv()
                    if isinstance(data, list):
                        return data
                logger.warning(f"获取 {hwnd} 任务列表超时或接收到无效数据。", mode=self.log_mode)
            except Exception as e:
                logger.error(f"从 {hwnd} 获取任务列表失败: {e}", mode=self.log_mode)
        return None
    
    def set_process_task_list(self, hwnd: int, new_task_names: list[str]) -> bool:
        """
        通过 Pipe 向子进程发送新的任务列表，并要求其更新。
        """
        item = self.get_item(hwnd)
        if not item or not isinstance(new_task_names, list):
            return False
        
        # 通过 Pipe 发送命令和数据
        if item.conn and not item.conn.closed:
            try:
                # 发送 (命令, 数据) 元组
                item.conn.send(("set_task_list", new_task_names))
                logger.info(f"{hwnd} 的任务列表已设置为: {new_task_names}", mode=self.log_mode)
            except Exception as e:
                logger.error(f"向 {hwnd} 设置任务列表失败: {e}", mode=self.log_mode)
        return False

    def _poll_all_task_status(self):
        """
        轮询所有子进程的 Pipe，接收 TaskModel 发送的实时状态更新，并转发给 ProcessItem。
        """
        # 遍历所有 ProcessItem
        for hwnd, item in self.items.items():
            # 确保进程正在运行且连接有效
            if item.process and item.process.is_alive() and item.conn and not item.conn.closed:
                try:
                    # 检查管道是否有待读取的数据
                    if item.conn.poll():
                        # 尽可能多地处理管道中的所有消息，避免积压
                        while item.conn.poll(0): 
                            # conn.poll(0) 非阻塞检查
                            status_data = item.conn.recv()
                            
                            # 检查接收到的数据是否是 TaskModel 状态字典
                            if isinstance(status_data, dict) and 'type' in status_data and 'data' in status_data:
                                item.update_task_model_status(status_data) 

                except Exception as e:
                    # 如果管道断开或发生其他通信错误
                    logger.error(f"从进程 {hwnd} 接收任务状态失败: {e}", mode=self.log_mode)

class LogBridge:
    """
    多进程日志桥接器.
    用于将多进程中的日志消息发送到主进程的 logger.
    """
    def __init__(self, queue):
        self.queue = queue
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll)
        self.timer.start(5)

    def poll(self):
        """
        从队列中轮询日志消息并发送到 logger.
        """
        while not self.queue.empty():
            type, msg = self.queue.get()
            msg = f"[多开]{msg}"
            logger.log_multiprocess_signal.emit(msg, type)  # 发到 UI
            logger.add_log_to_cache(msg)


class IPCThread(QThread):
    """
    IPC 线程.
    用于处理与子进程的异步通信.
    """
    result_signal = Signal(int, object)

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.queue = Queue()
        self.running = True

    def run(self):
        while self.running:
            try:
                hwnd, cmd = self.queue.get(timeout=0.1)
            except Empty:
                continue

            # 若线程已被要求停止，则立即退出
            if not self.running:
                break

            item = self.manager.get_item(hwnd)
            if not item or not item.conn or item.conn.closed:
                self.result_signal.emit(hwnd, None)
                continue

            try:
                item.conn.send(cmd)
                if item.conn.poll(2.0):
                    data = item.conn.recv()
                else:
                    data = None
            except:
                data = None

            self.result_signal.emit(hwnd, data)

    def stop(self):
        """
        安全停止线程
        """
        self.running = False
        try:
            # 往 queue 塞一个 dummy 消息让它从 get() 醒来
            self.queue.put_nowait((0, None))
        except:
            pass


