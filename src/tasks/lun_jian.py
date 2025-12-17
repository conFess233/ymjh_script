from .template_maching_task import TemplateMatchingTask
from ..ui.core.logger import logger
import random

class LunJian(TemplateMatchingTask):
    """
    论剑任务类.

    自动执行论剑相关操作，进入论剑场景后立刻退出。
    """
    
    TASK_NAME = "论剑"  # 论剑任务

    # 模板图片路径列表
    TEMPLATE_PATH_LIST = [
        "template_img/huo_dong.png",
        "template_img/fen_zheng.png",
        "template_img/1_v_1.png",
        "template_img/tui_chu_lun_jian.png",
        "template_img/que_ding.png",
    ]

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
        return self.TEMPLATE_PATH_LIST

    def get_base_window_size(self) -> tuple:
        """
        获取基准窗口尺寸.

        Returns:
            tuple: 基准窗口尺寸 (宽度, 高度)
        """
        return self.base_window_size

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
                for template_path in self.get_template_path_list():
                    
                    # 每次迭代前再次检查是否超时或被外部停止
                    if self.check_timeout() or not self.running:
                        return # 超时或被停止，退出任务逻辑
                    
                    # 跳过已点击的模板
                    if template_path in self.clicked_templates:
                        continue
                    
                    # 捕获截图并匹配模板
                    match_result = self.capture_and_match_template(template_path, None)
                    if match_result is None:
                        # 如果捕获失败，等待重试时检查停止/超时
                        if self._pause_aware_sleep(self.template_retry_delay):
                            return 
                        continue
                    
                    center, match_val, size = match_result
                    if center:
                        # 点击匹配到的模板
                        if self.click_template(template_path, center, size):
                            matched = True
                            logger.info(f"[{self.get_task_name()}]模板 {template_path} 已处理完成, 相似度{match_val:.3f}", mode=self.log_mode)
                            
                            # 特殊处理
                            # 如果点击确认，记录点击并退出循环
                            if "template_img/que_ding.png" in template_path and "template_img/tui_chu_lun_jian.png" in self.clicked_templates:
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

    def start(self):
        """
        启动任务.
        """
        if not self._running:
            self._running = True
            self._stop_event.clear()  # 确保停止事件未设置
            self.clicked_templates.clear()  # 启动时清空点击记录
            logger.info(f"任务 {self.get_task_name()} 已启动", mode=self.log_mode)

    def stop(self):
        """
        停止任务.
        """
        if self._running:
            self._running = False
            self._stop_event.set()  # 设置停止事件
            self.clicked_templates.clear()  # 停止时清空点击记录
            logger.info(f"任务 {self.get_task_name()} 已停止", mode=self.log_mode)

    def __str__(self):
        """
        返回任务的字符串表示.
        """
        completed, total, percentage = self.get_progress()
        return f"LunJian(name={self.get_task_name()}(论剑), running={self._running}, progress={completed}/{total}({percentage:.1f}%))"
    