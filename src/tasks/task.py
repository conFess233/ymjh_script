from abc import ABC, abstractmethod

class Task(ABC):
    """
    任务抽象基类，定义了游戏中任务的基本结构。

    所有具体任务类都必须继承此类并实现抽象方法。该类确保了所有任务
    都具有统一的接口，包括启动、停止功能以及任务名称标识。

    Attributes:
        TASK_NAME: 任务名称常量，子类必须重写此属性
    """
    TASK_NAME = None  # 任务名, 子类需要重写此常量

    def __init__(self):
        """
        初始化任务实例。

        Raises:
            ValueError: 当子类未定义task_name常量时抛出异常
        """
        if self.__class__.TASK_NAME is None:
            raise ValueError(f"子类 {self.__class__.__name__} 必须定义 task_name 常量")
        self._running = False

    def configure_window_access(self, wincap, clicker):
        """
        由 TaskModel 调用，注入已连接的窗口捕获和点击对象。
        子类应该重写此方法来接收和配置自身所需组件。
        """
        pass 

    @abstractmethod
    def start(self):
        """
        启动任务的抽象方法。

        子类必须实现此方法以定义任务启动时的具体行为。
        实现时应将任务状态设置为运行中。
        """
        pass

    @abstractmethod
    def stop(self):
        """
        停止任务的抽象方法。

        子类必须实现此方法以定义任务停止时的具体行为。
        实现时应将任务状态设置为已停止。
        """
        pass

    @property
    def running(self):
        """
        获取任务运行状态。

        Returns:
            bool: 任务是否正在运行
        """
        return self._running

    def __str__(self):
        """
        返回任务的字符串表示。

        Returns:
            str: 包含任务名称和运行状态的字符串
        """
        return f"Task(name={self.TASK_NAME}, running={self._running})"

    def __repr__(self):
        """
        返回任务的详细表示。

        Returns:
            str: 包含类名、任务名称和运行状态的详细字符串
        """
        return f"{self.__class__.__name__}(name='{self.TASK_NAME}', running={self._running})"

