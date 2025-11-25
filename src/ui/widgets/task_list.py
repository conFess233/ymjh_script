from PySide6.QtWidgets import QListWidget, QMenu, QAbstractItemView, QListWidgetItem
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor
from ..core.logger import logger

class TaskList(QListWidget):
    """
    任务列表组件，支持右键菜单、拖放排序，并与 TaskModel 同步。
    """
    def __init__(self, task_model, placeholder="请从右侧选择任务添加到此处"):
        # 1. ⚡ 关键改进：保存 TaskModel 引用
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
    
    # ------------------ 2. 核心同步方法 ------------------

    def refresh_list_from_model(self):
        """
        根据 TaskModel 中的 _run_list 刷新 UI 列表。
        
        注意：Model 中存储的是任务实例 (Task Instance)，UI 中存储的是任务名称 (Task Name)。
        """
        # 清空现有列表
        self.clear()
        
        # 从 Model 中获取任务实例，并添加到 UI 列表中
        for task_instance in self.task_model.get_run_list():
            task_name = task_instance.get_task_name() # 假设任务实例有 get_task_name()
            # 💡 确保添加到 UI 列表的是任务名称
            item = QListWidgetItem(task_name)
            self.addItem(item)
            

    # ------------------ 3. 右键菜单操作同步 ------------------

    def open_menu(self, pos: QPoint):
        item = self.itemAt(pos)
        if not item:
            return

        row = self.row(item)
        count = self.count()

        # ... (创建菜单和执行菜单操作的代码保持不变)
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

        # ⚡ 关键改进：将 UI 操作映射到 Model 的方法
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
        # 1. 通知 Model 移除任务
        self.task_model.remove_task_by_index(row) 
        # 2. UI 刷新：由于 TaskModel 会发出 run_list_changed 信号，我们只需在 refresh_list_from_model 中处理。
        #    但为了日志和即时性，直接 takeItem 并记录日志更直观：
        self.refresh_list_from_model

    def move_task_action(self, old_row: int, new_row: int):
        """
        ⚡ 关键修复：移动任务，仅通知 Model。UI 刷新由 Model 信号触发。
        """
        if old_row == new_row or new_row < 0 or new_row >= self.count():
            return
        
        # 仅通知 Model
        self.task_model.move_task(old_row, new_row)
        
        item_text = self.item(old_row).text() if self.item(old_row) else "Unknown Task"


    # ------------------ 4. 拖放同步 (最关键) ------------------

    def dropEvent(self, event):
        """
        覆盖 dropEvent，允许 QListWidget 移动 UI 元素，然后同步到 Model。
        通过在 super().dropEvent() 之前/之后使用 Model.blockSignals() 来解决冲突。
        """
        old_row = self.currentRow()
        
        # 1. 让 QListWidget 完成 UI 移动，同时确保 Model 不触发刷新
        # QListWidget 的 drag/drop 操作会自动处理 UI 移动
        # 因此，我们不应该在这里阻塞 Model 的信号，因为 super().dropEvent() 不会触发 run_list_changed。
        # 
        # 尝试直接调用父类 dropEvent，让它移动 UI：
        super().dropEvent(event)
        
        new_row = self.row(self.currentItem())
        
        # 2. 如果 UI 确实发生了移动，则同步 Model。
        if old_row != new_row and old_row != -1:
            # ⚡ 关键修复：在更新 Model 时，临时阻止 Model 发送 run_list_changed 信号。
            # 否则 Model 信号会再次触发 refresh_list_from_model，重置 UI。
            
            # 注意：这里我们假设 Model 也有 blockSignals 方法（通常 Model 会继承 QObject）
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

    # ------------------ 5. 辅助方法，简化为调用 move_task_action ------------------

    def move_item_up(self, row):
        if row <= 0:
            return
        self.move_task_action(row, row - 1)

    def move_item_down(self, row):
        if row >= self.count() - 1:
            return
        self.move_task_action(row, row + 1)

    def move_item_to(self, old_row, new_row):
        """这个方法现在应该统一调用 move_task_action"""
        self.move_task_action(old_row, new_row)