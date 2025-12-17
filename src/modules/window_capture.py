
import win32gui
import win32ui
import win32con
import numpy as np
from cv2 import cvtColor, COLOR_BGRA2BGR, imwrite
import os
from typing import Optional, Tuple


class WindowCapture:
    """
    捕获指定窗口画面.
    """

    def __init__(self):
        """
        初始化窗口捕获器.
        """
        self.hwnd = None
        self.cache = None

    def set_hwnd(self, hwnd: int):
        """
        设置目标窗口句柄.

        Args:
            hwnd: 目标窗口的句柄
        """
        self.hwnd = hwnd

    def get_window_size(self) -> Optional[Tuple[int, int]]:
        """
        获取窗口尺寸.

        Returns:
            窗口尺寸(Optional[Tuple[int, int]]): 窗口的宽度和高度 (width, height)，如果窗口无效则返回 None
        """
        if not self.hwnd:
            return None
        left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
        w = right - left
        h = bottom - top
        if not w or not h:
            return None
        return (w, h)

    def capture(self) -> Optional[np.ndarray]:
        """
        截取画面并缓存.

        截取目标窗口的画面并将其缓存到内存中。

        Returns:
            截图图像(Optional[np.ndarray]): 截图图像，截取失败则返回None
        """
        if not self.hwnd:
            return None

        # 获取窗口区域(客户端)
        left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
        w = right - left # 减去窗口边框宽度
        h = bottom - top # 减去窗口标题栏高度

        # 获取设备上下文
        # 如果使用 GetWindowDC，(0,0) 坐标会包含标题栏
        hwndDC = win32gui.GetDC(self.hwnd) 
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)

        # 截图
        try:
            # (0, 0) => 目标 DC 的左上角
            # (w, h) => 复制的宽高
            # mfcDC  => 源 DC
            # (0, 0) => 源 DC 的左上角
            saveDC.BitBlt((0, 0), (w, h), mfcDC, (0, 0), win32con.SRCCOPY)
            result = True
        except win32ui.error:
            result = None

        # 从 bitmap 提取数据
        # bmpinfo = saveBitMap.GetInfo() # 可选
        bmpstr = saveBitMap.GetBitmapBits(True)

        # 将字节流转换为 numpy 数组（BGRX → BGR）
        img = np.frombuffer(bmpstr, dtype=np.uint8)
        
        # 防止窗口大小变化导致数据不匹配
        if len(img) == w * h * 4:
            img = img.reshape((h, w, 4))       # 4通道：B, G, R, X
            frame = cvtColor(img, COLOR_BGRA2BGR)
            self.cache = frame
        else:
            print(f"截图数据尺寸不匹配: 预期 {w*h*4}, 实际 {len(img)}")
            result = None
            frame = None

        # 清理资源
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwndDC)

        if result is None:
            print("捕获失败（或窗口无效）")
            return None

        # print(f"捕获成功，尺寸：{frame.shape[1]}x{frame.shape[0]}")
        return frame

    def get_cache(self) -> Optional[np.ndarray]:
        """
        获取缓存图像.

        Returns:
            缓存图像(Optional[np.ndarray]): 缓存的图像，未缓存则返回None
        """
        if self.cache is None:
            print("当前没有缓存画面，请先调用 capture()")
            return None
        return self.cache

    def save_cache(self, filename: str = "capture.png") -> bool:
        """
        保存缓存图像.

        将缓存的图像保存到指定文件。

        Args:
            filename: 保存的文件名，默认为"capture.png"

        Returns:
            保存结果(bool): 保存成功返回True，否则返回False
        """
        if self.cache is None:
            print("当前没有缓存画面")
            return False

        imwrite(filename, self.cache)
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
    wc = WindowCapture()
    frame = wc.capture()
    if frame is not None:
        wc.save_cache("test_capture.png")