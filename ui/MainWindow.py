import os
from typing import Iterable

from PyQt5.QtCore import Qt, pyqtSlot, QDir, QModelIndex
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from core import Moment, ModelData
from ui import DurationsListModel
from ui.layout.Ui_MainWindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        super(MainWindow, self).setupUi(self)

        self.model = DurationsListModel(ModelData(),
                                        self.tabv_intervals)
        self.tabv_intervals.setModel(self.model)

        self.lbl_file_drop.changeFile.connect(
            self.on_lbl_file_drop_change_file
        )
        self.model.dataChanged.connect(self.on_model_data_changed)
        self.model.rowsInserted.connect(self.on_model_rows_inserted)
        self.model.rowsMoved.connect(self.on_model_rows_moved)
        self.model.rowsRemoved.connect(self.on_model_rows_removed)
        self.model.modelReset.connect(self.on_model_model_reset)

        self.update_source()
        self.update_output()

    def __clear_add_interval(self):
        self.spin_interval_begin_hour.setValue(0)
        self.spin_interval_begin_mins.setValue(0)
        self.spin_interval_begin_secs.setValue(0)
        self.spin_interval_end_hour.setValue(0)
        self.spin_interval_end_mins.setValue(0)
        self.spin_interval_end_secs.setValue(0)

    @pyqtSlot()
    def on_act_new_task_triggered(self):
        self.lineedt_output_path.clear()
        self.model.setPathSrc("")
        self.model.setPathDstDir("")
        self.model.clearIntervals()
        self.__clear_add_interval()

    @pyqtSlot()
    def on_tbtn_parse_source_clicked(self):
        self.parse_source()

    @pyqtSlot()
    def on_pbtn_add_interval_clicked(self):
        begin = Moment.from_args(
            self.spin_interval_begin_hour.value(),
            self.spin_interval_begin_mins.value(),
            self.spin_interval_begin_secs.value()
        )
        end = Moment.from_args(
            self.spin_interval_end_hour.value(),
            self.spin_interval_end_mins.value(),
            self.spin_interval_end_secs.value()
        )

        if begin is not None and end is not None and begin <= end:
            self.model.addInterval(begin, end)
            self.__clear_add_interval()
            self.spin_interval_begin_hour.setFocus()
        else:
            QMessageBox.critical(None, "错误", "添加的时间段存在错误", QMessageBox.Ok)

    @pyqtSlot()
    def on_tbtn_move_up_clicked(self):
        rows = set((index.row()
                    for index in self.tabv_intervals.selectedIndexes()))
        for row in sorted(rows):
            self.model.moveInterval(row, -1)

    @pyqtSlot()
    def on_tbtn_move_down_clicked(self):
        rows = set((index.row()
                    for index in self.tabv_intervals.selectedIndexes()))
        for row in sorted(rows, reverse=True):
            self.model.moveInterval(row, 1)

    @pyqtSlot()
    def on_tbtn_remove_clicked(self):
        self.tabv_intervals.setUpdatesEnabled(False)
        rows = set((index.row()
                    for index in self.tabv_intervals.selectedIndexes()))
        for row in sorted(rows, reverse=True):
            self.model.removeRow(row)
        self.tabv_intervals.setUpdatesEnabled(True)

    @pyqtSlot()
    def on_tbtn_clear_clicked(self):
        self.tabv_intervals.setUpdatesEnabled(False)
        self.model.clearIntervals()
        self.tabv_intervals.setUpdatesEnabled(True)

    @pyqtSlot(int)
    def on_spin_interval_begin_value_changed(self):
        # begin = Moment(
        #     self.spin_interval_begin_hour.value(),
        #     self.spin_interval_begin_mins.value(),
        #     self.spin_interval_begin_secs.value()
        # )
        # end = Moment(
        #     self.spin_interval_end_hour.value(),
        #     self.spin_interval_end_mins.value(),
        #     self.spin_interval_end_secs.value()
        # )
        # if begin > end:
        #     self.spin_interval_end_hour.setValue(begin.hour)
        #     self.spin_interval_end_mins.setValue(begin.mins)
        #     self.spin_interval_end_secs.setValue(begin.secs)
        pass

    @pyqtSlot(int)
    def on_spin_interval_end_value_changed(self):
        # begin = Moment(
        #     self.spin_interval_begin_hour.value(),
        #     self.spin_interval_begin_mins.value(),
        #     self.spin_interval_begin_secs.value()
        # )
        # end = Moment(
        #     self.spin_interval_end_hour.value(),
        #     self.spin_interval_end_mins.value(),
        #     self.spin_interval_end_secs.value()
        # )
        # if begin > end:
        #     self.spin_interval_begin_hour.setValue(end.hour)
        #     self.spin_interval_begin_mins.setValue(end.mins)
        #     self.spin_interval_begin_secs.setValue(end.secs)
        pass

    @pyqtSlot(name='on_lineedt_output_path_editingFinished')
    def on_lineedt_output_path_editing_finished(self):
        self.model.setPathDstDir(self.lineedt_output_path.text())
        self.update_source()
        self.update_output()

    @pyqtSlot(str)
    def on_lbl_file_drop_change_file(self, url):
        self.model.setPathSrc(url)
        self.update_source()
        self.update_output()

    @pyqtSlot(QModelIndex, QModelIndex, 'QVector<int>')
    def on_model_data_changed(self,
                              top_left: QModelIndex,
                              bottom_right: QModelIndex,
                              roles: Iterable[int]):
        # print('on_model_data_changed((%d, %d), (%d, %d), %s)'
        #       % (top_left.row(),
        #          top_left.column(),
        #          bottom_right.row(),
        #          bottom_right.column(),
        #          repr(roles)))
        if Qt.EditRole in roles:
            self.update_source()
            self.update_output()

    @pyqtSlot()
    def on_model_model_reset(self):
        self.update_source()
        self.update_output()

    @pyqtSlot(QModelIndex, int, int)
    def on_model_rows_inserted(self,
                               parent: QModelIndex,
                               first: int, last: int):
        self.update_source()
        self.update_output()

    @pyqtSlot(QModelIndex, int, int, QModelIndex, int)
    def on_model_rows_moved(self,
                            parent: QModelIndex, start: int, end: int,
                            destination: QModelIndex, row: int):
        self.update_source()
        self.update_output()

    @pyqtSlot(QModelIndex, int, int)
    def on_model_rows_removed(self,
                              parent: QModelIndex,
                              first: int, last: int):
        self.update_source()
        self.update_output()

    def parse_source(self):
        txt = self.txtedt_source.toPlainText()
        if self.model.importFromJson(txt):
            self.statusbar.showMessage("解析源码已成功：已更新参数")
        else:
            self.statusbar.showMessage("解析源码时出错：JSON解析出错或者存在不合法的参数")

    def update_source(self):
        self.txtedt_source.setText(
            self.model.exportToJson(indent=4)
            if self.chkbox_format_source.isChecked()
            else self.model.exportToJson()
        )

    def update_output(self):
        path_src = QDir.toNativeSeparators(self.model.getPathSrc())
        path_dst_dir = QDir.toNativeSeparators(self.model.getPathDstDir())
        path_dst_base = os.path.splitext(os.path.basename(path_src))
        path_dst_base_prefix, path_dst_base_suffix = path_dst_base
        cmd = 'ffmpeg -ss %02d:%02d:%02d -t %02d:%02d:%02d ' \
              '-i %s ' \
              '-vcodec copy -acodec copy ' \
              '%s'

        self.txtbrw_output.clear()

        for index, interval in enumerate(self.model.iterIntervals()):
            begin, end = interval
            begin = Moment(begin[0], begin[1], begin[2])
            end = Moment(end[0], end[1], end[2])
            delta = end - begin
            self.txtbrw_output.append(cmd % (
                begin.hour, begin.mins, begin.secs,
                delta.hour, delta.mins, delta.secs,
                path_src,
                os.path.join(
                    path_dst_dir,
                    '%s_%d%s' % (path_dst_base_prefix,
                                 index,
                                 path_dst_base_suffix)
                )
            ))
