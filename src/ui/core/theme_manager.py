import os
import sys
from PySide6.QtCore import QObject, Signal
# 导入你的颜色定义
from .themes import LIGHT_THEME, DARK_THEME 

class ThemeManager(QObject):
    """
    主题管理类。
    负责管理应用的主题切换和应用。
    """
    theme_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.is_dark = False
        self.current_theme = LIGHT_THEME
        
        self.template_path = self.get_resource_path('styles.qss.template')

    def get_resource_path(self, relative_path):
        """
        获取资源文件的绝对路径。
        如果程序是打包后的，使用 sys._MEIPASS 临时路径；
        否则，使用程序运行时的当前路径。
        """
        if getattr(sys, 'frozen', False):
            # 如果程序被打包 (frozen)，资源在 sys._MEIPASS (临时文件夹) 中
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        else:
            # 如果程序未打包，资源在脚本所在的目录下
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        return os.path.join(base_path, relative_path)

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.current_theme = DARK_THEME if self.is_dark else LIGHT_THEME
        
        # 读取文件并生成样式
        try:
            qss = self._generate_qss()
            
            # 应用样式
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss) # type: ignore
                
            self.theme_changed.emit(self.current_theme)
            
        except FileNotFoundError:
            print(f"错误: 找不到样式文件 -> {self.template_path}")

    def apply_theme(self, theme_name: str):
        """根据主题名称切换主题"""
        self.is_dark = theme_name == "dark"
        self.current_theme = DARK_THEME if self.is_dark else LIGHT_THEME
        try:
            qss = self._generate_qss()
            
            # 应用样式
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss) # type: ignore
                
            self.theme_changed.emit(self.current_theme)
            
        except FileNotFoundError:
            print(f"错误: 找不到样式文件 -> {self.template_path}")

    def _generate_qss(self) -> str:
        """
        生成QSS样式字符串。

        Returns:
            str: 生成的QSS样式字符串。
        """
        
        # 读取外部文件内容
        with open(self.template_path, 'r', encoding='utf-8') as f:
            style_content = f.read()
            
        # 执行替换
        sorted_keys = sorted(self.current_theme.keys(), key=len, reverse=True)
        
        for key in sorted_keys:
            value = self.current_theme[key]
            style_content = style_content.replace(f"@{key}", value)
            
        return style_content
    
    def get_current_theme(self) -> dict:
        """
        获取当前主题.
        """
        return self.current_theme
    
    def is_dark_theme(self) -> bool:
        """
        判断是否为暗黑主题.
        """
        return self.is_dark

# 实例化
theme_manager = ThemeManager()