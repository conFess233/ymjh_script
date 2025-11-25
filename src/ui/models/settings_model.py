from ..core.theme_manager import theme_manager
import json
import os
import atexit

class SettingsModel:
    """
    设置模型类，包含界面主题等设置.
    """
    def __init__(self, main_window=None, file_path="settings.json"):
        self.file_path = os.path.abspath(file_path)
        self.settings = {
            "theme": "light",
        }
        self.main_window = main_window
        
        self.load_settings()

        # 注册退出时的保存操作
        atexit.register(self.save_settings)
        
    
    def apply_theme(self, theme=None):
        """
        应用当前设置的主题.
        """
        if theme is None:
            theme = self.settings["theme"]
        if theme == "light" or theme == "浅色主题":
            theme_manager.apply_theme("light")
            self.settings["theme"] = "light"
        else:
            theme_manager.apply_theme("dark")
            self.settings["theme"] = "dark"
        
    def load_settings(self):
        """
        加载设置文件.
        """
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.settings.update(data)
        except FileNotFoundError:
            # 文件不存在则保存默认设置
            self.save_settings()
        self.apply_theme()

    def save_settings(self):
        """
        保存当前设置到文件.
        """
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
           # print("设置保存成功")
        except Exception as e:
            print(f"保存设置失败: {e}")
        

    def apply_settings(self, theme=None):
        """
        应用当前设置.

        Args:
            theme (str, optional): 主题. Defaults to None.
        """
        if theme is not None:
            self.settings["theme"] = theme

        self.save_settings()
        self.apply_theme()    
            
    def get_settings(self):
        """
        获取当前设置.
        """
        return self.settings
        
    def get_current_theme(self):
        """
        获取当前设置的主题.
        """
        return self.settings["theme"]