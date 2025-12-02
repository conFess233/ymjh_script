from .task import Task
from ..modules.auto_clicker import AutoClicker
from ..modules.window_capture import WindowCapture
from ..modules.template_matcher import TemplateMatcher
from abc import abstractmethod
from typing import Optional, Tuple
import os
import numpy as np
import threading
import time
from ..ui.core.logger import logger

class TemplateMatchingTask(Task):
    """
    基于模板匹配的任务的抽象父类.

    提供基础任务流程，截图，点击等操作。
    子类只需定义具体的模板路径和匹配逻辑。
    """
    # 任务名，子类需重写此常量
    TASK_NAME = None

    def __init__(self, config: dict):
        """
        初始化模板匹配任务。

        该构造函数用于初始化窗口截图、模板匹配与自动点击的相关组件，
        并设置默认的匹配参数、延迟时间以及重试机制。

        Args:
            base_window_size (tuple): 基准窗口大小，用于缩放匹配区域。默认值为 (2560, 1330)，根据实际截取模板时的客户端窗口大小调整(经测试, 在2K屏幕下, 设置为2560, 1330效果较好)。
            match_threshold (float): 默认匹配阈值（0~1 之间），匹配得分高于该值时视为匹配成功。
            click_delay (float): 每次点击后的等待时间（秒）。
            capture_retry_delay (float): 捕获失败后的重试延迟时间（秒）。
            template_retry_delay (float): 模板匹配失败后的重试延迟时间（秒）。
            match_loop_delay (float): 模板匹配循环延迟（秒）。
        """
        # 初始化参数设置
        self.base_window_size = config["base_window_size"]                  # 基准窗口大小，用于尺寸比例换算
        self.match_threshold = config["match_threshold"]                    # 默认模板匹配阈值
        self.click_delay = config["click_delay"]                            # 点击后的默认等待时间（秒）
        self.capture_retry_delay = config["capture_retry_delay"]            # 捕获失败重试延迟（秒）
        self.template_retry_delay = config["template_retry_delay"]          # 模板匹配失败重试延迟（秒）
        self.match_loop_delay = config["match_loop_delay"]                # 模板匹配循环延迟（秒）

        self.task_timeout = None                                            # 任务允许的最大运行时间（秒）
        self.start_time = None                                              # 任务开始运行的时间戳
        self.template_matcher = TemplateMatcher("", self.base_window_size)  # 模板匹配器实例

        # 状态变量
        self._running = False                                               # 当前任务运行状态标志
        self.clicked_templates = set()                                      # 已点击过的模板集合，用于防止重复点击

        self._stop_event = threading.Event()                                # 用于停止任务的事件对象


    # --- 初始化/更新配置方法 ---
    def configure_window_access(self, wincap: WindowCapture, clicker: AutoClicker):
        """
        接收并配置已连接的窗口访问对象。
        """
        self.window_capture = wincap
        self.auto_clicker = clicker

    def update_config(self, new_cfg: dict):
        """
        更新任务配置.

        Args:
            new_cfg (dict): 包含新任务配置的字典，键值对与任务参数对应。
        """
        self.base_window_size = new_cfg["base_window_size"]
        self.match_threshold = new_cfg["match_threshold"]
        self.click_delay = new_cfg["click_delay"]
        self.capture_retry_delay = new_cfg["capture_retry_delay"]
        self.template_retry_delay = new_cfg["template_retry_delay"]
        self.match_loop_delay = new_cfg["match_loop_delay"]
        self.template_matcher.set_base_window_size(self.base_window_size)

    def validate_templates(self) -> bool:
        """
        验证模板文件是否存在。

        遍历模板路径列表，检查模板文件是否存在。

        Returns:
            bool: 若所有模板文件均存在则返回 True，否则返回 False。
        """
        template_list = self.get_template_path_list()
        missing_templates = []
        for template_path in template_list:
            if not os.path.exists(template_path):
                missing_templates.append(template_path)
        
        if missing_templates:
            logger.error(f"错误：以下模板文件不存在: {missing_templates}")
            return False
        return True

    # --- 截图/模板匹配/点击方法 ---
    def capture_screenshot(self) -> Optional[np.ndarray]:
        """
        捕获窗口截图。

        调用窗口捕获对象的接口来获取当前截图。

        Returns:
            Optional[np.ndarray]: 窗口截图图像（numpy.ndarray）。
                若捕获失败，返回 None。
        """
        screenshot = self.window_capture.capture()
        if screenshot is None:
            logger.error("无法捕获窗口图像，稍后重试...")
            self._sleep(self.capture_retry_delay)
            return None
        return screenshot

    def match_template(self, screenshot: np.ndarray, template_path: str, 
                    screenshot_size: Optional[Tuple[int, ...]] = None) -> Optional[Tuple[Tuple[int, int], float]]:
        """
        使用模板匹配方法匹配指定模板。

        调用内部模板匹配器，根据输入截图与模板路径进行匹配，
        并返回匹配中心坐标及相似度。若匹配失败，返回 None。

        Args:
            screenshot (np.ndarray): 当前窗口或屏幕截图的图像数组。
            template_path (str): 模板图片文件路径。
            screenshot_size (Optional[Tuple[int, ...]]): 截图尺寸 (width, height)。
                若为 None，则自动从 screenshot 获取。

        Returns:
            Optional[Tuple[Tuple[int, int], float]]: 
                匹配结果 (center, match_val)，其中：
                    - center (Tuple[int, int]): 匹配到的中心坐标。
                    - match_val (float): 匹配相似度（0~1）。
                若未匹配到模板，返回 None。
        """
        if screenshot_size is None:
            screenshot_size = self.get_screenshot_size(screenshot)
        
        # 设置模板并进行匹配
        self.template_matcher.set_template(template_path)
        if not "tiao_guo_ju_qing.png" in template_path:
            match_result = self.template_matcher.match_scaled(
                screenshot, 
                threshold=self.match_threshold
            )
        else:
            match_result = self.template_matcher.pyramid_template_match(screenshot)

        center, match_val = match_result
        if center is None:
            return None
        return (center, match_val)
    
    def capture_and_match_template(self, template_path: str, 
                                screenshot_size: Optional[Tuple[int, ...]] = None) -> Optional[Tuple[Tuple[int, int], float]]:
        """
        捕获截图并匹配指定模板。

        先捕获当前窗口图像，再执行模板匹配。
        若匹配成功，可由子类对坐标进行进一步处理。

        Args:
            template_path (str): 模板图片路径。
            screenshot_size (Optional[Tuple[int, ...]]): 截图尺寸 (width, height)。
                若为 None，则自动获取。

        Returns:
            Optional[Tuple[Tuple[int, int], float]]: 
                匹配结果 (中心坐标, 相似度)。未匹配到返回 None。
        """
        # 捕获当前窗口图像
        screenshot = self.capture_screenshot()
        if screenshot is None:
            return None
        
        # 获取截图尺寸
        if screenshot_size is None:
            screenshot_size = self.get_screenshot_size(screenshot)
        
        # 模板匹配
        match_result = self.match_template(screenshot, template_path, screenshot_size)
        
        # 特殊处理：子类可以重写此方法来调整模板坐标
        if match_result is not None:
            screenshot_w, screenshot_h = screenshot_size
            match_result = self.process_special_templates_point(template_path, match_result, screenshot_w, screenshot_h)
            if match_result and match_result[0] is not None:
                return match_result
        
        return None

    def process_special_templates_point(self, template_path: str, match_result: Optional[tuple], 
                                screenshot_w: int, screenshot_h: int) -> Optional[tuple]:
        """
        处理特殊模板。

        子类可重写此方法，实现针对特定模板的匹配坐标调整逻辑。

        Args:
            template_path (str): 模板路径。
            screenshot_w (int): 截图宽度。
            screenshot_h (int): 截图高度。

        Returns:
            Optional[tuple]: 处理后的匹配结果。
        """
        # 默认实现：不修改任何坐标
        return match_result
    
    def match_multiple_templates(self, template_path_list: list, target_template: str, match_val_threshold: float = 0.6) -> Optional[Tuple[Tuple[int, int], float]]:
        """
        匹配多个模板图片, 若所有图片都匹配成功, 则返回指定图片的坐标以及相似度

        Args:
            template_path_list: 模板图片路径列表
            match_val_threshold: 匹配相似度阈值

        Returns:
            Optional[Tuple[Tuple[int, int], float]]: 
                匹配结果 (中心坐标, 相似度)。未匹配到返回 None。
        """
        screenshot = self.capture_screenshot()
        if screenshot is None:
            return None
        
        target_match_result = None
        for template_path in template_path_list:
            match_result = self.match_template(screenshot, template_path)
            if match_result is None or match_result[1] < match_val_threshold:
                return None
            if target_template in template_path:
                target_match_result = match_result
                
        return target_match_result

    def click_template(self, template_path: str, center: tuple) -> bool:
        """
        点击匹配到的模板。

        Args:
            template_path (str): 模板路径。
            center (tuple): 匹配到的中心坐标 (x, y)。

        Returns:
            bool: 点击成功返回 True，否则返回 False。
        """
        x, y = center
        print(f"找到模板 {template_path}, 点击位置: ({x}, {y})")
        
        if self.auto_clicker.click(x, y):
            if not "tiao_guo_ju_qing.png" in template_path:
                self.clicked_templates.add(template_path)
            total_templates = len(self.get_template_path_list())
            print(f"已点击的模板数量: {len(self.clicked_templates)}/{total_templates}")
            return True
        else:
            print(f"点击模板 {template_path} 失败")
            return False


    # --- 辅助方法 ---
    def _sleep(self, delay: float) -> bool:
            """
            使用 Event.wait 代替 time.sleep 实现非阻塞延迟。
            
            Args:
                delay: 延迟时间。
                
            Returns:
                bool: 如果在延迟时间内 stop 事件被设置（任务被要求停止），返回 True。
            """
            # wait 方法会在 event 被 set 时立即返回 True
            return self._stop_event.wait(delay)
    
    def reset_clicked_templates(self):
        """
        重置已点击的模板记录。"""
        self.clicked_templates.clear()
        print("已重置点击记录")

    # --- 任务控制方法 ---
    def start(self):
        """
        启动任务。

        若任务未运行，则置为运行状态并清空点击记录。
        """
        if not self._running:
            self._running = True
            self.clicked_templates.clear()  # 启动时清空点击记录
            print(f"任务 {self.get_task_name()} 已启动")
        else:
            print(f"任务 {self.get_task_name()} 已经在运行")

    def stop(self):
        """
        停止任务。

        若任务正在运行，则设置为停止状态。
        """
        if self._running:
            self._running = False
            print(f"任务 {self.get_task_name()} 已停止")
        else:
            print(f"任务 {self.get_task_name()} 未在运行")

    @abstractmethod
    def execute_task_logic(self):
        """
        执行具体的任务逻辑。

        子类必须实现此方法来定义任务执行流程。
        """
        pass

    def check_timeout(self) -> bool:
        """
        检查任务是否已超时。

        Returns:
            bool: 如果超时或未设置 timeout，返回 True；否则返回 False。
        """
        if self.task_timeout is None or self.start_time is None:
            return False # 如果没有设置超时，则不中断
            
        if (time.time() - self.start_time) > self.task_timeout:
            logger.warning(f"任务 {self.get_task_name()} 已超时 ({self.task_timeout} 秒)，正在停止。")
            self.stop()
            return True
        return False

    def run(self):
            """
            任务主入口，在执行具体逻辑前记录开始时间。
            """
            self.start() # 调用 start() 设置 _running = True
            self.start_time = time.time() # 记录任务开始时间
            try:
                self.execute_task_logic()
            except Exception as e:
                logger.error(f"任务 {self.get_task_name()} 执行逻辑出错: {e}")
            finally:
                self.stop() # 确保任务结束时调用 stop()


    # --- getters/setters ---

    @property
    def running(self) -> bool:
        """
        获取任务运行状态。
        该属性只读，外部无法直接修改任务运行状态。

        Returns:
            bool: 当前任务是否正在运行。
        """
        return self._running
    @abstractmethod

    def get_template_path_list(self) -> list:
        """
        获取模板路径列表。
        子类需实现此方法，返回模板图片路径的列表。

        Returns:
            list: 模板图片路径的列表。
        """
        pass

    @abstractmethod
    def get_task_name(self) -> str:
        """
        获取任务名称。
        子类需实现此方法，返回任务的名称。

        Returns:
            str: 任务名称。
        """
        pass
    def get_base_window_size(self) -> tuple:
        """
        获取基准窗口尺寸。

        Returns:
            tuple: 基准窗口尺寸 (宽度, 高度)。
        """
        return self.base_window_size

    def set_timeout(self, timeout: float):
        """
        设置任务允许的最大运行时间。
        """
        self.task_timeout = timeout

    def set_default_base_window_size(self, base_window_size: tuple):
        """
        设置默认基准窗口大小。

        Args:
            base_window_size (tuple): 新的基准窗口大小 (宽度, 高度)。
        """
        self.base_window_size = base_window_size

    def set_match_threshold(self, threshold: float):
        """
        设置默认模板匹配阈值。

        Args:
            threshold (float): 新的匹配阈值（0.0 到 1.0 之间）。
        """
        self.match_threshold = threshold

    def set_click_delay(self, delay: float):
        """
        设置默认点击延迟。

        Args:
            delay (float): 新的点击延迟（秒）。
        """
        self.click_delay = delay

    def set_capture_retry_delay(self, delay: float):
        """
        设置默认捕获失败重试延迟。

        Args:
            delay (float): 新的重试延迟（秒）。
        """
        self.capture_retry_delay = delay

    def set_template_retry_delay(self, delay: float):
        """
        设置默认模板匹配失败重试延迟。

        Args:
            delay (float): 新的重试延迟（秒）。
        """
        self.template_retry_delay = delay

    def set_default_max_retry_attempts(self, max_attempts: int):
        """
        设置默认最大模板匹配重试次数。

        Args:
            max_attempts (int): 新的最大重试次数。
        """
        self.max_retry_attempts = max_attempts

    def set_all_config(self, base_window_size: tuple, threshold: float, click_delay: float, capture_delay: float, template_delay: float, max_attempts: int):
        """
        设置所有默认参数。

        Args:
            base_window_size (tuple): 新的基准窗口大小 (宽度, 高度)。
            threshold (float): 新的匹配阈值（0.0 到 1.0 之间）。
            delay (float): 新的点击延迟（秒）。
            capture_delay (float): 新的捕获失败重试延迟（秒）。
            template_delay (float): 新的模板匹配失败重试延迟（秒）。
            max_attempts (int): 新的最大重试次数。
        """
        self.set_default_base_window_size(base_window_size)
        self.set_match_threshold(threshold)
        self.set_click_delay(click_delay)
        self.set_capture_retry_delay(capture_delay)
        self.set_template_retry_delay(template_delay)
        self.set_default_max_retry_attempts(max_attempts)

    def get_progress(self) -> tuple:
        """
        获取任务进度。

        Returns:
            tuple(int, int, float): (已点击数量, 总数量, 完成百分比)。
        """
        total = len(self.get_template_path_list())
        completed = len(self.clicked_templates)
        percentage = (completed / total) * 100 if total > 0 else 0
        return completed, total, percentage
        
    def get_screenshot_size(self, screenshot: np.ndarray) -> Tuple[int, int]:
        """
        获取截图尺寸。

        Args:
            screenshot (np.ndarray): 截图图像。

        Returns:
            Tuple[int, int]: 截图的宽度和高度。
        """
        screenshot_h, screenshot_w = screenshot.shape[:2]
        return (screenshot_w, screenshot_h)
    
    def is_task_completed(self) -> bool:
        """
        检查任务是否完成。

        Returns:
            bool: 若所有模板均已点击则返回 True，否则返回 False。
        """
        total_templates = len(self.get_template_path_list())
        return len(self.clicked_templates) >= total_templates

    def __str__(self) -> str:
        """
        返回任务对象的字符串表示形式。

        Returns:
            str: 包含任务名称、运行状态与进度信息的字符串。
        """
        completed, total, percentage = self.get_progress()
        return f"{self.__class__.__name__}(name={self.get_task_name()}, running={self._running}, progress={completed}/{total}({percentage:.1f}%))"