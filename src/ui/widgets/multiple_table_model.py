from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QTableView
from PySide6.QtCore import Signal

class MultipleTableModel(QAbstractTableModel):
    """
    多开任务表格模型
    """

    data_changed_signal = Signal() # 数据改变信号

    def __init__(self, data: list[dict], parent=None):
        """
        初始化多开任务表格模型.

        Args:
            data: 多开任务数据列表，每个元素是一个字典，包含任务信息
        """
        super().__init__(parent)
        self._data = data
        
        # 定义列标题，顺序对应数据字典中的键
        self._headers = ["任务名", "窗口句柄", "任务状态", "当前运行", "进度"]
        self._keys = ["name", "handle", "status", "current_run", "progress"]

    def rowCount(self, parent=QModelIndex()):
        """
        返回行数（即任务的数量）.

        Returns:
            int: 任务数量
        """
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        """
        返回列数（即数据字段的数量）.

        Returns:
            int: 数据字段数量
        """
        return len(self._headers)
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """
        返回表格中指定索引位置的数据.

        Args:
            index: 要查询数据的索引位置
            role: 数据角色，默认为显示角色

        Returns:
            Any: 对应索引位置的数据值
        """
        if not index.isValid():
            return None
            
        row = index.row()
        col = index.column()
        
        # 提供显示数据
        if role == Qt.ItemDataRole.DisplayRole:
            # 根据列索引获取对应的键名
            key = self._keys[col]
            # 返回对应行（任务）和列（字段）的值
            return str(self._data[row][key])
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        """
        返回表格的行或列标题.

        Args:
            section: 要查询标题的行或列索引
            orientation: 标题方向，水平或垂直
            role: 数据角色，默认为显示角色

        Returns:
            Any: 对应索引位置的标题值
        """
        # 设置行或列的标题
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                # 设置列标题
                return self._headers[section]
            if orientation == Qt.Orientation.Vertical:
                # 设置行标题
                return section + 1
        return None
    
    def flags(self, index: QModelIndex):
        """
        返回表格中指定索引位置的项标志.

        Args:
            index: 要查询项标志的索引位置

        Returns:
            Qt.ItemFlag: 对应索引位置的项标志
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        # 默认返回可启用和可选中的标志
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    
    # TaskModel.setData 方法修改后的版本

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole):
        """
        设置表格中指定索引位置的数据.

        Args:
            index: 要设置数据的索引位置
            value: 要设置的新值
            role: 数据角色，默认为编辑角色

        Returns:
            bool: 设置成功返回True，失败返回False
        """
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
            
        row = index.row()
        col = index.column()
        try:
            key = self._keys[col]
        except IndexError:
            return False
        # 确保新值是字符串，以便存储
        new_value = str(value) 
        if self._data[row][key] != new_value:
            self._data[row][key] = new_value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            return True
                
        return False 
    
    def update_data(self, task_index: int, column_index: int, new_value):
        """
        更新指定任务（行）的指定字段（列）的值。

        Args:
            task_index: 任务在列表中的行索引。
            column_index: 要修改的列索引 (0=任务名, 1=句柄, 2=状态)。
            new_value: 要设置的新值。

        Returns:
            bool: 成功返回 True，失败返回 False。
        """
        # 检查行索引和列索引是否有效
        if 0 <= task_index < len(self._data) and 0 <= column_index < self.columnCount():

            target_index = self.index(task_index, column_index)

            self.data_changed_signal.emit()
            return self.setData(target_index, new_value, Qt.ItemDataRole.EditRole)
            
        return False
    
    def add_data(self, task_data: dict):
        """
        向列表末尾添加一个新任务。

        Args:
            task_data: 包含新任务数据的字典，例如: 
                        {"name": "新任务", "handle": 0, "status": "Waiting"}
        """
        row = self.rowCount()

        self.beginInsertRows(QModelIndex(), row, row)

        self._data.append(task_data)

        self.endInsertRows()
        
        
        self.data_changed_signal.emit()
        return True
    
    def remove_data(self, row: int):
        """
        删除指定行索引处的任务。

        Args:
            row: 要删除任务的行索引。
        """
        
        # 1. 检查索引是否有效
        if row < 0 or row >= self.rowCount():
            return False
            
        self.beginRemoveRows(QModelIndex(), row, row)
        
        del self._data[row]
        
        self.endRemoveRows()
        
        self.data_changed_signal.emit()
        return True
    
    def get_data(self, row_index: int) -> dict | None:
        """
        根据行索引返回该任务的原始数据字典。

        Args:
            row_index: 任务在列表中的行索引。

        Returns:
            dict | None: 对应索引位置的任务数据字典，如果索引无效则返回None。
        """
        if 0 <= row_index < len(self._data):
            # 返回内部存储的字典数据
            return self._data[row_index]
        return None
    
    def get_selected_row_index(self, table_view: QTableView) -> int | None:
        """
        获取当前 QTableView 中选中的行索引 (row number)。

        Args:
            table_view: 要查询选中行的 QTableView 实例。

        Returns:
            int | None: 选中的行索引 (从0开始)，如果未选中或无效则返回 None。
        """
        # 1. 获取选择模型
        selection_model = table_view.selectionModel()
        
        if selection_model is None:
            return None

        selected_indexes: list[QModelIndex] = selection_model.selectedRows()

        if selected_indexes:
            return selected_indexes[0].row()
        else:
            return None
        
    def clear_data(self):
        """
        清空所有任务数据。
        """
        self.beginRemoveRows(QModelIndex(), 0, self.rowCount() - 1)
        
        self._data.clear()
        
        self.endRemoveRows()
        
        self.data_changed_signal.emit()

    def find_index_by_handle(self, handle: int) -> QModelIndex | None:
        """
        根据句柄查找任务在列表中的索引。

        Args:
            handle: 要查找的任务句柄。

        Returns:
            QModelIndex | None: 对应句柄的任务索引，如果未找到则返回 None。
        """
        for index, task in enumerate(self._data):
            if task["handle"] == handle:
                return self.index(index, 0)
        return None

    def find_index_by_handle_int(self, handle: int) -> int | None:
        """
        根据句柄查找任务在列表中的索引 (整数形式)。

        Args:
            handle: 要查找的任务句柄。

        Returns:
            int | None: 对应句柄的任务索引 (从0开始)，如果未找到则返回 None。
        """
        for index, task in enumerate(self._data):
            if task["handle"] == handle:
                return index
        return None