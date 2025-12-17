from PySide6.QtWidgets import QListWidget, QMenu, QAbstractItemView, QListWidgetItem
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor
from ..core.logger import logger
from PySide6.QtCore import Signal

class TaskList(QListWidget):
    """
    任务列表组件，支持右键菜单、拖放排序，并与 TaskModel 同步。
    """
    def __init__(self, task_model, placeholder="请从右侧选择任务添加到此处"):
        super().__init__()
        self.task_model = task_model
        self.placeholder = placeholder

        # 启用自定义右键菜单

        self.setContextMenuPolicy(Qt.CustomContextMenu) # type: ignore
        self.customContextMenuRequested.connect(self.open_menu)
        self.setDragDropMode(QAbstractItemView.InternalMove) # type: ignore
        self.setAcceptDrops(True)
        self.setSortingEnabled(False)
        self.setPlaceholderText(self.placeholder)
        
        # 连接 TaskModel 的信号来刷新 UI
        self.task_model.run_list_changed.connect(self.refresh_list_from_model)
        
        # 初始刷新
        self.refresh_list_from_model()

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

    def refresh_list_from_model(self):
        """
        根据 TaskModel 中的 _run_list 刷新 UI 列表。
        
        注意：Model 中存储的是任务实例 (Task Instance)，UI 中存储的是任务名称 (Task Name)。
        """
        # 清空现有列表
        self.clear()
        
        # 从 Model 中获取任务实例，并添加到 UI 列表中
        for task_instance in self.task_model.get_run_list():
            task_name = task_instance.get_task_name()
            # 确保添加到 UI 列表的是任务名称
            item = QListWidgetItem(task_name)
            self.addItem(item)

    def open_menu(self, pos: QPoint):
        """
        打开任务列表的右键菜单，包含上移、下移、移动到顶部、移动到底部、删除操作。
        """
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
            self.move_task_action(row, row - 1)

        elif action == act_down:
            self.move_task_action(row, row + 1)

        elif action == act_top:
            self.move_task_action(row, 0)

        elif action == act_bottom:
            self.move_task_action(row, count - 1)

        elif action == act_delete:
            self.delete_task_action(row, item.text())


    def delete_task_action(self, row: int, task_name: str):
        """
        删除任务并通知 Model。
        """
        self.task_model.remove_task_by_index(row) 
        self.refresh_list_from_model

    def move_task_action(self, old_row: int, new_row: int):
        """
        移动任务，仅通知 Model。UI 刷新由 Model 信号触发。
        """
        if old_row == new_row or new_row < 0 or new_row >= self.count():
            return
        
        # 仅通知 Model
        self.task_model.move_task(old_row, new_row)
        
        item_text = self.item(old_row).text() if self.item(old_row) else "Unknown Task"

    # --- 拖放功能 目前未实现 ---

    def move_item_up(self, row):
        """
        上移任务，仅通知 Model。UI 刷新由 Model 信号触发。
        """
        if row <= 0:
            return
        self.move_task_action(row, row - 1)

    def move_item_down(self, row):
        """
        下移任务，仅通知 Model。UI 刷新由 Model 信号触发。
        """
        if row >= self.count() - 1:
            return
        self.move_task_action(row, row + 1)

class MultipleTaskList(QListWidget):
    """
    多开用任务列表，用于显示和管理多个任务。
    """
    task_moved_signal = Signal(int, int)

    def __init__(self, placeholder=""):
        super().__init__()
        self.placeholder = placeholder

        # 右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu) # type: ignore
        self.customContextMenuRequested.connect(self.open_menu)

        # 启用拖放内部移动
        self.setDragDropMode(QAbstractItemView.InternalMove) # type: ignore
        self.setAcceptDrops(True)
        self.setSortingEnabled(False)
        
        self.setPlaceholderText(self.placeholder)

    def setPlaceholderText(self, text):
        """
        设置列表为空时显示的占位文字。
        """
        self.placeholder = text
        
    def paintEvent(self, event):
        """
        重写 paintEvent 以在列表为空时显示占位文字。
        """
        super().paintEvent(event)
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(150, 150, 150))
            x = 10
            y = self.height() // 2
            painter.drawText(x, y, self.placeholder)

    def open_menu(self, pos: QPoint):
        """
        打开任务列表的右键菜单，包含上移、下移、移动到顶部、移动到底部、删除操作。
        """
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
            self._move_and_emit(row, row - 1)
        elif action == act_down:
            self._move_and_emit(row, row + 1)
        elif action == act_top:
            self._move_and_emit(row, 0)
        elif action == act_bottom:
            self._move_and_emit(row, count - 1)
        elif action == act_delete:
            self.delete_task_action(row)

    def _move_and_emit(self, old_row: int, new_row: int):
        """
        内部移动并发信号给外部。对从下往上移动做索引修正。
        """
        count = self.count()
        if old_row < 0 or old_row >= count:
            return
        if new_row < 0:
            new_row = 0
        if new_row > count:
            new_row = count
        if old_row == new_row:
            return

        item = self.takeItem(old_row)
        if item is None:
            return
        insert_index = new_row
        self.insertItem(insert_index, item)
        self.setCurrentItem(item)

        self.task_moved_signal.emit(old_row, new_row)

    def move_task_action(self, old_row: int, new_row: int):
        """
        移动任务
        """
        self._move_and_emit(old_row, new_row)

    def delete_task_action(self, row: int):
        """
        删除任务
        """
        item_to_delete = self.takeItem(row)
        if item_to_delete:
            del item_to_delete
        if self.count() > 0:
            if row < self.count():
                self.setCurrentRow(row)
            else:
                self.setCurrentRow(self.count() - 1)

    def clear_list(self):
        """
        清空任务列表。
        """
        self.clear()

    def set_list(self, tasks: list[str]):
        """
        设置任务列表，先清空再添加。
        """
        self.clear_list()
        for task in tasks:
            self.addItem(task)

    def get_all_items(self) -> list[str]:
        """
        获取所有任务项的文本。

        Returns:
            list[str]: 所有任务项的文本列表。
        """
        return [self.item(i).text() for i in range(self.count())]