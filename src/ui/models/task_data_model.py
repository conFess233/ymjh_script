from PySide6.QtCore import QObject, Signal
from ...tasks.ri_chang_fu_ben import RiChangFuBen
from ...tasks.lun_jian import LunJian
from .task_cfg_model import task_cfg_model
from ..core.logger import logger

class TaskDataModel(QObject):
    """
    任务数据模型：仅负责管理任务列表数据和配置。
    """
    run_list_changed = Signal()  # 列表增删改时发送

    # 任务名称到类的映射
    TASK_MAP = {
        "日常副本": RiChangFuBen,
        "论剑": LunJian
    }

    def __init__(self, log_mode: int = 0):
        super().__init__()
        self.log_mode = log_mode
        self._tasks = []  # 存储任务实例
        # 连接全局配置更新信号
        task_cfg_model.task_cfg_updated.connect(self.update_all_tasks_config)

    def get_tasks(self) -> list:
        """
        获取当前任务实例列表
        """
        return self._tasks

    def get_task_names(self) -> list[str]:
        """
        获取当前任务名称列表（用于 UI 显示或序列化）
        """
        return [task.get_task_name() for task in self._tasks]

    def add_task(self, task_name: str, multi: bool = False):
        """
        添加单个任务
        """
        task_class = self.TASK_MAP.get(task_name)
        if task_class:
            try:
                # 创建任务实例，传入当前全局配置
                task = task_class(config=task_cfg_model.task_cfg)
                self._tasks.append(task)
                logger.info(f"添加任务: {task_name}", mode=1)
                if not multi:
                    self.run_list_changed.emit()
            except Exception as e:
                logger.error(f"创建任务实例失败 {task_name}: {e}")

    def add_tasks_by_names(self, task_names: list[str]):
        """
        批量添加任务
        """
        self._tasks.clear()
        for name in task_names:
            self.add_task(name, multi=True)
        # 批量添加只发送一次信号
        self.run_list_changed.emit()

    def remove_task(self, index: int):
        """
        移除指定索引的任务
        """
        if 0 <= index < len(self._tasks):
            task = self._tasks.pop(index)
            logger.info(f"移除任务: {task.get_task_name()}", mode=1)
            self.run_list_changed.emit()

    def move_task(self, from_index: int, to_index: int):
        """
        移动任务位置
        """
        if 0 <= from_index < len(self._tasks) and 0 <= to_index < len(self._tasks):
            if from_index == to_index:
                return
            task = self._tasks.pop(from_index)
            self._tasks.insert(to_index, task)
            self.run_list_changed.emit()

    def clear_tasks(self):
        """
        清空所有任务
        """
        self._tasks.clear()
        self.run_list_changed.emit()

    def update_all_tasks_config(self):
        """
        当 task_cfg_model 更新时，同步更新所有现有任务实例的配置
        """
        cfg = task_cfg_model.task_cfg
        for task in self._tasks:
            try:
                task.update_config(cfg)
            except Exception as e:
                logger.error(f"更新任务配置失败: {e}", mode=self.log_mode)