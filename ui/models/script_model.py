from tasks.ri_chang_fu_ben import RiChangFuBen
from tasks.lun_jian import LunJian

class ScriptModel:
    """
    脚本模型类，包含脚本列表、脚本设置等.
    """
    def __init__(self, window=None):
        self.window = window
        self.scripts = [
            RiChangFuBen(),
            LunJian()
        ]
        self.run_list = []
        self.running_task = None
        self.status = "未运行"
        self.progress = 0


    def get_scripts(self):
        return self.scripts
    
    def get_run_list(self):
        return self.run_list
    
    def get_status(self):
        return self.status
    
    def get_task_names(self):
        task_names = [script.get_task_name() for script in self.scripts]
        return task_names
    
