from PySide6.QtWidgets import QApplication, QListWidget, QMenu, QMessageBox, QAbstractItemView
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from core.logger import logger

class TaskList(QListWidget):
    def __init__(self, palacehodler=""):
        super().__init__()
        self.palaceholder = palacehodler

        # 启用自定义右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu) # type: ignore
        self.customContextMenuRequested.connect(self.open_menu)
        self.setDragDropMode(QAbstractItemView.InternalMove) # type: ignore
        self.setAcceptDrops(True)
        self.setSortingEnabled(True)
        
        self.setPlaceholderText(self.palaceholder)

    def setPlaceholderText(self, text):
        """
        设置占位符文本，当列表为空时显示.

        Args:
            text (str): 占位符文本.
        """
        self.placeholder = text
        
    def paintEvent(self, event):
        super().paintEvent(event)

        # 当列表为空时绘制提示文字
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(150, 150, 150))  # 灰色文字

            # 垂直居中显示
            x = 10
            y = self.height() // 2
            painter.drawText(x, y, self.placeholder)
            
    def open_menu(self, pos):
        """
        打开右键菜单，根据鼠标位置获取对应的条目并显示菜单.

        Args:
            pos (QPoint): 鼠标点击位置，用于确定要操作的条目.
        """
        # 根据鼠标位置获取对应的条目
        item = self.itemAt(pos)
        if not item:
            # 如果没有条目则直接返回
            return

        # 获取条目的行号和总条目数
        row = self.row(item)
        count = self.count()

        # 创建右键菜单
        menu = QMenu(self)

        # 添加“上移”、“下移”、“移动到顶部”、“移动到底部”操作
        act_up = menu.addAction("上移")
        act_down = menu.addAction("下移")
        act_top = menu.addAction("移动到顶部")
        act_bottom = menu.addAction("移动到底部")
        menu.addSeparator()  # 添加分隔线
        act_delete = menu.addAction("删除")  # 添加“删除”操作

        # 显示菜单，并获取用户选择的操作
        action = menu.exec(self.mapToGlobal(pos))
        if not action:
            # 如果没有选择任何操作则返回
            return

        # 根据用户选择的操作执行对应的方法
        if action == act_up:
            self.move_item_up(row)

        elif action == act_down:
            self.move_item_down(row)

        elif action == act_top:
            self.move_item_to(row, 0)

        elif action == act_bottom:
            self.move_item_to(row, count - 1)

        elif action == act_delete:
            # 删除条目并记录日志
            item = self.takeItem(row)
            logger.log(f"删除任务: {item.text()}")
            del item
            

    def move_item_up(self, row):
        if row <= 0:
            return
        self.move_item_to(row, row - 1)

    def move_item_down(self, row):
        if row >= self.count() - 1:
            return
        self.move_item_to(row, row + 1)

    def move_item_to(self, old_row, new_row):
        if old_row == new_row:
            return

        item = self.takeItem(old_row)  # 取出旧位置的 item
        self.insertItem(new_row, item)  # 插到新位置
        self.setCurrentRow(new_row)  # 选中新的位置
        logger.log(f"任务 {item.text()} 移动到 {new_row}")