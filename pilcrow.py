import sys
from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from pyqt5_material import apply_stylesheet
from DefineAxes import DefineAxes
from DefineSources import DefineSources
from CheckAndSave import CheckAndSave
from fontTools.designspaceLib import DesignSpaceDocument
from BuildFont import BuildFont
from PyQt5.QtCore import Qt, QSettings, QStandardPaths
import os

from enum import IntEnum
class PageId(IntEnum):
  FIRST_PAGE = 1
  BUILD_FONT = 10
  DEFINE_AXES = 2
  DEFINE_SOURCES = 3
  CHECK_AND_SAVE = 4

# create the application and the main window

import qcrash.api as qcrash

app = QApplication(sys.argv)
app.setApplicationName("Pilcrow")
app.setOrganizationDomain("corvelsoftware.co.uk")
# app.setOrganizationName("Corvel Software")

email = qcrash.backends.EmailBackend('simon@simon-cozens.org', 'pilcrow')
github = qcrash.backends.GithubBackend('simoncozens', 'pilcrow')
qcrash.install_backend(github)
qcrash.install_backend(email)
qcrash.install_except_hook()

apply_stylesheet(app, theme='light_blue.xml')

class FirstPage(MyWizardPage):
  def __init__(self, parent=None):
    super(QWizardPage, self).__init__(parent)
    self.parent = parent
    self.setTitle("Let's make a variable font!")
    label = QLabel("Do you have a designspace file already?")
    label.setWordWrap(True)
    layout = QVBoxLayout()
    layout.addWidget(label)
    self.got_designspace_no = QRadioButton("No, I need to make one")
    self.got_designspace_no.clicked.connect(lambda :self.completeChanged.emit())
    self.got_designspace_edit = QRadioButton("Yes, but I'd like to edit it")
    self.got_designspace_edit.clicked.connect(self.openOne)
    self.got_designspace_yes = QRadioButton("Yes, I just need to build the font")
    self.got_designspace_yes.clicked.connect(self.openOne)
    layout.addWidget(self.got_designspace_no)
    layout.addWidget(self.got_designspace_edit)
    layout.addWidget(self.got_designspace_yes)
    self.setLayout(layout)

  def openOne(self):

    filename = QFileDialog.getOpenFileName(
      self, "Open designspace", filter="Designspace file (*.designspace)",
      directory = self.parent.settings.value("lastdirectory", None)
    )
    if filename and filename[0]:
      self.parent.settings.setValue('lastdirectory', os.path.dirname(filename[0]))
      self.parent.designspace_file = filename[0]
      self.parent.designspace = DesignSpaceDocument.fromfile(filename[0])
      print(self.parent.designspace)
    self.completeChanged.emit()


  def isComplete(self):
    if self.got_designspace_no.isChecked():
      return True
    if not self.got_designspace_yes.isChecked() and not self.got_designspace_edit.isChecked():
      return False
    if not self.parent.designspace:
      return False
    return True

  def nextId(self):
    if self.got_designspace_yes.isChecked():
      return PageId.BUILD_FONT
    else:
      return PageId.DEFINE_AXES


class Pilcrow(QWizard):
  def __init__(self, parent=None):
    super(Pilcrow, self).__init__(parent)
    self.settings = QSettings()
    geometry = self.settings.value('mainwindowgeometry', '')
    if geometry:
        self.restoreGeometry(geometry)
    self.startId = PageId.FIRST_PAGE
    self.designspace = DesignSpaceDocument()
    self.designspace_file = None
    self.setPage(PageId.FIRST_PAGE, FirstPage(self))
    self.setPage(PageId.DEFINE_AXES, DefineAxes(self))
    self.setPage(PageId.DEFINE_SOURCES, DefineSources(self))
    self.setPage(PageId.CHECK_AND_SAVE, CheckAndSave(self))
    self.setPage(PageId.BUILD_FONT, BuildFont(self))
    self.setWindowTitle("Pilcrow")
    self.resize(640,480)
    self.resetButtons()
    self.button(QWizard.BackButton).clicked.connect(self.resetButtons)
    self.dirty = False

  def resetButtons(self):
    self.setButtonLayout([
    QWizard.Stretch,QWizard.BackButton,QWizard.NextButton,QWizard.CancelButton,
    ])
    self.setOption(QWizard.HaveCustomButton1, False)

  def closeEvent(self, event):
    geometry = self.saveGeometry()
    self.settings.setValue('mainwindowgeometry', geometry)



window = Pilcrow()
window.show()
app.exec_()
