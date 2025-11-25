from PySide6.QtCore import QObject, Signal
import threading
import datetime


class _Logger(QObject):
    """
    日志类，用于在 UI 中显示日志信息.
    """
    log_signal = Signal(str, str)

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        单例模式，确保只有一个 Logger 实例.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def log(self, message: str, type: str = "INFO"):
        """
        发送日志消息到 UI.

        Args:
            message (str): 要发送的日志消息.
            type (str, optional): 日志类型，默认值为 "INFO".
        """
        ts = self.get_time()
        text = f"{ts} [{type}] {message}"
        self.log_signal.emit(text, type)  # 发给 UI

    def info(self, message: str):
        """
        发送信息日志消息到 UI.

        Args:
            message (str): 要发送的信息日志消息.
        """
        self.log(f"{message}", type="INFO")

    def error(self, message: str):
        """
        发送错误日志消息到 UI.

        Args:
            message (str): 要发送的错误日志消息.
        """
        self.log(f"{message}", type="ERROR")

    def warning(self, message: str):
        """
        发送警告日志消息到 UI.

        Args:
            message (str): 要发送的警告日志消息.
        """
        self.log(f"{message}", type="WARN")

    def get_time(self):
        """
        获取当前时间.

        Returns:
            str: 当前时间，格式为 "[HH:MM:SS]".
        """
        return datetime.datetime.now().strftime("[%H:%M:%S]")

# 全局实例
logger = _Logger()
