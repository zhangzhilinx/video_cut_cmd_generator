import re

from PyQt5.QtCore import QAbstractTableModel, QModelIndex
from PyQt5.QtCore import Qt, QObject, QVariant

from core import ModelData, Moment


class DurationsListModel(QAbstractTableModel):
    __regexp_moment = re.compile(r'([0-9]+):([0-5]?[0-9]):([0-5]?[0-9])')

    def __init__(self, modelData: ModelData, parent: QObject = None):
        super(DurationsListModel, self).__init__(parent)
        self._model_data = modelData

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return self._model_data.intervals_size()

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return 2

    def headerData(self, section: int, orientation: int, role: int = None) -> QVariant:
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            if section == 0:
                return QVariant("Begin")
            elif section == 1:
                return QVariant("End")
            else:
                return QVariant()
        return super(DurationsListModel, self) \
            .headerData(section, orientation, role)

    def data(self, index: QModelIndex, role=None) -> QVariant:
        if not index.isValid():
            return QVariant()
        if 0 <= index.row() < self._model_data.intervals_size():
            if role == Qt.DisplayRole:
                row, col = index.row(), index.column()
                if col == 0 or col == 1:
                    t = self._model_data.get_interval_unwrap(row, col)
                    return QVariant('%02d:%02d:%02d' % (t[0], t[1], t[2]))
        return QVariant()

    def setData(self, index: QModelIndex, value: QVariant, role: int = None) -> bool:
        result = True
        if index.isValid() and role == Qt.EditRole:
            row, col = index.row(), index.column()
            if 0 <= row < self._model_data.intervals_size():
                if col == 0 or col == 1:
                    match_res = self.__regexp_moment.match(str(value))
                    if match_res:
                        hour, mins, secs = [int(i) for i in match_res.groups()]
                        interval = self._model_data.get_interval_unwrap(row)
                        if Moment.validate(hour, mins, secs):
                            if col == 0:
                                if [hour, mins, secs] > interval[1]:
                                    result = False
                                else:
                                    self._model_data \
                                        .set_interval(row,
                                                      begin=Moment(hour,
                                                                   mins,
                                                                   secs))
                            elif col == 1:
                                if [hour, mins, secs] < interval[0]:
                                    result = False
                                else:
                                    self._model_data \
                                        .set_interval(row,
                                                      end=Moment(hour,
                                                                 mins,
                                                                 secs))
                            else:
                                return False
                    else:
                        result = False
                else:
                    result = False
                if result:
                    self.dataChanged.emit(index, index, [role])
            else:
                result = False
        return result

    def flags(self, index: QModelIndex) -> int:
        if not index.isValid():
            return Qt.ItemIsEnabled
        return super(DurationsListModel, self).flags(index) \
               | Qt.ItemIsEditable

    def insertRow(self, row: int, parent: QModelIndex = None, *args, **kwargs) -> bool:
        return self.insertRows(row, 1, parent, *args, **kwargs)

    def insertRows(self, row: int, count: int, parent: QModelIndex = None, *args, **kwargs) -> bool:
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        for i in range(count):
            self._model_data.insert_interval(row + i,
                                             Moment(0, 0, 0),
                                             Moment(0, 0, 0))
        self.endInsertRows()
        return True

    def removeRow(self, row: int, parent: QModelIndex = None, *args, **kwargs) -> bool:
        return self.removeRows(row, 1, parent, *args, **kwargs)

    def removeRows(self, row: int, count: int, parent: QModelIndex = None, *args, **kwargs) -> bool:
        result = True
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        intervals_size = self._model_data.intervals_size()
        if 0 <= row < intervals_size \
                and count > 0 and row + count <= intervals_size:
            for i in range(row + count - 1, row, -1):
                self._model_data.del_interval(i)
        else:
            result = False
        self.endRemoveRows()
        return result

    def addInterval(self, begin: Moment, end: Moment):
        if begin <= end:
            index = self.rowCount()
            self.beginInsertRows(QModelIndex(), index, index)
            self._model_data.add_interval(begin, end)
            self.endInsertRows()

    def moveInterval(self, row: int, offset: int):
        row_src, row_dst = row, row + offset
        row_cnt = self.rowCount()
        if offset != 0 \
                and 0 <= row_src < row_cnt \
                and 0 <= row_dst < row_cnt:
            self.beginMoveRows(QModelIndex(),
                               row_src, row_src,
                               QModelIndex(),
                               row_dst if offset < 0 else row_dst + 1)
            self._model_data.move_interval(row, offset)
            self.endMoveRows()

    def clearIntervals(self):
        self.beginRemoveRows(QModelIndex(), 0, self.rowCount() - 1)
        self._model_data.clear_intervals()
        self.endRemoveRows()

    def iterIntervals(self):
        return self._model_data.intervals_iter()

    def getPathSrc(self) -> str:
        return self._model_data.path_src

    def setPathSrc(self, value: str):
        self._model_data.path_src = value

    def getPathDstDir(self) -> str:
        return self._model_data.path_dst_dir

    def setPathDstDir(self, value: str):
        self._model_data.path_dst_dir = value

    def importFromJson(self, strJson: str) -> bool:
        model_data = ModelData.from_json(strJson)
        if model_data is not None:
            self.beginResetModel()
            self._model_data = model_data
            self.endResetModel()
            return True
        else:
            return False

    def exportToJson(self, *args, **kwargs) -> str:
        return self._model_data.to_json(*args, **kwargs)
