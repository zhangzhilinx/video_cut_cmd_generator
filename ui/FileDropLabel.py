from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel


class FileDropLabel(QLabel):
    changeFile = pyqtSignal(str)

    def __init__(self, *__args):
        super().__init__(*__args)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("text/uri-list"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if len(urls):
            self.changeFile.emit(urls[0].toLocalFile())
