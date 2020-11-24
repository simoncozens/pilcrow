from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from fontTools.designspaceLib import AxisDescriptor
from PyQt5.QtCore import Qt, pyqtSlot, QPoint
from PyQt5 import QtGui
import re


class DragDropArea(QPushButton):
    def __init__(self, parent):
        super(DragDropArea, self).__init__()
        self.parent = parent
        self.setText("Drop a font here or click to open")
        self.setStyleSheet("border: 1px solid green")
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        print(event.mimeData().urls())
        if event.mimeData().hasUrls() and self.isAllFonts(event.mimeData()):
            self.setStyleSheet("border: 1px solid yellow")
            event.accept()
        else:
            self.setStyleSheet("border: 1px solid red ")
            event.ignore()

    def isAllFonts(self, mime):
        for url in mime.urls():
            path = url.toLocalFile()
            if not re.match(r".*\.(ufo/?|otf|ttf|ttc|otc)$", path):
                return False
        return True

    def dragLeaveEvent(self, event):
        self.setStyleSheet("border: 1px solid green")

    def dropEvent(self, event):
        self.setStyleSheet("border: 1px solid green")
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.paths = paths
        event.accept()


class DefineSources(MyWizardPage):
  def __init__(self, parent=None):
    super(QWizardPage, self).__init__(parent)
    self.setTitle("Let's define our sources!")
    self.layout = QVBoxLayout()
    self.setLayout(self.layout)
    self.pilcrow = parent
    self.droparea = DragDropArea(self)
    self.layout.addWidget(self.droparea)
