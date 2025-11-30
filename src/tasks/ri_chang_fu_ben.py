from .template_maching_task import TemplateMatchingTask
from ..ui.core.logger import logger

class RiChangFuBen(TemplateMatchingTask):
    """
    日常副本任务类.

    自动执行日常副本相关操作，包括活动、挑战等流程。
    """
    
    TASK_NAME = "ri_chang_fu_ben"  # 日常副本任务
    # 模板图片路径列表
    TEMPLATE_PATH_LIST = [
        "template_img/huo_dong.png",
        "template_img/huo_dong_hong_dian.png",
        "template_img/jiang_hu.png",
        "template_img/jiang_hu_ji_shi.png",
        "template_img/jiang_hu_ji_shi_1.png",
        "template_img/tiao_zhan.png",
        "template_img/que_ren.png",
        "template_img/dan_ren_tiao_zhan.png",
        "template_img/gua_ji.png",
        "template_img/tiao_guo_ju_qing.png",
        "template_img/ri_chang_fu_ben_jie_shu.png",
        "template_img/tui_ben_tui_dui.png",
    ]

    def __init__(self, config: dict):
        """初始化日常副本任务."""
        # 调用父类初始化
        super().__init__(config)

    def get_template_path_list(self) -> list:
        """
        获取模板路径列表.

        Returns:
            list: 模板图片路径列表
        """
        return self.TEMPLATE_PATH_LIST

    def get_task_name(self) -> str:
        """
        获取任务名称.

        Returns:
            str: 任务名称
        """
        return "日常副本"

    def execute_task_logic(self):
        """执行具体的任务逻辑."""
        # 验证模板文件
        if not self.validate_templates():
            logger.error(f"[{self.get_task_name()}]模板文件验证失败，任务无法启动")
            return
        
        try:
            while self.running:
                # 每次循环开始时检查是否超时
                if self.check_timeout():
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
                    if "ri_chang_fu_ben_jie_shu.png" in template_path:
                        match_result = self.match_multiple_templates([template_path, "template_img/ri_chang_fu_ben_tui_chu.png"], "template_img/ri_chang_fu_ben_tui_chu.png", match_val_threshold=self.match_threshold)
                    else:
                        match_result = self.capture_and_match_template(template_path)
                    
                    if match_result is None:
                        if self._sleep(self.template_retry_delay):
                            return
                        continue
                    
                    center, match_val = match_result
                    if center:
                        # 点击匹配到的模板
                        if self.click_template(template_path, center):
                            matched = True
                            logger.info(f"[{self.get_task_name()}]模板 {template_path} 已处理完成, 相似度{match_val:.3f}")
                            
                            # 特殊模板处理
                            if template_path in ["template_img/huo_dong.png", "template_img/huo_dong_hong_dian.png"]:
                                self.clicked_templates.update(["template_img/huo_dong.png", "template_img/huo_dong_hong_dian.png"])
                            elif template_path in ["template_img/jiang_hu_ji_shi.png", "template_img/jiang_hu_ji_shi_1.png"]:
                                self.clicked_templates.update(["template_img/jiang_hu_ji_shi.png", "template_img/jiang_hu_ji_shi_1.png"])
                                
                            if "ri_chang_fu_ben_jie_shu.png" in template_path:
                                self._sleep(1)
                                self.auto_clicker.click(center[0], center[1])

                            # 若提前点击退本按钮，直接退出任务
                            if "tui_ben_tui_dui.png" in template_path:
                                logger.info(f"[{self.get_task_name()}]已执行退出副本操作，结束任务。")
                                self.stop() # 停止任务，退出 while 循环
                                return 
                            
                            self._sleep(self.click_delay)
                            break  # 找到一个匹配后跳出 for 循环
                    else:
                        logger.info(f"[{self.get_task_name()}]模板 {template_path} 未匹配到有效位置, 相似度:{match_val:.3f}")
                        # 模板匹配失败，等待重试时检查停止/超时
                        if self._sleep(self.template_retry_delay):
                            return


                # 如果没有匹配到任何模板，检查是否已完成所有任务
                if not matched:
                    if self.is_task_completed():
                        logger.info(f"[{self.get_task_name()}]所有模板已处理完成，任务结束")
                        break # 完成所有模板，退出 while 循环
                
                # 等待下次循环 
                # 每次等待时检查是否停止或超时
                if self._sleep(self.match_loop_delay):
                    return # 被停止，退出任务逻辑
                
            logger.info(f"[{self.get_task_name()}]任务逻辑自然退出。")

        except KeyboardInterrupt:
            logger.info(f"[{self.get_task_name()}]任务被手动停止。")
        return # 任务逻辑结束

    def start(self):
        """启动任务."""
        if not self._running:
            self._running = True
            self._stop_event.clear()  # 确保事件未被设置
            self.clicked_templates.clear()  # 启动时清空点击记录
            logger.info(f"[{self.get_task_name()}]任务已启动")

    def stop(self):
        """停止任务."""
        if self._running:
            self._running = False
            self.clicked_templates.clear()  # 停止时清空点击记录
            self._stop_event.set()  # 设置事件，通知任务停止
            logger.info(f"[{self.get_task_name()}]任务已停止")

    def __str__(self):
        """返回任务的字符串表示."""
        completed, total, percentage = self.get_progress()
        return f"RiChangFuBen(name={self.get_task_name()}(日常副本), running={self._running}, progress={completed}/{total}({percentage:.1f}%))"
    