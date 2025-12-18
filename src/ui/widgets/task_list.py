from PySide6.QtWidgets import QListWidget, QMenu, QAbstractItemView, QListWidgetItem
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor
from ..core.logger import logger
from PySide6.QtCore import Signal

class TaskList(QListWidget):
    """
    任务列表组件 - 已适配 TaskDataModel
    """
    def __init__(self, data_model, placeholder="请从右侧选择任务添加到此处"):
        super().__init__()
        # TaskDataModel 实例
        self.data_model = data_model 
        self.placeholder = placeholder

        self.setContextMenuPolicy(Qt.CustomContextMenu) # type: ignore
        self.customContextMenuRequested.connect(self.open_menu)
        self.setDragDropMode(QAbstractItemView.InternalMove) # type: ignore
        self.setAcceptDrops(True)
        self.setSortingEnabled(False)
        self.setPlaceholderText(self.placeholder)
        
        # 连接 TaskDataModel 的信号
        self.data_model.run_list_changed.connect(self.refresh_list_from_model)
        
        self.refresh_list_from_model()

    def setPlaceholderText(self, text):
        self.placeholder = text

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(150, 150, 150))
            x = 10
            y = self.height() // 2
            painter.drawText(x, y, self.placeholder)

    def refresh_list_from_model(self):
        """
        刷新列表
        """
        self.clear()
        for task_instance in self.data_model.get_tasks():
            task_name = task_instance.get_task_name()
            item = QListWidgetItem(task_name)
            self.addItem(item)

    def open_menu(self, pos: QPoint):
        """
        打开上下文菜单
        """
        item = self.itemAt(pos)
        if not item: return
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
        if not action: return

        if action == act_up: self.move_task_action(row, row - 1)
        elif action == act_down: self.move_task_action(row, row + 1)
        elif action == act_top: self.move_task_action(row, 0)
        elif action == act_bottom: self.move_task_action(row, count - 1)
        elif action == act_delete: self.delete_task_action(row)

    def delete_task_action(self, row: int):
        """
        删除任务
        """
        self.data_model.remove_task(row) 

    def move_task_action(self, old_row: int, new_row: int):
        """
        移动任务
        """
        if old_row == new_row or new_row < 0 or new_row >= self.count():
            return
        self.data_model.move_task(old_row, new_row)

    def dropEvent(self, event):
        """
        处理任务列表的拖放事件，实现任务的内部移动。
        """
        source_row = self.currentRow()
        if source_row < 0: return
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item:
            target_row = self.row(item)
        else:
            target_row = self.count() - 1
        if target_row == source_row:
            event.ignore()
            return
        self.data_model.move_task(source_row, target_row)
        event.accept()
        
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
    
    def dropEvent(self, event):
        source_row = self.currentRow()
        
        # 执行默认的 UI 移动
        super().dropEvent(event)
        
        target_row = self.currentRow()
        
        # 通知外部数据已变更
        if source_row != target_row:
            self.task_moved_signal.emit(source_row, target_row)