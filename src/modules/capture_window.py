
from ctypes import windll
import win32gui
import win32ui
import numpy as np
import cv2
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
        try:
            self.hwnd = win32gui.FindWindow(None, self.window_title)  # 获取窗口的句柄
        except IndexError:
            print(f"未找到标题包含 '{self.window_title}' 的窗口")
            return None
        return self.hwnd

    def get_window_size(self):
        """
        获取窗口尺寸.

        Returns:
            tuple: 窗口的宽度和高度 (width, height)
        """
        if not self.hwnd:
            if not self.find_window():
                return None
            if not self.hwnd:
                return None
        left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
        w = right - left
        h = bottom - top
        if not w or not h:
            return None
        return (w, h)

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
            
        # 统一处理DPI,防止高DPI显示器导致截图尺寸异常
        try:
            windll.user32.SetProcessDPIAware()
        except AttributeError:
            print("当前Windows版本为:", os.environ.get('OS'))
            print("SetProcessDPIAware 函数不存在，请假查Windows版本是否支持")

        # 获取窗口区域(客户端)
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        w = right - left - 19 # 减去窗口边框宽度
        h = bottom - top - 48 # 减去窗口标题栏高度

        hwndDC = win32gui.GetWindowDC(self.hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)

        # 截图
        result = windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 1)

        # 从 bitmap 提取数据
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        # 将字节流转换为 numpy 数组（BGRX → BGR）
        img = np.frombuffer(bmpstr, dtype=np.uint8)
        img = img.reshape((h, w, 4))       # 4通道：B, G, R, X
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # 清理资源
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwndDC)

        if result is None:
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