import sys
from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from pyqt5_material import apply_stylesheet
from fontTools.designspaceLib import AxisDescriptor
from PyQt5.QtCore import Qt, pyqtSlot
from DefineAxes import DefineAxes

from enum import IntEnum
class PageId(IntEnum):
  FIRST_PAGE = 1
  BUILD_FONT = 10
  DEFINE_AXES = 2

# create the application and the main window
app = QApplication(sys.argv)
apply_stylesheet(app, theme='light_blue.xml')

class FirstPage(MyWizardPage):
  def __init__(self, parent=None):
    super(QWizardPage, self).__init__(parent)
    self.setTitle("Let's make a variable font!")
    label = QLabel("Do you have a designspace file already?")
    label.setWordWrap(True)
    layout = QVBoxLayout()
    layout.addWidget(label)
    self.got_designspace_no = QRadioButton("No, I need to make one")
    self.got_designspace_no.clicked.connect(lambda :self.completeChanged.emit())
    self.got_designspace_yes = QRadioButton("Yes, I just need to build the font")
    self.got_designspace_yes.clicked.connect(lambda :self.completeChanged.emit())
    layout.addWidget(self.got_designspace_no)
    layout.addWidget(self.got_designspace_yes)
    self.setLayout(layout)

  def isComplete(self):
    return self.got_designspace_no.isChecked() or self.got_designspace_yes.isChecked()

  def nextId(self):
    if self.got_designspace_no.isChecked():
      return PageId.DEFINE_AXES
    else:
      return PageId.BUILD_FONT


class Pilcrow(QWizard):
  def __init__(self, parent=None):
    super(Pilcrow, self).__init__(parent)
    self.startId = PageId.FIRST_PAGE
    self.axes = [AxisDescriptor()]
    self.setPage(PageId.FIRST_PAGE, FirstPage(self))
    self.setPage(PageId.DEFINE_AXES, DefineAxes(self))
    self.setWindowTitle("Pilcrow")
    self.resize(640,480)



window = Pilcrow()
window.show()
app.exec_()
