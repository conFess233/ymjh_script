from .state_base import State
from ...ui.core.logger import logger

class IdleState(State):
    """
    空闲状态，主要负责检测高频/突发事件，以及常规任务流程循环。
    """
    def execute(self):
        # 优先检测高频/突发事件：剧情
        if self.task.capture_and_match_template(self.task.TEMPLATE_LIST.get("tiao_guo_ju_qing")):
            return DialogState(self.task)

        # 检测是否已进入副本
        if match_result := self.task.capture_and_match_template(self.task.TEMPLATE_LIST.get("gua_ji")) and self.task.TEMPLATE_LIST.get("huo_dong").get("path") in self.task.clicked_templates:
            return CombatState(self.task)

        # 常规任务流程循环
        # 定义此状态下关心的模板列表
        targets = {
            "huo_dong": self.task.TEMPLATE_LIST.get("huo_dong"),
            "huo_dong_hong_dian": self.task.TEMPLATE_LIST.get("huo_dong_hong_dian"),
            "jiang_hu": self.task.TEMPLATE_LIST.get("jiang_hu"),
            "jiang_hu_ji_shi": self.task.TEMPLATE_LIST.get("jiang_hu_ji_shi"),
            "jiang_hu_ji_shi_1": self.task.TEMPLATE_LIST.get("jiang_hu_ji_shi_1"),
            "tiao_zhan": self.task.TEMPLATE_LIST.get("tiao_zhan"),
            "dan_ren_tiao_zhan": self.task.TEMPLATE_LIST.get("dan_ren_tiao_zhan"),
        }
        
        matched = False
        for key in targets.keys():
            tmpl = targets[key]
            # print(f"检查模板 {key}: {tmpl.get('path')}, {tmpl.get('rect')}, {tmpl.get('base_size')}")
            if self.task.check_timeout() or not self.task.running:
                return # 超时或被停止，退出任务逻辑
            # 跳过已点击的（防止重复点活动图标）
            if tmpl.get("path") in self.task.clicked_templates:
                continue
            
            if tmpl == targets["huo_dong"] and tmpl.get("path") not in self.task.clicked_templates:
                        huo_dong_result = self.task.capture_and_match_template(tmpl)
                        hong_dian_result = self.task.capture_and_match_template(targets["huo_dong_hong_dian"])
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
                    self.task.click_template(tmpl.get("path"), center, size)
                    # logger.info(f"[{self.task.get_task_name()}]模板 {key} 已处理完成, 相似度{val:.3f}", mode=self.task.log_mode)
                    matched = True
                    self.sleep(self.task.click_delay)
            else:
                self.sleep(self.task.template_retry_delay)
        
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
        match_result = self.task.capture_and_match_template(self.task.TEMPLATE_LIST.get("tiao_guo_ju_qing"))
        
        if match_result:
            center, val, size = match_result
            if center:
                self.task.click_template(self.task.TEMPLATE_LIST.get("tiao_guo_ju_qing").get("path"), center, size)
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
            match_result = self.task.capture_and_match_template(self.task.TEMPLATE_LIST.get("gua_ji"))
            if match_result:
                center, val, size = match_result
                self.task.click_template(self.task.TEMPLATE_LIST.get("gua_ji").get("path"), center, size)
                self.sleep(self.task.click_delay)

    def execute(self):
        
        # 战斗中主要关注：是否结束战斗，跳过剧情
        if self.task.capture_and_match_template(self.task.TEMPLATE_LIST.get("tiao_guo_ju_qing")):
            return DialogState(self.task)
        
        # 检测退出副本（结束标志）
        if match_result := self.task.match_multiple_templates([self.task.TEMPLATE_LIST.get("ri_chang_fu_ben_jie_shu"), self.task.TEMPLATE_LIST.get("ri_chang_fu_ben_tui_chu")],
                                                                      self.task.TEMPLATE_LIST.get("ri_chang_fu_ben_tui_chu"), match_val_threshold=0.68):
            center, val, size = match_result
            if center:
                self.task.click_template(self.task.TEMPLATE_LIST.get("ri_chang_fu_ben_tui_chu").get("path"), center, size)
                self.sleep(2.0)
                self.task.auto_clicker.click(center[0], center[1])
                self.sleep(2.0)
        if self.task.TEMPLATE_LIST.get("ri_chang_fu_ben_tui_chu").get("path") in self.task.clicked_templates:
            match_result = self.task.capture_and_match_template(self.task.TEMPLATE_LIST.get("tui_ben_tui_dui"))
            center, val, size = match_result
            if center:
                self.task.click_template(self.task.TEMPLATE_LIST.get("tui_ben_tui_dui").get("path"), center, size)
                logger.info(f"[{self.task.get_task_name()}]已执行退出副本操作，结束任务。", mode=self.task.log_mode)
                self.task.stop()
        self.sleep(3.0)
        return None