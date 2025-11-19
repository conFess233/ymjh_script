from PySide6.QtWidgets import QApplication, QListWidget, QMenu, QMessageBox, QAbstractItemView
from PySide6.QtCore import Qt
import sys

class TaskList(QListWidget):
    def __init__(self):
        super().__init__()
        self.addItems(["项目 1", "项目 2", "项目 3"])

        # 启用自定义右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu) # type: ignore
        self.customContextMenuRequested.connect(self.open_menu)
        self.setDragDropMode(QAbstractItemView.InternalMove) # type: ignore
        self.setAcceptDrops(True)
        self.setSortingEnabled(True)

   # -----------------------------
    # 右键菜单
    # -----------------------------
    def open_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            return

        row = self.row(item)
        count = self.count()

        menu = QMenu(self)

        act_up = menu.addAction("上移")
        act_down = menu.addAction("下移")
        act_top = menu.addAction("移动到顶部")
        act_bottom = menu.addAction("移动到底部")
        menu.addSeparator()
        act_delete = menu.addAction("删除")

        action = menu.exec(self.mapToGlobal(pos))
        if not action:
            return

        if action == act_up:
            self.move_item_up(row)

        elif action == act_down:
            self.move_item_down(row)

        elif action == act_top:
            self.move_item_to(row, 0)

        elif action == act_bottom:
            self.move_item_to(row, count - 1)

        elif action == act_delete:
            item = self.takeItem(row)
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