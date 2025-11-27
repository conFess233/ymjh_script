import os
import json

from PySide6.QtCore import QObject, Signal
from ..core.logger import logger

class TaskCfgModel(QObject):
    task_cfg_updated = Signal(dict) # 任务配置更新信号，参数为新的任务配置字典
        
    def __init__(self, file_path="task_config.json"):
        super().__init__()
        self.file_path = os.path.abspath(file_path)
        self.task_cfg = {
            "window_title": "一梦江湖", # 目标窗口标题
            "timeout": 600, # 任务超时时间（秒）
            "loop_count": 1, # 循环次数
            "base_window_size": (2560, 1330),       # 基准窗口大小，用于尺寸比例换算
            "match_threshold": 0.6,        # 默认模板匹配阈值
            "click_delay": 3,                # 点击后的默认等待时间（秒）
            "capture_retry_delay": 2, # 捕获失败重试延迟（秒）
            "template_retry_delay": 0.5, # 模板匹配失败重试延迟（秒）
            "max_retry_attempts": 5, # 最大重试次数
        }

        self.load_task_cfg()

    
    def load_task_cfg(self):
        """
        从文件加载任务配置.
        """
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.task_cfg.update(data)
                self.task_cfg_updated.emit(self.task_cfg)
                logger.info(f"加载任务配置成功.")
        except FileNotFoundError:
            # 文件不存在则保存默认设置
            self.save_task_cfg()
        except Exception as e:
            logger.error(f"加载任务配置失败: {e}")
    
    def save_task_cfg(self):
        """
        将任务配置保存到文件.
        """
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.task_cfg, f, indent=4, ensure_ascii=False)
                logger.info(f"任务配置保存成功.")
        except Exception as e:
            logger.error(f"保存任务配置失败: {e}")
    
    def update_task_cfg(self, new_cfg: dict):
        """
        更新任务配置.

        Args:
            new_cfg (dict): 包含新任务配置的字典.
        """
        self.task_cfg.update(new_cfg)
        self.save_task_cfg()
        logger.info(f"任务配置更新成功.")
        self.task_cfg_updated.emit(self.task_cfg)
    
    def get_task_cfg(self) -> dict:
        """
        获取当前任务配置.

        Returns:
            dict: 当前任务配置字典.
        """
        return self.task_cfg
    
    def get_task_cfg_item(self, key: str):
        """
        获取任务配置项.

        Args:
            key (str): 配置项键名.

        Returns:
            Any: 对应配置项的值.
        """
        return self.task_cfg.get(key, None)

task_cfg_model = TaskCfgModel()
