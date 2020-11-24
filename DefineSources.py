from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from fontTools.designspaceLib import SourceDescriptor
from PyQt5.QtCore import Qt, pyqtSlot, QPoint, pyqtSignal
from PyQt5 import QtGui
import re, os
from QDesignSpace import DesignSpaceVisualizer


class DragDropArea(QPushButton):
    gotFiles = pyqtSignal()
    def __init__(self, parent):
        super(DragDropArea, self).__init__()
        self.parent = parent
        self.setText("Drop a font here or click to open")
        self.setStyleSheet("border: 1px solid green")
        self.setAcceptDrops(True)
        self.clicked.connect(self.buttonClicked)
        self.lastFiles = None

    def dragEnterEvent(self, event):
        print(event.mimeData().urls())
        if event.mimeData().hasUrls() and self.isAllFonts(event.mimeData()):
            self.setStyleSheet("border: 1px solid yellow")
            event.accept()
        else:
            self.setStyleSheet("border: 1px solid red ")
            event.ignore()

    def buttonClicked(self):
        ufo = QFileDialog.getOpenFileNames(
            self, "Open font file", filter="Font file (*.ufo)"
        )
        if not ufo:
            return
        self.lastFiles = [ x for x in ufo if x != "Font file (*.ufo)" ]
        self.gotFiles.emit()

    def isAllFonts(self, mime):
        for url in mime.urls():
            path = url.toLocalFile()
            if not re.match(r".*\.ufo/?$", path):
                return False
        return True

    def dragLeaveEvent(self, event):
        self.setStyleSheet("border: 1px solid green")

    def dropEvent(self, event):
        self.setStyleSheet("border: 1px solid green")
        self.lastFiles = [url.toLocalFile() for url in event.mimeData().urls()]
        event.accept()
        self.gotFiles.emit()


class DefineSources(MyWizardPage):
  def __init__(self, parent=None):
    super(QWizardPage, self).__init__(parent)
    self.designspace = parent.designspace

    self.setTitle("Let's define our sources!")
    self.layout = QHBoxLayout()
    self.setLayout(self.layout)

  def initializePage(self):
    self.clearLayout()
    self.left = QWidget()
    if len(self.designspace.sources):
      self.right = DesignSpaceVisualizer(self.designspace, draw_glyph="e")
    else:
      self.right = DesignSpaceVisualizer(self.designspace)
    self.layout.addWidget(self.left)
    self.layout.addWidget(self.right)

    self.left_layout = QVBoxLayout()
    self.left.setLayout(self.left_layout)

    self.droparea = DragDropArea(self.left)
    self.left_layout.addWidget(self.droparea)
    self.droparea.gotFiles.connect(self.addSource)

    self.sourcesScroll = QScrollArea()
    self.sourcesWidget = QWidget()
    self.sourcesScroll.setWidget(self.sourcesWidget)
    self.sourcesScroll.setWidgetResizable(True)
    self.sourcesLayout = QVBoxLayout()
    self.sourcesWidget.setLayout(self.sourcesLayout)
    self.left_layout.addWidget(self.sourcesScroll)
    self.setupSources()
    self.completeChanged.emit()

  @pyqtSlot()
  def addSource(self):
    axis_tags = [ x.tag for x in self.designspace.axes ]
    print(self.sender().lastFiles)
    for file in self.sender().lastFiles[0]:
      source = SourceDescriptor(path=file, filename = os.path.basename(file))
      source.location = {}

      for t in axis_tags:
        m = re.search("-"+t+r"-?(\d+)", source.filename)
        if m:
          source.location[t] = int(m[1])
      self.designspace.sources.append(source)
    self.initializePage()

  @pyqtSlot()
  def removeRow(self):
    del self.designspace.sources[self.sender().ix]
    self.initializePage()

  def setupSources(self):
    self._clearLayout(self.sourcesLayout)
    headergroup = QWidget()
    headergroup_layout = QHBoxLayout()
    headergroup.setLayout(headergroup_layout)
    headergroup_layout.addWidget(QLabel("Source"))
    for ax in self.designspace.axes:
      headergroup_layout.addWidget(QLabel(ax.name))
    headergroup_layout.addWidget(QLabel("Remove"))
    self.sourcesLayout.addWidget(headergroup)

    for ix,source in enumerate(self.designspace.sources):
      if not source.location:
        source.location = {}
      group = QWidget()
      group.source = source
      group_layout = QHBoxLayout()
      group.setLayout(group_layout)

      group.filename = QLabel()
      if source.filename:
        group.filename.setText(source.filename)
      group.filename.setWordWrap(True)
      group_layout.addWidget(group.filename)

      for ax in self.designspace.axes:
        tag = ax.tag
        loc = QSpinBox()
        loc.tag = ax.tag
        loc.source = source
        loc.setMinimum(ax.minimum)
        loc.setMaximum(ax.maximum)
        if tag in source.location:
          loc.setValue(source.location[tag])
        group_layout.addWidget(loc)

      removeButton = QPushButton("Remove")
      removeButton.ix = ix
      group_layout.addWidget(removeButton)
      removeButton.clicked.connect(self.removeRow)
      self.sourcesLayout.addWidget(group)
