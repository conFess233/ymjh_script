from tasks.template_maching_task import TemplateMatchingTask
from time import sleep
import os
from typing import Optional, Tuple

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
        "template_img/huo_dong.png",
        "template_img/jiang_hu.png",
        "template_img/jiang_hu_ji_shi.png",
        "template_img/ri_chang.png",
        "template_img/tiao_zhan.png",
        "template_img/que_ren.png",
        "template_img/dan_ren_tiao_zhan.png",
        "template_img/gua_ji.png",
        "template_img/ri_chang_fu_ben_jie_shu.png",
        "template_img/tui_ben_tui_dui.png",
        "template_img/tiao_guo_ju_qing.png"
    ]

    def __init__(self):
        """初始化日常副本任务."""
        # 调用父类初始化
        super().__init__(default_match_threshold=0.7)

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

    def process_special_templates(self, template_path: str, match_result: Optional[tuple], screenshot_w: int, screenshot_h: int):
        """
        处理特殊模板的坐标修改.

        Args:
            template_path: 模板路径
            match_result: 原始匹配结果
            screenshot_w: 截图宽度
            screenshot_h: 截图高度

        Returns:
            tuple: 处理后的匹配结果
        """
        # 特殊处理：如果模板路径是ri_chang_fu_ben_jie_shu.png，将横坐标设置为屏幕边缘
        if "template_img/ri_chang_fu_ben_jie_shu.png" in template_path and match_result is not None:
            center, match_val = match_result
            if center:
                _, y = center  # 保持原始纵坐标
                edge_x = screenshot_w - 20 # 设置为屏幕右侧边缘
                modified_center = (edge_x, y)
                match_result = (modified_center, match_val)
                print(f"特殊处理模板 {template_path}: 坐标从 {center} 修改为 {modified_center}")
        
        return match_result

    def execute_task_logic(self):
        """执行具体的任务逻辑."""
        self.start()
        
        # 验证模板文件
        if not self.validate_templates():
            print("模板文件验证失败，任务无法启动")
            return

        try:
            while self.running:
                matched = False
                
                # 遍历所有模板
                for template_path in self.get_template_path_list():
                    # 跳过已点击的模板
                    if template_path in self.clicked_templates:
                        continue
                    
                    # 捕获截图并匹配模板
                    match_result = self.capture_and_match_template(template_path, None)
                    if match_result is None:
                        continue  # 捕获失败，继续下一个模板
                    
                    center, match_val = match_result
                    if center:
                        # 点击匹配到的模板
                        if self.click_template(template_path, center):
                            matched = True
                            print(f"模板 {template_path} 已处理完成, 相似度{match_val:.3f}, 任务进度: {self.get_progress()[0]}/{self.get_progress()[1]} ({self.get_progress()[2]:.1f}%)")
                            if template_path == "template_img/tui_ben_tui_dui.png":
                                print("已执行退出副本操作，结束任务。")
                                self.stop()
                            break  # 找到一个匹配后跳出循环
                    else:
                        print(f"模板 {template_path} 未匹配到有效位置, 相似度:{match_val:.3f}")
                        sleep(self.default_template_retry_delay)

                # 如果没有匹配到任何模板，检查是否已完成所有任务
                if not matched:
                    print("本轮未找到任何匹配模板")
                    if self.is_task_completed():
                        print("所有模板已处理完成，任务结束")
                        break
                
                # 等待下次循环
                sleep(self.default_click_delay)

        except KeyboardInterrupt:
            print("任务被手动停止。")
        finally:
            self.stop()

    def start(self):
        """启动任务."""
        if not self._running:
            self._running = True
            self.clicked_templates.clear()  # 启动时清空点击记录
            print(f"任务 {self.get_task_name()} 已启动")
        else:
            print(f"任务 {self.get_task_name()} 已经在运行")

    def stop(self):
        """停止任务."""
        if self._running:
            self._running = False
            self.clicked_templates.clear()  # 停止时清空点击记录
            print(f"任务 {self.get_task_name()} 已停止")
        else:
            print(f"任务 {self.get_task_name()} 未在运行")

    def __str__(self):
        """返回任务的字符串表示."""
        completed, total, percentage = self.get_progress()
        return f"RiChangFuBen(name={self.get_task_name()}(日常副本), running={self._running}, progress={completed}/{total}({percentage:.1f}%))"
    
    # 添加一个便捷方法来运行任务
    def run(self):
        """运行日常副本任务."""
        self.execute_task_logic()

if __name__ == "__main__":
    task = RiChangFuBen()
    task.run()