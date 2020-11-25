from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from fontTools.designspaceLib import AxisDescriptor
from PyQt5.QtCore import Qt, pyqtSlot, QPoint
from PyQt5 import QtGui
from fontTools.varLib.interpolatable import test
from fontTools.ufoLib import UFOReader
from os.path import basename, dirname, commonpath


class CheckAndSave(MyWizardPage):
  def __init__(self, parent=None):
    super(QWizardPage, self).__init__(parent)
    self.setTitle("Checking it's OK...")
    self.layout = QVBoxLayout()
    self.setLayout(self.layout)
    self.parent = parent
    self.problems = {}

  def initializePage(self):
    self.clearLayout()
    self.designspace = self.parent.designspace
    print(self.designspace.sources)
    fonts = [ UFOReader(x.path) for x in self.designspace.sources ]
    print(fonts)
    names = [basename(x.filename).rsplit(".", 1)[0] for x in self.designspace.sources]
    print(names)
    glyphsets = [font.getGlyphSet() for font in fonts]
    self.problems = test(glyphsets, names=names)
    self.cleanProblems()
    if not self.problems:
      self.layout.addWidget(QLabel("Everything looks good! Let's save it now..."))
      savebutton = QPushButton("Save")
      savebutton.clicked.connect(self.saveDesignspace)
      self.layout.addWidget(savebutton)

    else:
      self.sourcesScroll = QScrollArea()
      self.problemsWidget = QTreeWidget()
      for k in self.problems.keys():
        glyphItem = QTreeWidgetItem(["Glyph %s" % k])
        self.problemsWidget.addTopLevelItem(glyphItem)
        for v in self.problems[k]:
          problemItem = QTreeWidgetItem([str(v)]) #  for now
          glyphItem.addChild(problemItem)
      self.sourcesScroll.setWidget(self.problemsWidget)
      self.sourcesScroll.setWidgetResizable(True)
      self.layout.addWidget(self.sourcesScroll)

  def saveDesignspace(self):
      filename = QFileDialog.getSaveFileName(
        self, "Save File",
        directory = commonpath([dirname(x.filename) for x in self.designspace.sources]),
        filter="Designspace files (*.designspace)"
      )
      if not filename:
        return
      self.designspace.write(filename[0])
      self.parent.designspace_file = filename[0]
      self.completeChanged.emit()

  def isComplete(self):
    return not self.problems and self.parent.designspace_file

  def cleanProblems(self):
    # We don't care about high_cost.
    keys = list(self.problems.keys())
    for k in keys: # We do this malarkey because we can't alter an OrderDict while iterating
      v = self.problems[k]
      v = [x for x in v if x["type"] != "high_cost"]
      if not v:
        del self.problems[k]
      else:
        self.problems[k] = v
