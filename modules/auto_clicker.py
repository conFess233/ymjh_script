from pywinauto import Application, findwindows
from pywinauto.findwindows import ElementNotFoundError
import time

class AutoClicker:
    """
    使用 pywinauto 在后台点击指定窗口坐标.

    该类提供后台点击功能，无需移动鼠标指针即可在指定窗口的坐标位置执行点击操作。
    """

    def __init__(self, window_title: str):
        """
        初始化自动点击器.

        Args:
            window_title: 目标窗口标题
        """
        self.window_title = window_title
        self.app = None
        self.window = None
        self._connect_window()

    def _connect_window(self):
        """
        连接目标窗口.

        尝试查找并连接到指定标题的窗口。
        """
        try:
            hwnd = findwindows.find_window(title=self.window_title)
            self.app = Application().connect(handle=hwnd)
            self.window = self.app.window(handle=hwnd)
            print(f"成功连接窗口: {self.window_title} (hwnd={hwnd})")
        except ElementNotFoundError:
            print(f"未找到窗口: {self.window_title}")
        except Exception as e:
            print(f"连接窗口失败: {e}")

    def click(self, x: int, y: int, delay: float = 0.05) -> bool:
        """
        后台点击窗口内坐标（不移动鼠标）.

        在指定窗口的坐标位置执行点击操作，不会移动实际的鼠标指针。

        Args:
            x: 点击位置的x坐标
            y: 点击位置的y坐标
            delay: 点击后的延迟时间（秒），默认为0.05秒

        Returns:
            bool: 点击成功返回True，失败返回False
        """
        if not self.window:
            print("窗口未连接，无法点击")
            return False
        try:
            self.window.click(coords=(x, y))
            print(f"成功点击 ({x}, {y})")
            time.sleep(delay)
            return True
        except Exception as e:
            print(f"点击失败: {e}")
            return False

    def is_window_ready(self) -> bool:
        """检查窗口是否仍然存在.

        Returns:
            bool: 窗口存在且可用返回True，否则返回False
        """
        return self.window is not None and self.window.exists()