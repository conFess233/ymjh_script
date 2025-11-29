from PySide6.QtWidgets import QListWidget, QMenu, QAbstractItemView, QListWidgetItem
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor
from ..core.logger import logger

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
    def dropEvent(self, event):
        """
        覆盖 dropEvent，允许 QListWidget 移动 UI 元素，然后同步到 Model。
        通过在 super().dropEvent() 之前/之后使用 Model.blockSignals() 来解决冲突。
        """
        old_row = self.currentRow()
    
        super().dropEvent(event)
        
        new_row = self.row(self.currentItem())
        
        # 2. 如果 UI 确实发生了移动，则同步 Model。
        if old_row != new_row and old_row != -1:
            # 在更新 Model 时，临时阻止 Model 发送 run_list_changed 信号。
            was_blocked = self.task_model.blockSignals(True)
            try:
                # 更新 Model 的内部数据顺序
                self.task_model.move_task(old_row, new_row)
                
                item_text = self.item(new_row).text() if self.item(new_row) else "Unknown Task"
                logger.log(f"任务 {item_text} 通过拖放移动到 {new_row}")
            finally:
                # 恢复信号发送状态
                self.task_model.blockSignals(was_blocked)
        
        event.accept()

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