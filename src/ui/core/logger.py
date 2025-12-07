from PySide6.QtCore import QObject, Signal
import threading
import datetime
import atexit

class _Logger(QObject):
    """
    日志类，用于在 UI 中显示日志信息.
    """
    log_signal = Signal(str, str)
    log_multiprocess_signal = Signal(str, str)

    auto_save = True
    # 单例模式
    _instance = None
    _lock = threading.Lock()
    log_cache = []  # 日志缓存

    def __new__(cls):
        """
        单例模式，确保只有一个 Logger 实例.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                atexit.register(cls._instance._auto_save) # 程序退出时自动保存日志
                cls._process_queue = None # 进程队列
                cls.process_queue_mode = False
        return cls._instance
    
    def set_process_queue(self, queue):
        """
        设置进程队列，用于多开窗口日志输出.

        Args:
            queue (Queue): 进程队列，用于存储日志消息.
        """
        self._process_queue = queue
        self.process_queue_mode = True

    def log(self, message: str, type: str = "INFO", mode: int = 0):
        """
        发送日志消息到 UI.

        Args:
            message (str): 要发送的日志消息.
            type (str): 日志类型，默认值为 "INFO".
            mode (int): 日志模式，0代表同时发送给ui和文件, 1代表仅保存到文件， 2代表只发送给ui，3代表多开窗口日志输出，默认值为0.
        """
        ts = self.get_time()
        msg = f"{ts} [{type}] {message}"

        # 仅保存到文件
        if mode == 1:
            self.add_log_to_cache(message=msg)
            return

        # 多开窗口日志输出，通过进程队列发送
        if self._process_queue is not None:
            self._process_queue.put((type, msg))
            return
        
        if mode == 0:
            self.log_signal.emit(msg, type)
            self.add_log_to_cache(message=msg)
        elif mode == 1:
            self.add_log_to_cache(message=msg)
        elif mode == 2:
            self.log_signal.emit(msg, type)
        elif mode == 3:
            msg = f"[多开]{msg}"
            self.log_multiprocess_signal.emit(msg, type)
            self.add_log_to_cache(message=msg)


    def info(self, message: str, mode: int = 0):
        """
        发送信息日志消息到 UI.

        Args:
            message (str): 要发送的信息日志消息.
            mode (int, optional): 日志模式，0代表同时发送给ui和文件, 1代表保存到文件， 2代表只发送给ui，默认值为0.
        """
        self.log(f"{message}", type="INFO", mode=mode)

    def error(self, message: str, mode: int = 0):
        """
        发送错误日志消息到 UI.

        Args:
            message (str): 要发送的错误日志消息.
            mode (int, optional): 日志模式，0代表同时发送给ui和文件, 1代表保存到文件， 2代表只发送给ui，默认值为0."""
        self.log(f"{message}", type="ERROR", mode=mode)

    def warning(self, message: str, mode: int = 0):
        """
        发送警告日志消息到 UI.

        Args:
            message (str): 要发送的警告日志消息.
            mode (int, optional): 日志模式，0代表同时发送给ui和文件, 1代表保存到文件， 2代表只发送给ui，默认值为0.`"""
        self.log(f"{message}", type="WARN", mode=mode)

    def get_time(self):
        """
        获取当前时间.

        Returns:
            str: 当前时间，格式为 "[HH:MM:SS]".
        """
        return datetime.datetime.now().strftime("[%H:%M:%S]")
    
    def save_log_to_file(self, file_path: str="log.txt"):
        """
        将日志消息保存到文件.

        Args:
            file_path (str): 日志文件路径.
            message (str): 要保存的日志消息.
        """
        with open(file_path, "a", encoding="utf-8") as f:
            f.write("\n".join(self.log_cache) + "\n")

    def _auto_save(self):
        """
        自动保存日志到文件.
        """
        if self.auto_save:
            self.save_log_to_file("log.txt")

    def add_log_to_cache(self, message: str=""):
        """
        将日志消息添加到缓存.

        Args:
            message (str): 要添加的日志消息.
        """
        self.log_cache.append(message)

    def set_auto_save(self, auto_save: bool):
        """
        设置是否自动保存日志.

        Args:
            auto_save (bool): 是否自动保存日志.
        """
        self.auto_save = auto_save

# 全局实例
logger = _Logger()
