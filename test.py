from src.modules.template_matcher import TemplateMatcher
from src.modules.window_capture import WindowCapture
import win32gui
import numpy as np
import cv2

if __name__ == "__main__":
    capture = WindowCapture()
    hwnd = win32gui.FindWindow(None, "一梦江湖")
    capture.set_hwnd(hwnd)
    template_path = "template_img/jiang_hu_ji_shi_1.png"
    # screenshot = capture.capture()
    screenshot = cv2.imread("template_img/555.png")
    matcher = TemplateMatcher(template_path=template_path, base_window_size=(2560, 1330))
    matcher.set_template(template_path)
    # 加载截图
    if screenshot is None:
        raise ValueError(f"无法加载截图")

    print(capture.get_window_size())
    match_result = matcher.match_scaled(screenshot, threshold=0.2)
    if match_result is not None:
        center, match_val = match_result
        print(f"匹配到模板，中心坐标: {center}，匹配值: {match_val}")
        matcher.visualize_match(screenshot)
    else:
        print("未匹配到模板")