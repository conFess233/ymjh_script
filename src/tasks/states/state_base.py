from abc import ABC, abstractmethod
from ...ui.core.logger import logger
import time

class State(ABC):
    """
    状态基类，定义状态的标准接口。
    """
    def __init__(self, task):
        # 持有 Task 实例 (Context)，以便调用截图、点击等方法
        self.task = task 

    def on_enter(self):
        """
        进入该状态时触发
        """
        # 使用 mode=1 避免日志刷屏，只在文件记录或调试时显示
        logger.info(f"切换状态 -> {self.__class__.__name__}", mode=1)

    def on_exit(self):
        """
        退出该状态时触发
        """
        pass

    @abstractmethod
    def execute(self):
        """
        核心逻辑循环。
        
        Returns:
            State: 如果需要切换状态，返回下一个状态的实例。
            None:  如果保持当前状态，返回 None。
        """
        pass

    def sleep(self, seconds, is_random=True):
        """
        封装任务的随机等待
        """
        # 假设你在 TemplateMatchingTask 中实现了 sleep_random
        if hasattr(self.task, '_pause_aware_sleep'):
            self.task._pause_aware_sleep(seconds, is_random)
        else:
            logger.warning(f"任务未实现 _pause_aware_sleep 方法，使用 time.sleep({seconds}) 等待")
            time.sleep(seconds)