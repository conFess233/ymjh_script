import os
from PySide6.QtCore import QObject, Signal
# 导入你的颜色定义
from .themes import LIGHT_THEME, DARK_THEME 

class ThemeManager(QObject):
    theme_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.is_dark = False
        self.current_theme = LIGHT_THEME
        
        # 模板文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.template_path = os.path.join(current_dir, 'styles.qss.template')

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.current_theme = DARK_THEME if self.is_dark else LIGHT_THEME
        
        # 2. 读取文件并生成样式
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

    def _generate_qss(self):
        """读取文件内容 -> 替换变量 -> 返回最终字符串"""
        
        # 3. 读取外部文件内容
        with open(self.template_path, 'r', encoding='utf-8') as f:
            style_content = f.read()
            
        # 4. 执行替换 (记得加上你之前的排序修复！)
        sorted_keys = sorted(self.current_theme.keys(), key=len, reverse=True)
        
        for key in sorted_keys:
            value = self.current_theme[key]
            style_content = style_content.replace(f"@{key}", value)
            
        return style_content
    
    def get_current_theme(self):
        return self.current_theme
    
    def is_dark_theme(self):
        return self.is_dark

# 实例化
theme_manager = ThemeManager()