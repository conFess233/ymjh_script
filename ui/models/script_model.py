# from tasks.ri_chang_fu_ben import RiChangFuBen
# from tasks.lun_jian import LunJian

class ScriptModel:
    """
    脚本模型类，包含脚本列表、脚本设置等.
    """
    def __init__(self, window=None):
        self.window = window
        # self.scripts = [
        #     RiChangFuBen(),
        #     LunJian()
        # ]
        self.tasks = [
            "日常副本",
            "论剑"
        ]
        self.run_list = []
        self.running_task = None
        self.status = "未运行"
        self.progress = 0


    def get_tasks(self):
        """
        获取任务列表.

        Returns:
            list: 任务列表.
        """
        return self.tasks
    
    def get_run_list(self):
        """
        获取运行列表.

        Returns:
            list: 运行列表.
        """
        return self.run_list
    
    def get_status(self):
        """
        获取脚本运行状态.

        Returns:
            str: 脚本运行状态.
        """
        return self.status
    
    def get_task_names(self):
        """
        获取任务名称列表.

        Returns:
            list: 任务名称列表.
        """
        # task_names = [script.get_task_name() for script in self.tasks]
        return self.tasks
    
    def get_progress(self):
        """
        获取脚本运行进度.

        Returns:
            int: 脚本运行进度.
        """
        return self.progress
    
    def set_progress(self, progress: int):
        """
        设置脚本运行进度.

        Args:
            progress (int): 脚本运行进度.
        """
        self.progress = progress
        
    def set_status(self, status: str):
        """
        设置脚本运行状态.

        Args:
            status (str): 脚本运行状态.
        """
        self.status = status
        
    def set_running_task(self, task: str):
        """
        设置当前运行任务.

        Args:
            task (str): 当前运行任务.
        """
        self.running_task = task
        
    def get_running_task(self):
        """
        获取当前运行任务.

        Returns:
            str: 当前运行任务.
        """
        return self.running_task
