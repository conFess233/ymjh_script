import random
import time
import win32api
import win32con
import win32gui


class AutoClicker:
    """
    使用 pywinauto 在后台点击指定窗口坐标.

    该类提供后台点击功能，无需移动鼠标指针即可在指定窗口的坐标位置执行点击操作。
    """

    def __init__(self):
        """
        初始化自动点击器.

        Args:
            window_title: 目标窗口标题
        """
        self.hwnd = None

    def connect_window(self):
        # 简单检查句柄有效性
        if self.hwnd and not win32gui.IsWindow(self.hwnd):
            raise Exception(f"无效的句柄: {self.hwnd}")
    
    def set_hwnd(self, hwnd: int):
        """
        设置目标窗口句柄.

        Args:
            hwnd: 目标窗口的句柄
        """
        self.hwnd = hwnd

    def click(self, x: int, y: int, random_range: int | tuple = 0) -> bool:
        """
        后台点击窗口内坐标（不移动鼠标）.

        在指定窗口的坐标位置执行点击操作，不会移动实际的鼠标指针。

        Args:
            x: 点击位置的x坐标
            y: 点击位置的y坐标
            random_range: 随机点击范围（整数或元组），默认为0。
                如果为整数，点击坐标将在该范围内随机偏移。
                如果为元组 (dx, dy)，点击坐标将在该范围内随机偏移。

        Returns:
            bool: 点击成功返回True，失败返回False
        """
        if not self.hwnd:
            print("窗口未连接，无法点击")
            return False
        
        if isinstance(random_range, tuple):
            rx, ry = random_range
        else:
            rx = ry = random_range
        
        cx = x + random.randint(int(-rx / 2), int(rx / 2))
        cy = y + random.randint(int(-ry / 2), int(ry / 2))
        print(random_range)

        # 组合坐标参数 (高位y, 低位x)
        lparam = win32api.MAKELONG(cx, cy)

        try:
            # 使用 PostMessage 发送点击消息，不需要激活窗口
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
            # 加上微小的延迟模拟真实点击
            time.sleep(random.uniform(0.05, 0.15)) 
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lparam)
            return True
        except Exception as e:
            print(f"点击失败: {e}")
            return False

    def is_window_ready(self) -> bool:
        """
        检查窗口是否仍然存在.

        Returns:
            bool: 窗口存在且可用返回True，否则返回False
        """
        return bool(self.hwnd is not None and win32gui.IsWindow(self.hwnd))
    
