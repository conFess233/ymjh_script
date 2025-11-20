from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
import markdown

class PageDir(QWidget):
    """
    目录页面类，包含使用说明.
    """
    def __init__(self):
        super().__init__()
        self.filepath = "ui/pages/README.md"
        self.web = QWebEngineView()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.addWidget(self.web)
        
        self.load_markdown_file(self.filepath)

    def load_markdown(self, md_text: str):
        bg = self.palette().window().color().name()
        fg = self.palette().windowText().color().name()

        html = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])

        final_html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    width: 100%;
                    max-width: 100%;
                    box-sizing: border-box;
                    background-color: {bg};
                    color: {fg};
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    line-height: 1.6;
                }}
                img {{
                    max-width: 100%;
                }}
                pre {{
                    background: {fg}22;    /* 代码块适配背景 */
                    padding: 10px;
                    border-radius: 5px;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
                code {{
                    font-family: Consolas, monospace;
                }}
                a {{
                    color: #4eaaff;
                }}
            </style>
        </head>
        <body>{html}</body>
        </html>
        """

        self.web.setHtml(final_html)

    def load_markdown_file(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            md = f.read()
        self.load_markdown(md)