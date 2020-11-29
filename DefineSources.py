from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from fontTools.designspaceLib import SourceDescriptor
from PyQt5.QtCore import Qt, pyqtSlot, QPoint, pyqtSignal
from PyQt5 import QtGui
import re, os
from QDesignSpace import DesignSpaceVisualizer
import defcon


class DragDropArea(QPushButton):
    gotFiles = pyqtSignal()
    def __init__(self, parent):
        super(DragDropArea, self).__init__()
        self.parent = parent
        self.setText("Drop a UFO file or click to open")
        self.setStyleSheet("background-color: #C8E6C9")
        self.setAcceptDrops(True)
        self.clicked.connect(self.buttonClicked)
        self.lastFiles = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and self.isAllFonts(event.mimeData()):
            self.setStyleSheet("background-color: #FFF9C4")
            event.accept()
        else:
            self.setStyleSheet("background-color: #B00020 ")
            event.accept()

    def buttonClicked(self):
        ufo = QFileDialog.getOpenFileNames(
            self, "Open UFO file", filter="UFO file (*.ufo)"
        )
        if not ufo:
            return
        self.lastFiles = [ x for x in ufo if x != "UFO file (*.ufo)" ]
        self.gotFiles.emit()

    def isAllFonts(self, mime):
        for url in mime.urls():
            path = url.toLocalFile()
            if not re.match(r".*\.ufo/?$", path):
                return False
        return True

    def dragLeaveEvent(self, event):
        self.setStyleSheet("background-color: #C8E6C9")

    def dropEvent(self, event):
        self.setStyleSheet("background-color: #C8E6C9")
        if not self.isAllFonts(event.mimeData()):
          return
        self.lastFiles = [[url.toLocalFile()[:-1] for url in event.mimeData().urls()]]
        event.accept()
        self.gotFiles.emit()


class DefineSources(MyWizardPage):
  disableEnter = True

  def __init__(self, parent=None):
    super(QWizardPage, self).__init__(parent)
    self.parent = parent
    self.designspace = parent.designspace

    self.setTitle("Let's define our sources!")
    self.splitter = QSplitter()
    self.layout = QHBoxLayout()
    self.layout.addWidget(self.splitter)
    # self.layout.addWidget(QLabel("Hello"))
    self.setLayout(self.layout)
    self.splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.left = QWidget()
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

    self.splitter.addWidget(self.left)

    self.right = DesignSpaceVisualizer(self.designspace)
    self.splitter.addWidget(self.right)


  def initializePage(self):
    self.designspace = self.parent.designspace
    self.right.setParent(None)
    self.right.deleteLater()
    if len(self.designspace.sources):
      # Check the source files exist!
      missing = []
      found = []
      for source in self.designspace.sources:
        if os.path.exists(source.path):
          found.append(source)
        else:
          missing.append(source)
        self.setNames(source)
      self.designspace.sources = found
      if missing:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Some source files were not found; they have been skipped")
        msg.setInformativeText("\n".join([x.filename for x in missing]))
        msg.setWindowTitle("Missing sources")
        msg.exec_()
      self.right = DesignSpaceVisualizer(self.designspace, draw_glyph="e")
    else:
      self.right = DesignSpaceVisualizer(self.designspace)
    self.splitter.addWidget(self.right)
    width = qApp.desktop().availableGeometry(self).width()
    self.splitter.setSizes([width * 2/3, width * 1/3])

    self.setupSources()
    self.completeChanged.emit()

  def setNames(self, source):
    if source.familyName and source.styleName:
      return
    self.designspace.loadSourceFonts(defcon.Font)
    if not source.familyName:
      source.familyName = source.font.info.familyName
    if not source.styleName:
      source.styleName = source.font.info.styleName

  @pyqtSlot()
  def addSource(self):
    self.parent.dirty = True
    axis_tags = [ x.tag for x in self.designspace.axes ]
    for file in self.sender().lastFiles[0]:
      source = SourceDescriptor(path=file, filename = os.path.basename(file))
      source.location = {}

      for t in axis_tags:
        m = re.search("-"+t+r"-?(\d+)", source.filename)
        if m:
          source.location[t] = int(m[1])
      self.designspace.sources.append(source)
      self.setNames(source)
    self.initializePage()
    self.right.refresh()

  @pyqtSlot()
  def removeRow(self):
    del self.designspace.sources[self.sender().ix]
    self.parent.dirty = True
    self.initializePage()

  @pyqtSlot()
  def locationChanged(self):
    self.parent.dirty = True
    loc = self.sender()
    source = loc.source
    if not source.location:
      source.location = {}
    source.location[loc.name] = loc.value()
    self.right.refresh()

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
        name = ax.name
        loc = QSpinBox()
        loc.tag = ax.tag
        loc.name = ax.name
        loc.source = source
        loc.setMinimum(ax.minimum)
        loc.setMaximum(ax.maximum)
        if name in source.location:
          loc.setValue(source.location[name])
        else:
          loc.setValue(ax.default)
        loc.valueChanged.connect(self.locationChanged)
        group_layout.addWidget(loc)

      removeButton = QPushButton("Remove")
      removeButton.ix = ix
      group_layout.addWidget(removeButton)
      removeButton.clicked.connect(self.removeRow)
      self.sourcesLayout.addWidget(group)


  def isComplete(self):
    if not self.designspace.sources:
      return False
    return True
    # Any other checks here?

