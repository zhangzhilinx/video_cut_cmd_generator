import os
from typing import Iterable

from PyQt5.QtCore import Qt, pyqtSlot, QDir, QModelIndex
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QFileDialog
from pymediainfo import MediaInfo

from core import Moment, ModelData
from ui import DurationsListModel
from ui.layout.Ui_MainWindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        super(MainWindow, self).setupUi(self)

        self._model = DurationsListModel(ModelData(),
                                         self.tabv_intervals)
        self._json_path = None
        self.tabv_intervals.setModel(self._model)

        self.lbl_file_drop.changeFile.connect(
            self.on_lbl_file_drop_change_file
        )
        self._model.dataChanged.connect(self.on_model_data_changed)
        self._model.rowsInserted.connect(self.on_model_rows_inserted)
        self._model.rowsMoved.connect(self.on_model_rows_moved)
        self._model.rowsRemoved.connect(self.on_model_rows_removed)
        self._model.modelReset.connect(self.on_model_model_reset)

        self.update_source()
        self.update_output()

    def __clear_add_interval(self):
        self.spin_interval_begin_hour.setValue(0)
        self.spin_interval_begin_mins.setValue(0)
        self.spin_interval_begin_secs.setValue(0)
        self.spin_interval_end_hour.setValue(0)
        self.spin_interval_end_mins.setValue(0)
        self.spin_interval_end_secs.setValue(0)

    @pyqtSlot(name='on_tbtn_src_meta_refresh_clicked')
    def refresh_src_meta(self):
        src_path = os.path.join(self._model.src_path_dir,
                                self._model.src_filename)
        try:
            stat = os.stat(src_path)
            media_info = MediaInfo.parse(src_path)
            if media_info is not None and len(media_info.tracks):
                # Warning: Maybe track 0 is not a video track
                self.spin_src_duration.setValue(media_info.tracks[0].duration)
            size_src = stat.st_size
            self.spin_src_size.setValue(size_src)

            duration_src = self.spin_src_duration.value()
            duration_dst = 0
            for interval in self._model.iter_intervals():
                begin, end = interval
                delta = Moment.from_list(end) - Moment.from_list(begin)
                duration_dst += delta.to_secs() * 1000
            save_rate = 1.0 - duration_dst / duration_src
            save_time = Moment.from_secs((duration_src - duration_dst) // 1000)
            self.statusBar \
                .showMessage("删减时长：%02d:%02d:%02d，节约率：%.2f %%，估计可节省空间：%.2f MiB"
                             % (save_time.hour, save_time.mins, save_time.secs,
                                save_rate * 100.0,
                                (size_src * save_rate) / 1048576))
        except OSError:
            pass

    @pyqtSlot(name='on_tbtn_refresh_source_clicked')
    def update_source(self):
        self.txtbrw_source.setText(
            self._model.export_to_json(indent=4)
            if self.act_setting_format.isChecked()
            else self._model.export_to_json()
        )

    @pyqtSlot(name='on_tbtn_refresh_commands_clicked')
    def update_output(self):
        src_filename = self._model.src_filename
        src_path_dir = self._model.src_path_dir
        src_path = QDir.toNativeSeparators(
            os.path.join(src_path_dir, src_filename)
        )
        dst_path_dir = QDir.toNativeSeparators(self._model.dst_path_dir)
        dst_prefix, dst_suffix = os.path.splitext(src_filename)
        cmd = 'ffmpeg -ss %02d:%02d:%02d -t %02d:%02d:%02d ' \
              '-i %s ' \
              '-vcodec copy -acodec copy ' \
              '%s'

        self.txtbrw_output.clear()

        for index, interval in enumerate(self._model.iter_intervals()):
            begin, end = interval
            begin = Moment(begin[0], begin[1], begin[2])
            end = Moment(end[0], end[1], end[2])
            delta = end - begin
            self.txtbrw_output.append(cmd % (
                begin.hour, begin.mins, begin.secs,
                delta.hour, delta.mins, delta.secs,
                src_path,
                os.path.join(
                    dst_path_dir,
                    '%s_%d%s' % (dst_prefix,
                                 index,
                                 dst_suffix)
                )
            ))

    def open_json(self, json_path: str) -> bool:
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf8') as f:
                if self._model.import_from_json(f.read()):
                    self.ledt_src_filename.setText(self._model.src_filename)
                    self.ledt_src_path_dir.setText(self._model.src_path_dir)
                    self.ledt_dst_path_dir.setText(self._model.dst_path_dir)
                    self.txtbrw_output.clear()
                    self.txtbrw_source.clear()
                    self.__clear_add_interval()

                    self._json_path = json_path

                    self.refresh_src_meta()
                    self.update_output()
                    self.update_source()

                    return True
                else:
                    return False

    @pyqtSlot()
    def on_act_file_new_triggered(self):
        self.ledt_src_filename.clear()
        self.ledt_src_path_dir.clear()
        self.ledt_dst_path_dir.clear()
        self.spin_src_duration.setValue(0)
        self.spin_src_size.setValue(0)
        self.txtbrw_output.clear()
        self.txtbrw_source.clear()

        self._model.reset_data()
        self.__clear_add_interval()

        self._json_path = None

        self.update_output()
        self.update_source()

    @pyqtSlot()
    def on_act_file_open_triggered(self):
        json_path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="打开JSON文件",
            filter="JSON File (*.json)"
        )
        if len(json_path):
            if self.open_json(json_path):
                self.statusBar \
                    .showMessage("解析配置已成功：%s" % json_path)
            else:
                self.statusBar \
                    .showMessage("解析配置时出错：JSON解析出错或者存在不合法的参数")

    @pyqtSlot()
    def on_act_file_save_triggered(self):
        if self._json_path is None:
            self.on_act_file_save_as_triggered()
        else:
            try:
                with open(self._json_path, 'w', encoding='utf8') as f:
                    f.write(
                        self._model.export_to_json(indent=4)
                        if self.act_setting_format.isChecked()
                        else self._model.export_to_json()
                    )
                    self.statusBar \
                        .showMessage("保存成功：%s" % self._json_path)
            except IOError:
                QMessageBox.critical(
                    parent=self,
                    title="保存失败",
                    text="保存时出现了错误，请使用另存为保存"
                )

    @pyqtSlot()
    def on_act_file_save_as_triggered(self):
        json_path, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption="另存为",
            directory=os.path.join(
                self._model.src_path_dir,
                os.path.splitext(self._model.src_filename)[0]
            ),
            filter="JSON File (*.json)"
        )
        if len(json_path):
            try:
                with open(json_path, 'w', encoding='utf8') as f:
                    f.write(
                        self._model.export_to_json(indent=4)
                        if self.act_setting_format.isChecked()
                        else self._model.export_to_json()
                    )
                    self._json_path = json_path
                    self.statusBar \
                        .showMessage("另存为成功：%s" % self._json_path)
            except IOError:
                QMessageBox.critical(
                    parent=self,
                    title="保存失败",
                    text="保存时出现了错误，可能是磁盘空间不足等原因，"
                         "建议换一个合适的路径进行保存"
                )

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
            self._model.add_interval(begin, end)
            self.__clear_add_interval()
            self.spin_interval_begin_hour.setFocus()
        else:
            QMessageBox.critical(None, "错误", "添加的时间段存在错误", QMessageBox.Ok)

    @pyqtSlot()
    def on_tbtn_move_up_clicked(self):
        rows = set((index.row()
                    for index in self.tabv_intervals.selectedIndexes()))
        for row in sorted(rows):
            self._model.move_interval(row, -1)

    @pyqtSlot()
    def on_tbtn_move_down_clicked(self):
        rows = set((index.row()
                    for index in self.tabv_intervals.selectedIndexes()))
        for row in sorted(rows, reverse=True):
            self._model.move_interval(row, 1)

    @pyqtSlot()
    def on_tbtn_remove_clicked(self):
        self.tabv_intervals.setUpdatesEnabled(False)
        rows = set((index.row()
                    for index in self.tabv_intervals.selectedIndexes()))
        for row in sorted(rows, reverse=True):
            self._model.removeRow(row)
        self.tabv_intervals.setUpdatesEnabled(True)

    @pyqtSlot()
    def on_tbtn_clear_clicked(self):
        self.tabv_intervals.setUpdatesEnabled(False)
        self._model.clear_intervals()
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

    @pyqtSlot(str)
    def on_lbl_file_drop_change_file(self, url):
        path_dir, filename = os.path.split(url)
        if os.path.splitext(filename)[-1] == '.json':
            if self.open_json(url):
                self.statusBar \
                    .showMessage("解析配置已成功：%s" % url)
            else:
                self.statusBar \
                    .showMessage("解析配置时出错：JSON解析出错或者存在不合法的参数")
        else:
            self.ledt_src_path_dir.setText(path_dir)
            self.ledt_src_filename.setText(filename)
            self.refresh_src_meta()
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

    @pyqtSlot(str, name='on_ledt_src_filename_textChanged')
    def on_ledt_src_filename_text_changed(self, text: str):
        self._model.src_filename = text

    @pyqtSlot(str, name='on_ledt_src_path_dir_textChanged')
    def on_ledt_src_path_dir_text_changed(self, text: str):
        self._model.src_path_dir = text

    @pyqtSlot(str, name='on_ledt_dst_path_dir_textChanged')
    def on_ledt_dst_path_dir_text_changed(self, text: str):
        self._model.dst_path_dir = text
