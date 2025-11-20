from controllers.theme_controller import ThemeController
import json
import os
import atexit

class SettingsModel:
    """
    设置模型类，包含界面主题、字体大小等设置.
    """
    def __init__(self, main_window=None, file_path="settings.json"):
        self.file_path = os.path.abspath(file_path)
        self.settings = {
            "theme": "light",
            "font_size": 12
        }
        self.main_window = main_window
        
        self.theme_controller = ThemeController(self.main_window)
        
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
            self.theme_controller.apply_light()
            self.settings["theme"] = "light"
        else:
            self.theme_controller.apply_dark()
            self.settings["theme"] = "dark"
        
    
    def apply_font_size(self):
        """
        应用当前设置的字体大小.
        """
        #self.main_window.setFontSize(self.settings["font_size"])
        #self.main_window.repaint()
        
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
        self.set_current_font_size(self.settings["font_size"])

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
        

    def apply_settings(self, theme=None, font_size=None):
        """
        应用当前设置.

        Args:
            theme (str, optional): 主题. Defaults to None.
            font_size (int, optional): 字体大小. Defaults to None.
        """
        if theme is not None:
            self.settings["theme"] = theme
        if font_size is not None:
            self.settings["font_size"] = font_size

        self.save_settings()
        self.apply_theme()    
        self.apply_font_size()
            
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
    
    def get_current_font_size(self):
        """
        获取当前设置的字体大小.
        """
        return self.settings["font_size"]
    
    def set_current_font_size(self, font_size):
        """
        设置当前字体大小.
        """
        self.settings["font_size"] = font_size
        # self.apply_font_size()
        