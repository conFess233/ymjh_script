from .template_maching_task import TemplateMatchingTask
from ..ui.core.logger import logger
import template_img
import random

class LunJian(TemplateMatchingTask):
    """
    论剑任务类.

    自动执行论剑相关操作，进入论剑场景后立刻退出。
    """
    
    TASK_NAME = "论剑"  # 论剑任务

    # 模板图片路径列表
    TEMPLATE_PATH_LIST = {
        "huo_dong": template_img.TEMPLAET["huo_dong"],
        "fen_zheng": template_img.TEMPLAET["fen_zheng"],
        "1_v_1": template_img.TEMPLAET["1_v_1"],
        "tui_chu_lun_jian": template_img.TEMPLAET["tui_chu_lun_jian"],
        "que_ding": template_img.TEMPLAET["que_ding"],
    }

    def __init__(self, config: dict, log_mode: int = 0):
        """
        初始化论剑任务.
        """
        # 调用父类初始化
        super().__init__(config, log_mode)

    def get_template_path_list(self) -> list:
        """
        获取模板路径列表.

        Returns:
            list: 模板图片路径列表
        """
        return [template["path"] for template in self.TEMPLATE_PATH_LIST.values()]

    def get_task_name(self) -> str:
        """
        获取任务名称.

        Returns:
            str: 任务名称
        """
        return self.TASK_NAME

    def execute_task_logic(self):
        """
        执行具体的任务逻辑.
        """
        
        # 验证模板文件
        if not self.validate_templates():
            logger.error(f"[{self.get_task_name()}]模板文件验证失败，任务无法启动", mode=self.log_mode)
            return
        
        self._pause_aware_sleep(2) # 任务开始前暂停两秒，防止ui无反应
        
        try:
            while self.running:
                
                # 每次循环开始时检查是否超时
                if self.check_timeout():
                    logger.warning(f"[{self.get_task_name()}]任务超时，已退出.", mode=self.log_mode)
                    return # 超时，退出任务逻辑
                
                matched = False
                
                # 遍历所有模板
                for key in self.TEMPLATE_PATH_LIST.keys():
                    template = self.TEMPLATE_PATH_LIST[key]
                    
                    # 每次迭代前再次检查是否超时或被外部停止
                    if self.check_timeout() or not self.running:
                        return # 超时或被停止，退出任务逻辑
                    
                    # 跳过已点击的模板
                    if template["path"] in self.clicked_templates:
                        continue
                    
                    # 捕获截图并匹配模板
                    match_result = self.capture_and_match_template(template, None)
                    if match_result is None:
                        # 如果捕获失败，等待重试时检查停止/超时
                        if self._pause_aware_sleep(self.template_retry_delay):
                            return 
                        continue
                    
                    center, match_val, size = match_result
                    if center:
                        # 点击匹配到的模板
                        if self.click_template(template["path"], center, size):
                            matched = True
                            logger.info(f"[{self.get_task_name()}]模板 {template["path"]} 已处理完成, 相似度{match_val:.3f}", mode=self.log_mode)
                            
                            # 特殊处理
                            # 如果点击确认，记录点击并退出循环
                            if key == "que_ding" and "template_img/tui_chu_lun_jian.png" in self.clicked_templates:
                                logger.info(f"[{self.get_task_name()}]已执行退出副本操作，结束任务。", mode=self.log_mode)
                                self.stop() # 停止任务，退出 while 循环
                                return 
                            
                            click_delay = random.uniform(max(self.click_delay - self.rand_delay, self.click_delay * 0.7), self.click_delay + self.rand_delay)
                            self._pause_aware_sleep(click_delay)
                            break  # 找到一个匹配后跳出 for 循环
                    else:
                        # 模板匹配失败，等待重试时检查停止/超时
                        if self._pause_aware_sleep(self.template_retry_delay):
                            return


                # 如果没有匹配到任何模板，检查是否已完成所有任务
                if not matched:
                    if self.is_task_completed():
                        logger.info(f"[{self.get_task_name()}]所有模板已处理完成，任务结束", mode=self.log_mode)
                        break # 完成所有模板，退出 while 循环
                
                # 等待下次循环
                # 每次等待时检查是否停止或超时
                # 计算随机延迟
                loop_delay = random.uniform(max(self.click_delay - self.rand_delay, self.click_delay), self.click_delay + self.rand_delay)
                if self._pause_aware_sleep(loop_delay):
                    return # 被停止，退出任务逻辑
                
            logger.info(f"[{self.get_task_name()}]任务逻辑自然退出。", mode=self.log_mode)

        except KeyboardInterrupt:
            logger.info(f"[{self.get_task_name()}]任务被手动停止。", mode=self.log_mode)
        return # 任务逻辑结束

    def __str__(self):
        """
        返回任务的字符串表示.
        """
        completed, total, percentage = self.get_progress()
        return f"LunJian(name={self.get_task_name()}(论剑), running={self._running}, progress={completed}/{total}({percentage:.1f}%))"
    