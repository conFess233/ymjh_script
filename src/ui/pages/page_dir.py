from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PySide6.QtGui import QPalette
# from PySide6.QtWebEngineWidgets import QWebEngineView  # 不再需要
import markdown
from ..core.theme_manager import theme_manager

class PageDir(QWidget):
    """
    目录页面类，包含使用说明。
    使用 QTextBrowser 代替 QWebEngineView。
    """
    def __init__(self):
        super().__init__()
        self.filepath = "src/ui/pages/README.md"
        # 替换为 QTextBrowser
        self.text_browser = QTextBrowser() 
        # 设置 QTextBrowser 阻止外部链接自动打开，如果有需要
        self.text_browser.setOpenExternalLinks(True) 

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # 添加 QTextBrowser 控件
        layout.addWidget(self.text_browser)
        theme_manager.theme_changed.connect(self.reload_content_on_theme_change)
        
        self.load_markdown_file(self.filepath)

    def load_markdown(self, md_text: str):
        current_theme = theme_manager.current_theme
        
        # 2. 从字典中提取所需颜色
        # 确保这些 key (@window_bg, @text, @base) 在你的 themes.py 中存在
        bg_color = current_theme.get("window_bg", "#FFFFFF") 
        fg_color = current_theme.get("text", "#000000")
        # *******************

        html = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])

        final_html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    background-color: {bg_color};
                    color: {fg_color};
                    /* 字体：优先使用 PingFang SC/微软雅黑，然后是通用无衬线字体 */
                    font-family: "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
                    padding: 20px;
                    line-height: 1.6;
                }}
                /* 确保代码块使用等宽字体，提高可读性 */
                pre, code {{
                    font-family: Consolas, Monaco, "Courier New", monospace;
                }}
                pre {{
                    background: #f0f0f0; 
                    padding: 10px;
                    border-radius: 5px;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
                a {{
                    color: #4eaaff; 
                }}
                img {{
                    max-width: 100%; 
                }}
            </style>
        </head>
        <body>{html}</body>
        </html>
        """

        self.text_browser.setHtml(final_html)

    def load_markdown_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                md = f.read()
            self.load_markdown(md)
        except FileNotFoundError:
            self.load_markdown(f"**错误：文件未找到。**\n\n请确保路径 `{filepath}` 正确。")

    def reload_content_on_theme_change(self, new_theme_colors: dict):
        """接收到主题变更信号后，重新加载文件内容，触发 load_markdown。"""
        # 注意：这里我们不需要 new_theme_colors，因为 load_markdown_file 会重新读取并调用 load_markdown
        # load_markdown_file -> load_markdown -> setHtml(新的颜色)
        self.load_markdown_file(self.filepath)