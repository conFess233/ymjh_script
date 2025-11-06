import win32api
import win32gui
import numpy as np
import cv2
import dxcam
import os


class WindowCapture:
    """
    用于捕获指定窗口画面的类.

    功能：
      自动查找目标窗口
      截取一次画面
      临时缓存画面
      获取、保存或清空缓存
    """

    def __init__(self, window_title: str = ""):
        """
        初始化窗口捕获器.

        Args:
            window_title: 目标窗口标题（支持模糊匹配）
        """
        self.window_title = window_title
        self.hwnd = None
        self.cache = None

    def find_window(self):
        """
        查找目标窗口.

        通过枚举所有可见窗口并匹配标题来查找目标窗口。

        Returns:
            int or None: 找到的窗口句柄，未找到则返回None
        """
        def enum_windows(hwnd, result):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if self.window_title.lower() in title.lower():
                    result.append((hwnd, title))

        windows = []
        win32gui.EnumWindows(enum_windows, windows)
        if not windows:
            print(f"未找到标题包含 '{self.window_title}' 的窗口")
            return None

        hwnd, title = windows[0]
        self.hwnd = hwnd
        # print(f"选用窗口: hwnd={hwnd}, title={title}")
        return hwnd

    def get_window_size(self):
        """
        获取窗口尺寸.

        Returns:
            tuple: 窗口的宽度和高度 (width, height)
        """
        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        return (screen_width, screen_height)

    def capture(self):
        """
        截取画面并缓存.

        截取目标窗口的画面并将其缓存到内存中。

        Returns:
            numpy.ndarray: 截图图像，截取失败则返回None
        """
        if not self.hwnd:
            if not self.find_window():
                return None
            if not self.hwnd:
                return None

        # 获取客户区尺寸（不含标题栏和边框）
        client_rect = win32gui.GetClientRect(self.hwnd)
        client_left_top = win32gui.ClientToScreen(self.hwnd, (0, 0))
        left = client_left_top[0]
        top = client_left_top[1]
        right = left + client_rect[2]
        bottom = top + client_rect[3]
        rect = (left, top, right, bottom)
        # print(f"客户区区域: {rect}")

        # 屏幕尺寸
        screen_width, screen_height = self.get_window_size()
        rect = (
            max(0, min(rect[0], screen_width - 1)),
            max(0, min(rect[1], screen_height - 1)),
            max(1, min(rect[2], screen_width)),
            max(1, min(rect[3], screen_height)),
        )

        # 捕获画面
        cam = dxcam.create(output_color="BGR")
        frame = cam.grab(region=rect)

        if frame is None:
            print("捕获失败（窗口可能被最小化或遮挡）")
            return None

        self.cache = frame
        # print(f"捕获成功，尺寸：{frame.shape[1]}x{frame.shape[0]}")
        return frame

    def get_cache(self):
        """
        获取缓存图像.

        Returns:
            numpy.ndarray or None: 缓存的图像，未缓存则返回None
        """
        if self.cache is None:
            print("当前没有缓存画面，请先调用 capture()")
            return None
        return self.cache

    def save_cache(self, filename: str = "capture.png"):
        """
        保存缓存图像.

        将缓存的图像保存到指定文件。

        Args:
            filename: 保存的文件名，默认为"capture.png"

        Returns:
            bool: 保存成功返回True，否则返回False
        """
        if self.cache is None:
            print("当前没有缓存画面")
            return False

        cv2.imwrite(filename, self.cache)
        print(f"已保存缓存画面：{os.path.abspath(filename)}")
        return True

    def clear_cache(self):
        """
        清空缓存.

        清空当前缓存的图像数据。
        """
        self.cache = None
        # print("已清空缓存")


if __name__ == "__main__":
    wc = WindowCapture("一梦江湖")
    frame = wc.capture()
    if frame is not None:
        wc.save_cache("test_capture.png")