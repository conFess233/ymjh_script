from PySide6.QtCore import QObject, Signal
import threading
import datetime


class _Logger(QObject):
    """
    日志类，用于在 UI 中显示日志信息.
    """
    log_signal = Signal(str)

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

    def log(self, message: str):
        """
        发送日志消息到 UI.

        Args:
            message (str): 要发送的日志消息.
        """
        ts = datetime.datetime.now().strftime("[%H:%M:%S]")
        text = f"{ts} {message}"
        self.log_signal.emit(text)  # 发给 UI


# 全局实例
logger = _Logger()
