
import win32gui
import win32con
import ctypes

if __name__ == "__main__":
    user32 = ctypes.windll.user32

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    hwnd = win32gui.FindWindow(None, "一梦江湖")

    # 恢复窗口
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    # 获取窗口样式
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

    # 目标客户端大小
    client_width = 1920
    client_height = 1080

    # 构造 RECT
    rect = RECT(0, 0, client_width, client_height)

    # 调用 Win32 API
    user32.AdjustWindowRectEx(
        ctypes.byref(rect),
        style,
        False,      # 是否有菜单
        ex_style
    )

    # 计算窗口大小
    window_width = rect.right - rect.left
    window_height = rect.bottom - rect.top

    # 设置窗口
    win32gui.MoveWindow(
        hwnd,
        0, 0,
        window_width,
        window_height,
        True
    )