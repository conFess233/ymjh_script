import cv2
import numpy as np
from typing import Any, Dict, Optional, Tuple, List


class TemplateMatcher:
    """
    模板匹配类。

    在图片中寻找模板的坐标位置，支持随时切换模板。

    Attributes:
        template_path (Optional[str]): 当前模板图像路径。
        template (Optional[np.ndarray]): 当前模板图像。
        template_gray (Optional[np.ndarray]): 当前模板的灰度图。
        base_w (int): 基准窗口宽度。
        base_h (int): 基准窗口高度。
        last_match (Optional[Tuple[Tuple[int, int], float, Tuple[int, int]]]):
            上次匹配结果（中心点坐标、相似度分数、模板尺寸）。
        template_mask (Optional[np.ndarray]): 模板掩模，用于屏蔽背景区域。
        method (int): OpenCV 模板匹配算法标识（默认为 TM_CCOEFF_NORMED）。
    """

    def __init__(self, template_path: str, base_window_size: tuple):
        """
        初始化模板匹配器。

        Args:
            template_path (str): 模板图像路径。
            base_window_size (tuple): 基准窗口尺寸 (宽度, 高度)。
        """
        self.template_path = None
        self.template = None
        self.template_gray = None
        self.base_window_size = base_window_size
        self.base_w, self.base_h = base_window_size
        self.last_match = None
        self.method = cv2.TM_CCOEFF_NORMED  # 默认匹配方法
        self.template_mask = None

    def set_template(self, template_path: str):
        """
        加载新的模板图像。

        Args:
            template_path (str): 模板图像文件路径。

        Raises:
            FileNotFoundError: 当模板图像无法加载时抛出异常。
        """
        template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        if template is None:
            raise FileNotFoundError(f"无法加载模板: {template_path}")

        # 去除透明通道
        if template.shape[2] == 4:
            alpha = template[:, :, 3]
            self.template_mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)[1]
            template = template[:, :, :3]
        else:
            # 自动生成掩模（排除亮度过低或过高的背景）
            gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            mask = cv2.inRange(gray, np.array([10], dtype=np.uint8), np.array([245], dtype=np.uint8))
            self.template_mask = mask

        self.template = template.copy()
        self.template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        self.template_path = template_path
        # print(f"模板已加载: {template_path}, 尺寸={self.template_gray.shape[::-1]}")

    def get_template_gray(self) -> Optional[np.ndarray]:
        """
        返回模板灰度图。

        Returns:
            Optional[np.ndarray]: 模板灰度图像。如果尚未加载模板，则返回 None。
        """
        return self.template_gray

    def get_template_info(self) -> Optional[Dict[str, Any]]:
        """
        返回当前模板信息（路径与尺寸）。

        Returns:
            Optional[Dict[str, Any]]: 包含模板路径、宽度和高度的字典。
            如果未设置模板则返回 None。
        """
        if self.template_gray is None:
            return None
        h, w = self.template_gray.shape[:2]
        return {"path": self.template_path, "width": w, "height": h}

    def match_scaled(self, screenshot: np.ndarray, threshold: float = 0.6) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        执行缩放模板匹配。

        根据当前窗口尺寸对模板进行缩放后执行匹配。

        Args:
            screenshot (np.ndarray): 当前截图图像。
            threshold (float, optional): 匹配阈值，默认 0.6。

        Returns:
            Tuple[Optional[Tuple[int, int]], float]: 
                匹配结果 (center, match_val)，其中：
                    - center (Tuple[int, int]): 匹配到的目标中心坐标；
                    - match_val (float): 匹配相似度（0~1）。
                如果未匹配到，center 为 None。
        """
        if self.template_gray is None:
            raise RuntimeError("未设置模板，请先调用 set_template() 或 set_template_from_image()")

        # 计算缩放比例
        h1, w1 = screenshot.shape[:2]
        scale_x = w1 / self.base_w
        scale_y = h1 / self.base_h
        scale = (scale_x + scale_y) / 2

        # 缩放模板与掩模
        resized_template = cv2.resize(self.template_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        if hasattr(self, "template_mask") and self.template_mask is not None:
            resized_mask = cv2.resize(self.template_mask, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        else:
            resized_mask = None

        th, tw = resized_template.shape[:2]
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screenshot_gray, resized_template, self.method, mask=resized_mask)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # 匹配结果处理
        if self.method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            match_val = 1 - min_val
            match_loc = min_loc
        else:
            match_val = max_val
            match_loc = max_loc

        # 判断阈值
        if match_val >= threshold:
            center = (match_loc[0] + tw // 2, match_loc[1] + th // 2)
            self.last_match = (center, match_val, (tw, th))
            return center, match_val
        else:
            self.last_match = None
            return None, match_val
        
    def pyramid_template_match(self, screenshot: np.ndarray, threshold: float = 0.6) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        使用图像金字塔多尺度模板匹配，返回最佳匹配结果的中心点坐标和匹配分数。
        """
        if self.template_gray is None:
            raise RuntimeError("未设置模板，请先调用 set_template() 或 set_template_from_image()")

        h, w = self.template_gray.shape[:2]
        best_val = -1
        best_loc = None
        best_scale = 1.0
        best_tw, best_th = w, h

        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        # 计算缩放比例
        h1, w1 = screenshot.shape[:2]
        scale_x = w1 / self.base_w
        scale_y = h1 / self.base_h
        scale = (scale_x + scale_y) / 2

        for scale in [scale]:
            # 缩放模板
            resized_template = cv2.resize(self.template_gray, (int(w * scale), int(h * scale)))
            th, tw = resized_template.shape[:2]
            if screenshot_gray.shape[0] < th or screenshot_gray.shape[1] < tw:
                continue

            res = cv2.matchTemplate(screenshot_gray, resized_template, self.method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            if self.method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                match_val = -min_val
                match_loc = min_loc
            else:
                match_val = max_val
                match_loc = max_loc

            if match_val > best_val:
                best_val = match_val
                best_loc = match_loc
                best_scale = scale
                best_tw, best_th = tw, th

        # 判断阈值
        if best_val >= threshold and best_loc is not None:
            center = (best_loc[0] + best_tw // 2, best_loc[1] + best_th // 2)
            self.last_match = (center, best_val, (best_tw, best_th))
            return center, best_val
        else:
            self.last_match = None
            return None, best_val

    def visualize_match(self, screenshot: np.ndarray):
        """
        可视化匹配结果。

        在截图上绘制匹配区域的矩形框和相似度分数。

        Args:
            screenshot (np.ndarray): 截图图像。
        """
        if not self.last_match:
            print("尚未找到匹配结果，请先调用匹配方法。")
            return

        center, score, (tw, th) = self.last_match
        top_left = (center[0] - tw // 2, center[1] - th // 2)
        bottom_right = (center[0] + tw // 2, center[1] + th // 2)

        img_show = screenshot.copy()
        cv2.rectangle(img_show, top_left, bottom_right, (0, 255, 0), 2)
        cv2.putText(img_show, f"{score:.2f}", (top_left[0], top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.imshow("Template Match", img_show)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
