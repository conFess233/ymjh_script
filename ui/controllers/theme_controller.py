class ThemeController:
    """
    主题控制器类，负责应用不同的主题.
    """
    def __init__(self, main_window):
        self.window = main_window

    def apply_light(self):
        self.window.apply_light_theme()

    def apply_dark(self):
        self.window.apply_dark_theme()
        
    