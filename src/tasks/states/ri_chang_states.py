from .state_base import State
from ...ui.core.logger import logger

class IdleState(State):
    """
    空闲状态，主要负责检测高频/突发事件，以及常规任务流程循环。
    """
    def execute(self):
        # 优先检测高频/突发事件：剧情
        if self.task.capture_and_match_template("template_img/tiao_guo_ju_qing.png"):
            return DialogState(self.task)

        # 检测是否已进入副本
        if match_result := self.task.capture_and_match_template("template_img/gua_ji.png") and "template_img/dan_ren_tiao_zhan.png" in self.task.clicked_templates:
            return CombatState(self.task)

        # 常规任务流程循环
        # 定义此状态下关心的模板列表
        targets = [
            "template_img/huo_dong.png",
            "template_img/huo_dong_hong_dian.png",
            "template_img/jiang_hu.png",
            "template_img/jiang_hu_ji_shi.png",
            "template_img/jiang_hu_ji_shi_1.png",
            "template_img/tiao_zhan.png",
            "template_img/dan_ren_tiao_zhan.png",
        ]
        
        matched = False
        for tmpl in targets:

            if self.task.check_timeout() or not self.task.running:
                return # 超时或被停止，退出任务逻辑
            # 跳过已点击的（防止重复点活动图标）
            if tmpl in self.task.clicked_templates:
                continue
            
            if tmpl == "template_img/huo_dong.png" and "template_img/huo_dong.png" not in self.task.clicked_templates:
                        huo_dong_result = self.task.capture_and_match_template(tmpl)
                        hong_dian_result = self.task.capture_and_match_template("template_img/huo_dong_hong_dian.png")
                        if huo_dong_result and hong_dian_result:
                            if huo_dong_result[1] > hong_dian_result[1]:
                                match_result = huo_dong_result
                            else:
                                match_result = hong_dian_result
                        else:
                            match_result = None
            else:
                match_result = self.task.capture_and_match_template(tmpl)

            if match_result:
                center, val, size = match_result 
                if center:
                    self.task.click_template(tmpl, center, size)
                    logger.info(f"[{self.task.get_task_name()}]模板 {tmpl} 已处理完成, 相似度{val:.3f}", mode=self.task.log_mode)
                    matched = True
                    self.sleep(self.task.click_delay)
        
        # 检查任务是否全部完成
        if not matched and self.task.is_task_completed():
            logger.info("日常副本任务流程已完成，退出任务", mode=self.task.log_mode)
            self.task.stop()
        
        self.sleep(self.task.match_loop_delay, is_random=False)
        return None # 保持当前状态

class DialogState(State):
    """
    剧情对话状态，主要负责处理剧情对话，直到遇到“跳过”按钮。暂时用不到，先把计数调小点用着。
    """
    def __init__(self, task):
        super().__init__(task)
        self.miss_count = 0 # 连续未检测到次数

    def execute(self):
        # 在剧情状态下，只检测“跳过”按钮
        match_result = self.task.capture_and_match_template("template_img/tiao_guo_ju_qing.png")
        
        if match_result:
            center, val, size = match_result
            if center:
                self.task.click_template("template_img/tiao_guo_ju_qing.png", center, size)
                self.miss_count = 0 # 重置计数
                self.sleep(0.5, is_random=False) # 点击后快速重试
                return None # 继续留在剧情状态
        
        # 如果连续几次没找到跳过，说明剧情可能结束了
        self.miss_count += 1
        if self.miss_count > 3:
            return IdleState(self.task) # 切回空闲状态重新扫描环境
            
        self.sleep(0.5, is_random=False)
        return None

class CombatState(State):
    """
    战斗/副本状态，主要负责处理战斗流程，直到副本结束。
    """
    def on_enter(self):
        super().on_enter()
        # 刚进副本，确保点击一次挂机
        if not "template_img/gua_ji.png" in self.task.clicked_templates:
            match_result = self.task.capture_and_match_template("template_img/gua_ji.png")
            if match_result:
                center, val, size = match_result
                self.task.click_template("template_img/gua_ji.png", center, size)
                self.sleep(self.task.click_delay)

    def execute(self):
        
        # 战斗中主要关注：是否结束战斗，跳过剧情
        if self.task.capture_and_match_template("template_img/tiao_guo_ju_qing.png"):
            return DialogState(self.task)
        
        # 检测退出副本（结束标志）
        if match_result := self.task.match_multiple_templates(["template_img/ri_chang_fu_ben_jie_shu.png", "template_img/ri_chang_fu_ben_tui_chu.png"],
                                                                      "template_img/ri_chang_fu_ben_tui_chu.png", direction='r', direction_size=60):
            center, val, size = match_result
            if center:
                self.task.click_template("template_img/ri_chang_fu_ben_tui_chu.png", center, size)
                self.sleep(2.0)
                self.task.auto_clicker.click(center[0], center[1])
                
        if "template_img/ri_chang_fu_ben_tui_chu.png" in self.task.clicked_templates:
            match_result = self.task.match_and_click("template_img/tui_ben_tui_dui.png")
            center, val, size = match_result
            if center:
                self.task.click_template("template_img/tui_ben_tui_dui.png", center, size)
                logger.info(f"[{self.task.get_task_name()}]已执行退出副本操作，结束任务。", mode=self.task.log_mode)
                self.task.stop()
        self.sleep(3.0)
        return None