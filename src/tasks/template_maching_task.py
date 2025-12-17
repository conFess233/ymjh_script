from .task import Task
from ..modules.auto_clicker import AutoClicker
from ..modules.window_capture import WindowCapture
from ..modules.template_matcher import TemplateMatcher
from abc import abstractmethod
from typing import Optional, Tuple, Callable
import os
import numpy as np
import threading
import time
import random
from ..ui.core.logger import logger

class TemplateMatchingTask(Task):
    """
    基于模板匹配的任务的抽象父类.

    提供基础任务流程，截图，点击等操作。
    子类只需定义具体的模板路径和匹配逻辑。
    """
    # 任务名，子类需重写此常量
    TASK_NAME = None

    def __init__(self, config: dict, log_mode: int = 0):
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
        self.match_loop_delay = config["match_loop_delay"]                  # 模板匹配循环延迟（秒）
        self.rand_delay = config["rand_delay"]                              # 随机等待时间，单位秒

        self.task_timeout = None                                            # 任务允许的最大运行时间（秒）
        self.start_time = None                                              # 任务开始运行的时间戳
        self.template_matcher = TemplateMatcher("", self.base_window_size)  # 模板匹配器实例

        self.log_mode = log_mode                                            # 日志模式

        # 状态变量
        self._running = False                                               # 当前任务运行状态标志
        self.clicked_templates = set()                                      # 已点击过的模板集合，用于防止重复点击

        self._stop_event = threading.Event()                                # 用于停止任务的事件对象

        self._pause_condition: Optional[threading.Condition] = None         # 暂停任务的条件变量
        self._is_paused_check: Optional[Callable[[], bool]] = None          # 检查 Model 暂停状态的函数

        self._load_templates()

    # --- 初始化/更新配置方法 ---
    def configure_window_access(self, wincap: WindowCapture, clicker: AutoClicker, pause_condition: threading.Condition, is_paused_check: Callable[[], bool]):
        """
        接收并配置已连接的窗口访问对象。
        """
        self.window_capture = wincap
        self.auto_clicker = clicker

        self._pause_condition = pause_condition
        self._is_paused_check = is_paused_check

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
        self.rand_delay = new_cfg["rand_delay"]
        self.template_matcher.set_base_window_size(self.base_window_size)

    def _load_templates(self):
        """
        预加载所有模板文件。

        遍历模板路径列表，调用模板匹配器加载每个模板文件。
        """

        try:
            template_list = self.get_template_path_list()
            if not template_list:
                logger.error("错误：模板路径列表为空")
                return
            self.template_matcher.load_templates_to_cache(template_list)
        except Exception as e:
            logger.error(f"加载模板文件时出错: {e}")

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
                    screenshot_size: tuple[int, int] | None = None) -> tuple[tuple[int, int], float, tuple[int, int] | None] | None:
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

        center, match_val, size = match_result
        if center is None:
            return None
        return (center, match_val, size)
    
    def capture_and_match_template(self, template_path: str, 
                                screenshot_size: tuple[int, int] | None = None) -> tuple[tuple[int, int], float, tuple[int, int]] | None:
        """
        捕获截图并匹配指定模板。

        先捕获当前窗口图像，再执行模板匹配。
        若匹配成功，可由子类对坐标进行进一步处理。

        Args:
            template_path (str): 模板图片路径。
            screenshot_size (Optional[tuple[int, int]]): 截图尺寸 (width, height)。
                若为 None，则自动获取。

        Returns:
            Optional[Tuple[Tuple[int, int], float, tuple[int, int]]]: 
                匹配结果 (中心坐标, 相似度, 模板尺寸)。未匹配到返回 None。
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
    
    def match_multiple_templates(self, template_path_list: list, target_template: str, match_val_threshold: float = 0.6, direction: str = '', direction_size: int = 60) -> tuple[tuple[int, int], float, tuple[int, int] | None] | None:
        """
        匹配多个模板图片, 若所有图片都匹配成功, 则返回指定图片的坐标以及相似度

        Args:
            template_path_list(list): 模板图片路径列表
            match_val_threshold(str): 匹配相似度阈值
            direction(str): 指定匹配哪个区域的图片（上下左右, u w l r）
            direction_size(int): 指定匹配区域的大小（百分比）

        Returns:
            Optional[Tuple[Tuple[int, int], float, tuple[int, int]]]: 
                匹配结果 (中心坐标, 相似度, 模板尺寸)。未匹配到返回 None。
        """
        screenshot = self.capture_screenshot()
        if screenshot is None:
            return None
        
        screenshot_size = self.get_screenshot_size(screenshot)
        screenshot_w, screenshot_h = screenshot_size
        
        target_match_result = None
        for template_path in template_path_list:
            match_result = self.match_template(screenshot, template_path)
            if match_result is None or match_result[1] < match_val_threshold:
                return None
            else:
                center_x, center_y = match_result[0]
                if direction == 'r' and center_x < screenshot_w * (1 - direction_size / 100):
                    return None
                elif direction == 'l' and center_x > screenshot_w * (direction_size / 100):
                    return None
                elif direction == 'u' and center_y > screenshot_h * (direction_size / 100):
                    return None
                elif direction == 'w' and center_y < screenshot_h * (1 - direction_size / 100):
                    return None
                else:
                    continue
        if target_template in template_path:
            target_match_result = match_result
        else:
            print(f"列表中没有模板 {target_template}")
            return None
        print(f"匹配到模板 {template_path}, 中心坐标: {match_result[0]}, 相似度: {match_result[1]}")
                
        return target_match_result

    def click_template(self, template_path: str, center: tuple[int, int], size: tuple[int, int] | None = None) -> bool:
        """
        点击匹配到的模板。

        Args:
            template_path (str): 模板路径。
            center (tuple): 匹配到的中心坐标 (x, y)。
            size (tuple | None): 模板尺寸 (w, h)。若为 None，则使用默认随机范围。

        Returns:
            bool: 点击成功返回 True，否则返回 False。
        """
        x, y = center
        # 计算动态随机范围
        if size:
            w, h = size
            # 避开边缘 30%，即在中心 40% 区域内点击
            rx = int(w * 0.4)
            ry = int(h * 0.4)
            # 确保至少有 1 像素的波动
            rx = max(1, rx)
            ry = max(1, ry)
            r_range = (rx, ry)
            # print(f"模板尺寸 {w}x{h}, 计算随机点击范围: X±{rx}, Y±{ry}")
        else:
            r_range = 5  # 默认兜底

        if self.auto_clicker.click(x, y, random_range=r_range):
            self.add_clicked_template(template_path)
            # print(f"成功点击模板 {template_path}, 坐标: ({x}, {y})")
            # print(f"已点击的模板: {self.clicked_templates}")
            return True
        else:
            # print(f"点击模板 {template_path} 失败, 坐标: ({x}, {y})")
            return False


    # --- 辅助方法 ---
    def add_clicked_template(self, template_path: str):
        """
        记录已点击的模板路径.
        子类需实现此方法，将模板路径添加到已点击集合中。

        Args:
            template_path (str): 模板路径。
        """
        self.clicked_templates.add(template_path)

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
    
    def _pause_aware_sleep(self, delay: float, is_random: bool = True) -> bool:
        """
        实现非阻塞等待，并在等待前和等待中检查 Model 层的暂停状态。

        Args:
            delay: 延迟时间。
            is_random: 是否使用随机延迟(默认为True)。
    
        Returns:
            bool: 如果任务被要求停止，返回 True。
        """
        # 检查停止标志 (如果任务被stop()，直接退出)
        if not self._running:
            return True

        # 检查并等待暂停状态 (在每次 sleep/retry 前检查)
        if self._is_paused_check and self._pause_condition:
            with self._pause_condition:
                while self._is_paused_check():
                    # 线程在此阻塞，等待 TaskModel.resume_queue() 唤醒
                    self._pause_condition.wait() 
        
        # 检查停止标志 (被唤醒后再次检查)
        if not self._running:
            return True

        # 随机延迟
        if is_random:
            delay = random.uniform(max(delay - self.rand_delay, delay * 0.8), delay + self.rand_delay)
        # 执行非阻塞延迟（在延迟期间仍然可以被 stop() 中断）
        return self._sleep(delay)
    
    def reset_clicked_templates(self):
        """
        重置已点击的模板记录。
        """
        self.clicked_templates.clear()
        print("已重置点击记录")

    # --- 任务控制方法 ---
    def start(self):
        """
        启动任务.
        """
        if not self._running:
            self._running = True
            self._stop_event.clear()  # 确保事件未被设置
            self.clicked_templates.clear()  # 启动时清空点击记录
            logger.info(f"[{self.get_task_name()}]任务已启动", mode=self.log_mode)

    def stop(self):
        """
        停止任务.
        """
        if self._running:
            self._running = False
            self.clicked_templates.clear()  # 停止时清空点击记录
            self._stop_event.set()  # 设置事件，通知任务停止
            logger.info(f"[{self.get_task_name()}]任务已停止", mode=self.log_mode)

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
    def get_task_name(self) -> str | None:
        """
        获取任务名称。
        子类需实现此方法，返回任务的名称。

        Returns:
            (str | None): 任务名称。
        """
        return self.TASK_NAME
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
    
    def set_log_mode(self, log_mode: int):
        """
        设置日志模式。

        Args:
            log_mode (int): 新的日志模式。
        """
        self.log_mode = log_mode

    def __str__(self) -> str:
        """
        返回任务对象的字符串表示形式。

        Returns:
            str: 包含任务名称、运行状态与进度信息的字符串。
        """
        completed, total, percentage = self.get_progress()
        return f"{self.__class__.__name__}(name={self.get_task_name()}, running={self._running}, progress={completed}/{total}({percentage:.1f}%))"