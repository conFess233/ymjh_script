from rapidocr_onnxruntime import RapidOCR
import os
import cv2
import numpy as np
from typing import Any, Dict, Optional, Tuple, List, Union
from PIL import Image, ImageDraw, ImageFont

class OCRMatcher:
    """
    OCR 匹配类。

    基于 RapidOCR 在图片或指定区域中寻找包含特定关键词的文本位置。
    模仿 TemplateMatcher 增加了分辨率自适应和区域裁剪功能。
    """

    def __init__(self, thread_num: int = 2, det_model_path: Optional[str] = None):
        """
        初始化 OCR 匹配器。

        Args:
            thread_num (int): OMP 和 ONNX 的线程数。
            det_model_path (str, optional): 自定义检测模型路径。
        """
        self.ocr = RapidOCR(det_model_path=det_model_path)
        os.environ["OMP_NUM_THREADS"] = str(thread_num)
        os.environ["ONNX_NUM_THREADS"] = str(thread_num)
        self.last_results = [] # 上次匹配的所有结果

    def match_text(self, screenshot: np.ndarray, keywords: Union[str, List[str]], threshold: float = 0.6, 
                   rect: Optional[Tuple[int, int, int, int]] = None, 
                   base_size: Optional[tuple] = None, padding: int = 5, gray: bool = True, binary: bool = False, clahe: bool = True) -> Optional[List[Tuple[Tuple[int, int], float, Tuple[int, int], str]]]:
        """
        执行文本匹配。

        在截图（或截图的特定区域）中查找包含关键词的文本块。

        Args:
            screenshot (np.ndarray): 当前截图图像。
            keywords (str | List[str]): 需要查找的关键词或关键词列表，为空时返回所有识别结果。
            threshold (float, optional): OCR 置信度阈值，默认 0.6。
            rect (Optional[Tuple[int, int, int, int]], optional): 搜索区域矩形框(x1, y1, x2, y2)，基于基准尺寸。
            base_size (tuple, optional): 基准窗口尺寸，如果不传则使用初始化时的设置。
            padding (int, optional): 搜索区域内边距，默认 5。
            gray (bool, optional): 是否将图像转换为灰度图，默认 True。
            binary (bool, optional): 是否进行二值化处理，默认 False。
            clahe (bool, optional): 是否应用 CLAHE 增强，默认 True。

        Returns:
            List[Tuple]: 匹配结果列表，每一项包含：
                (center, score, (tw, th), text)
                - center (Tuple[int, int]): 文本中心坐标 (x, y)。
                - score (float): 置信度。
                - (tw, th) (Tuple[int, int]): 文本框尺寸 (宽, 高)。
                - text (str): 识别到的完整文本内容。
        """
        if screenshot is None or screenshot.size == 0:
            return None
        base_w, base_h = base_size # type: ignore
            
        if isinstance(keywords, str):
            keywords = [keywords]

        h1, w1 = screenshot.shape[:2]
        
        # 计算缩放比例 (基于当前截图 vs 基准尺寸)
        scale_x = w1 / base_w
        scale_y = h1 / base_h

        # 处理搜索区域 (ROI)
        search_img = screenshot
        offset_x, offset_y = 0, 0
        
        if rect and all(coord >= 0 for coord in rect):
            x1, y1, x2, y2 = rect
            # 同步缩放 rect 坐标
            x1_s = int(x1 * scale_x) - padding
            y1_s = int(y1 * scale_y) - padding
            x2_s = int(x2 * scale_x) + padding
            y2_s = int(y2 * scale_y) + padding

            # 确保裁剪区域的坐标在截图范围内
            x1_c = max(0, x1_s)
            y1_c = max(0, y1_s)
            x2_c = min(w1, x2_s)
            y2_c = min(h1, y2_s)

            if x1_c < x2_c and y1_c < y2_c:
                search_img = screenshot[y1_c:y2_c, x1_c:x2_c]
                offset_x, offset_y = x1_c, y1_c
            else:
                print(f"警告: OCR裁剪区域无效. Rect: {rect}, 缩放后: ({x1_c}, {y1_c}, {x2_c}, {y2_c})")
                self.last_results = []
                return []

        if search_img.size == 0:
            return []
        
        # 处理灰度化、二值化、CLAHE 增强
        if gray:
            search_img = cv2.cvtColor(search_img, cv2.COLOR_BGR2GRAY)
        if binary:
            _, search_img = cv2.threshold(search_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if clahe:
            search_img = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(search_img)
            

        # 执行 OCR 推理
        result, _ = self.ocr(search_img)
        
        matches = []
        if not result:
            self.last_results = []
            return matches

        # 遍历结果并筛选
        for box, text, score in result:
            score = float(score)
            if score < threshold:
                continue
            
            # 检查是否包含任一关键词
            if keywords and any(k in text for k in keywords):
                # box 是四个点坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                # 转换为中心点和宽高
                box = np.array(box)
                min_x = np.min(box[:, 0])
                max_x = np.max(box[:, 0])
                min_y = np.min(box[:, 1])
                max_y = np.max(box[:, 1])
                
                tw = int(max_x - min_x)
                th = int(max_y - min_y)
                
                # 计算局部中心点
                cx_local = int(min_x + tw // 2)
                cy_local = int(min_y + th // 2)
                
                # 映射回全图坐标
                center = (cx_local + offset_x, cy_local + offset_y)
                
                matches.append((center, score, (tw, th), text))

        self.last_results = matches
        return matches

    def visualize_match(self, screenshot: np.ndarray, results: list = None): # type: ignore
        """
        可视化 OCR 匹配结果。

        Args:
            screenshot (np.ndarray): 输入的截图图像 (BGR 格式)。
            results (list, optional): OCR 匹配结果列表。如果不传则使用最近一次结果。
        """
        if results is None:
            results = self.last_results

        if not results:
            print("没有可显示的结果。")
            return

        img_show = screenshot.copy()
        
        for center, score, (tw, th), text in results:
            top_left = (center[0] - tw // 2, center[1] - th // 2)
            bottom_right = (center[0] + tw // 2, center[1] + th // 2)

            # 绘制矩形框
            cv2.rectangle(img_show, top_left, bottom_right, (255, 0, 0), 2)
            
            # 准备显示文本
            display_text = f"{text} ({score:.2f})"
            text_pos = (top_left[0], top_left[1] - 25) #稍微往上提一点，留出字号空间

            # 使用 Pillow 绘制中文
            img_show = self._put_chinese_text(img_show, display_text, text_pos, text_color=(255, 0, 0), text_size=20)
            
            # 绘制中心点
            cv2.circle(img_show, center, 3, (0, 255, 0), -1)

        cv2.imshow("OCR Match", img_show)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def _put_chinese_text(self, img_cv, text, position, text_color=(0, 255, 0), text_size=20):
        """
        在 OpenCV 图片上绘制中文 (BGR -> RGB -> PIL -> RGB -> BGR)
        """
        # OpenCV 图片 (BGR) 转换为 PIL 图片 (RGB)
        img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        # 加载字体 (尝试加载常用中文字体，防止报错)
        font = None
        try:
            # Windows 常见字体: 微软雅黑 (msyh.ttc) 或 黑体 (simhei.ttf)
            font = ImageFont.truetype("msyh.ttc", text_size) 
        except IOError:
            try:
                font = ImageFont.truetype("simhei.ttf", text_size)
            except IOError:
                # 实在找不到字体，使用默认 (可能无法显示中文，但不会崩)
                print("警告: 未找到中文字体，中文可能无法显示。")
                font = ImageFont.load_default()

        # 绘制文字
        draw.text(position, text, font=font, fill=text_color)

        # PIL 图片转换回 OpenCV 图片 (RGB -> BGR)
        img_cv_new = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        return img_cv_new