from PySide6.QtCore import QObject, Signal
import win32gui
import re
from ...ui.core.logger import logger

class WindowManager(QObject):
    """
    窗口管理器：负责查找、连接和验证游戏窗口。
    """
    # 信号
    connected = Signal(int, str)  # 成功连接 (hwnd, title)
    disconnected = Signal()       # 连接断开/未找到

    def __init__(self, log_mode: int = 0):
        super().__init__()
        self.hwnd = None
        self.window_title = ""
        self.log_mode = log_mode

    def connect_by_title(self, title_pattern: str) -> bool:
        """
        通过标题关键词查找并连接窗口
        Args:
            title_pattern (str): 标题关键词或正则表达式
        """
        target_handles = []

        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                curr_title = win32gui.GetWindowText(hwnd)
                # 使用正则忽略大小写匹配
                if curr_title and re.search(title_pattern, curr_title, re.IGNORECASE):
                    extra.append(hwnd)
            return True

        try:
            win32gui.EnumWindows(callback, target_handles)
        except Exception as e:
            logger.error(f"枚举窗口出错: {e}", mode=self.log_mode)
            return False
        
        if target_handles:
            # 默认取第一个
            self.hwnd = target_handles[0]
            self.window_title = win32gui.GetWindowText(self.hwnd)
            
            self.connected.emit(self.hwnd, self.window_title)
            logger.info(f"成功连接窗口: {self.window_title} (HWND: {self.hwnd})", mode=self.log_mode)
            return True
        else:
            self.hwnd = None
            self.disconnected.emit()
            logger.error(f"未找到包含 '{title_pattern}' 的窗口", mode=self.log_mode)
            return False
        
    def get_windows_by_filter(self, title_pattern: str) -> list[int]:
        """
        查找所有符合标题规则的窗口句柄
        Args:
            title_pattern (str): 标题关键词或正则表达式
        Returns:
            list[int]: 符合规则的窗口句柄列表
        """
        result_handles = []
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                curr_title = win32gui.GetWindowText(hwnd)
                if curr_title and re.search(title_pattern, curr_title, re.IGNORECASE):
                    extra.append(hwnd)
            return True
        
        try:
            win32gui.EnumWindows(callback, result_handles)
        except Exception:
            pass
        return result_handles

    def connect_by_hwnd(self, hwnd: int) -> bool:
        """
        直接通过句柄连接 (主要用于多开模式)
        """
        if win32gui.IsWindow(hwnd):
            self.hwnd = hwnd
            try:
                self.window_title = win32gui.GetWindowText(hwnd)
                self.connected.emit(self.hwnd, self.window_title)
                return True
            except Exception:
                return False
        else:
            self.hwnd = None
            self.disconnected.emit()
            return False

    def is_active(self) -> bool:
        """
        检查当前持有的句柄是否依然有效且可见
        """
        if not self.hwnd:
            return False
        return bool(win32gui.IsWindow(self.hwnd)) and bool(win32gui.IsWindowVisible(self.hwnd))

    def get_hwnd(self) -> int | None:
        """
        获取当前持有的窗口句柄
        """
        return self.hwnd

    def get_title(self) -> str:
        """
        获取当前持有的窗口标题
        """
        return self.window_title