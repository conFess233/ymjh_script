import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QStackedLayout
)
from .pages.page_dir import PageDir
from .pages.page_task import PageScript
from .pages.page_setting import PageSetting
from .core.theme_manager import theme_manager
from .models.settings_model import SettingsModel
from .pages.page_multiple import PageMultiple
from .core.logger import logger

class MainWindow(QMainWindow):
    """
    主窗口类，包含导航栏和内容区域.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YMJH Script")
        self.setGeometry(200, 100, 1200, 800)

        # 主布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # 左侧导航栏
        self.nav_widget = QWidget()
        self.nav_widget.setFixedWidth(180)
        self.nav_layout = QVBoxLayout(self.nav_widget)
        self.nav_layout.setSpacing(20)
        self.nav_layout.setContentsMargins(10, 20, 10, 20)

        self.btn_dir = QPushButton("使用说明")
        self.btn_script = QPushButton("脚本执行")
        self.btn_multiple = QPushButton("多开")
        self.btn_setting = QPushButton("设置")

        for btn in [self.btn_dir, self.btn_script, self.btn_multiple, self.btn_setting]:
            btn.setMinimumHeight(40)
            self.nav_layout.addWidget(btn)
        self.nav_layout.addStretch()
        self.main_layout.addWidget(self.nav_widget)

        # 右侧内容区
        self.content_widget = QWidget()
        self.stack_layout = QStackedLayout(self.content_widget)
        self.main_layout.addWidget(self.content_widget, 1)

        # 页面
        self.page_dir = PageDir()
        self.page_script = PageScript()
        self.page_multiple = PageMultiple()
        self.page_setting = PageSetting(main_window=self)

        self.stack_layout.addWidget(self.page_dir)
        self.stack_layout.addWidget(self.page_script)
        self.stack_layout.addWidget(self.page_multiple)
        self.stack_layout.addWidget(self.page_setting)
        # 映射
        self.page_dict = {
            "dir": (self.page_dir, self.btn_dir),
            "script": (self.page_script, self.btn_script),
            "multiple": (self.page_multiple, self.btn_multiple),
            "setting": (self.page_setting, self.btn_setting)
        }

        # 按钮绑定
        self.btn_dir.clicked.connect(lambda: self.switch_page("dir"))
        self.btn_script.clicked.connect(lambda: self.switch_page("script"))
        self.btn_multiple.clicked.connect(lambda: self.switch_page("multiple"))
        self.btn_setting.clicked.connect(lambda: self.switch_page("setting"))
        self.switch_page("dir")

        # 控制器
        # 设置
        self.settings_model = SettingsModel()
        current_theme = self.settings_model.get_current_theme() if self.settings_model.get_current_theme() else "light"
        theme_manager.apply_theme(current_theme)

    # 页面切换
    def switch_page(self, name):
        """
        切换到指定页面.
        Args:
            name (str): 页面名称，必须在 self.page_dict 中
        """
        page, btn = self.page_dict[name]
        index = self.stack_layout.indexOf(page)
        self.stack_layout.setCurrentIndex(index)
        for _, b in self.page_dict.values():
            b.setEnabled(True)
            b.setStyleSheet("")
        btn.setEnabled(False)
        btn.setStyleSheet("background-color: #0078D7; color: white; font-weight: bold;")

    def closeEvent(self, event):
        """
        窗口关闭事件：在此处清理所有线程，防止报错或残留
        """
        logger.info("程序正在退出，开始清理线程...", mode=1)

        # 清理多开页面的所有任务线程
        if hasattr(self.page_multiple, 'manager'):
            self.page_multiple.manager.clear_items()

        # 清理脚本执行页面的任务线程
        if hasattr(self.page_script, 'model'):
            # 如果正在运行，先停止
            self.page_script.model.stop_queue()
            # 等待内部 Python 线程结束，防止它在 QObject 销毁后继续发射信号
            if hasattr(self.page_script.model, 'wait_for_stop'):
                self.page_script.model.wait_for_stop(timeout=1.0)

        # 确保日志等资源保存
        logger.save_log_to_file()

        super().closeEvent(event)

def is_admin() -> bool:
    """
    检查当前是否以管理员权限运行
    """
    import ctypes
    try:
        # 检查用户是否为管理员
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
    
def show_admin_warning():
    """
    显示管理员权限警告
    """
    from PySide6.QtWidgets import QMessageBox
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning) # type: ignore
    msg.setText("警告")
    msg.setInformativeText("当前用户不是管理员，部分功能可能受限。\n是否继续？")
    msg.setWindowTitle("管理员权限警告")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No) # type: ignore
    ret = msg.exec()
    return ret == QMessageBox.Yes # type: ignore

def run():
    """
    主函数，启动应用.
    """
    app = QApplication(sys.argv)
    if not is_admin():
        if not show_admin_warning():
            sys.exit(1)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
