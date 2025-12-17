from .template_maching_task import TemplateMatchingTask
from ..ui.core.logger import logger
from .states.ri_chang_states import IdleState

class RiChangFuBen(TemplateMatchingTask):
    """
    日常副本任务类.

    自动执行日常副本相关操作，包括活动、挑战等流程。
    """
    
    TASK_NAME = "日常副本"  # 日常副本任务
    # 模板图片路径列表，仅用于初始化
    TEMPLATE_PATH_LIST = [
        "template_img/huo_dong.png",
        "template_img/huo_dong_hong_dian.png",
        "template_img/jiang_hu.png",
        "template_img/jiang_hu_ji_shi.png",
        "template_img/jiang_hu_ji_shi_1.png",
        "template_img/tiao_zhan.png",
        "template_img/dan_ren_tiao_zhan.png",
        "template_img/gua_ji.png",
        "template_img/tiao_guo_ju_qing.png",
        "template_img/ri_chang_fu_ben_jie_shu.png",
        "template_img/tui_ben_tui_dui.png",
        "template_img/ri_chang_fu_ben_tui_chu.png",
    ]

    def __init__(self, config: dict, log_mode: int = 0):
        """
        初始化日常副本任务.
        """
        # 调用父类初始化
        super().__init__(config, log_mode)
        self.current_state = None # 当前状态

    def get_template_path_list(self) -> list:
        """
        获取模板路径列表.

        Returns:
            list: 模板图片路径列表
        """
        return self.TEMPLATE_PATH_LIST

    def execute_task_logic(self):
        """
        执行具体的任务逻辑.
        """
        # 验证模板文件
        if not self.validate_templates():
            logger.error(f"[{self.get_task_name()}]模板验证失败", mode=self.log_mode)
            return
        
        # 初始化状态机：进入 Idle 状态
        self.current_state = IdleState(self)
        self.current_state.on_enter()
        
        try:
            while self.running:
                # 超时检查
                if self.check_timeout():
                    return
                
                # 状态机流转
                # execute() 返回下一个状态实例，或者 None
                next_state = self.current_state.execute()
                
                if next_state is not None:
                    # 切换状态流程：退出旧状态 -> 更新引用 -> 进入新状态
                    self.current_state.on_exit()
                    self.current_state = next_state
                    self.current_state.on_enter()
                
        except KeyboardInterrupt:
            logger.info(f"[{self.get_task_name()}]任务被停止。", mode=self.log_mode)
        except Exception as e:
            logger.error(f"[{self.get_task_name()}] 异常: {e}", mode=self.log_mode)
            import traceback
            logger.error(traceback.format_exc(), mode=self.log_mode)
        
        return
    
    def add_clicked_template(self, template_path: str):
        """
        添加已点击的模板记录.

        Args:
            template_path (str): 模板图片路径
        """
        if not "tiao_guo_ju_qing.png" in template_path:
                self.clicked_templates.add(template_path)
        if template_path in ["template_img/huo_dong.png", "template_img/huo_dong_hong_dian.png"]:
            self.clicked_templates.update(["template_img/huo_dong.png", "template_img/huo_dong_hong_dian.png"])
        elif template_path in ["template_img/jiang_hu_ji_shi.png", "template_img/jiang_hu_ji_shi_1.png"]:
            self.clicked_templates.update(["template_img/jiang_hu_ji_shi.png", "template_img/jiang_hu_ji_shi_1.png"])

    def __str__(self):
        """
        返回任务的字符串表示.
        """
        completed, total, percentage = self.get_progress()
        return f"RiChangFuBen(name={self.get_task_name()}, running={self._running}, progress={completed}/{total}({percentage:.1f}%))"
    