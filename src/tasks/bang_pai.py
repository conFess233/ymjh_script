from .template_maching_task import TemplateMatchingTask
from ..ui.core.logger import logger
from .states.bang_pai_states import 



class BangPai(TemplateMatchingTask):
    """
    帮派任务流程
    """
    TASK_NAME = "帮派任务"

    def __init__(self, config: dict, log_mode: int = 0):
        super().__init__(config, log_mode)
        self.current_state = 
