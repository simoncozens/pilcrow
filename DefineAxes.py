from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from MapEditor import MapEditor
from fontTools.designspaceLib import AxisDescriptor
from PyQt5.QtCore import Qt, pyqtSlot, QPoint
from PyQt5 import QtGui

tagToolTip =  """<qt>Four letter tag for this axis. Some might be registered at the OpenType specification. Privately-defined axis tags must begin with an uppercase letter and use only uppercase letters or digits.</qt>"""
minToolTip = "<qt>The minimum value for this axis in user space.</qt>"
maxToolTip = "<qt>The maximum value for this axis in user space.</qt>"
defaultToolTip = """<qt>The default value for this axis, i.e. when a new location is created, this is the value this axis will get in user space.</qt>"""
hiddenToolTip = """While most axes are intended to be exposed to the user through a \"slider\" or other interface, some axes (such as <i>opsz</i> or parametric axes) are normally hidden. If this checkbox is set, the axis will be exposed to the user."""
mapToolTip = """<qt>Edits the mapping between userspace and designspace coordinates (avar table).</qt>"""

from enum import IntEnum
class Col(IntEnum):
  NAME = 0
  TAG = 1
  MIN = 2
  DEFAULT = 3
  MAX = 4
  VISIBLE = 5
  MAP = 6
  REMOVE = 7

class DefineAxes(MyWizardPage):
  registeredAxes = {
    "italic": {
      "tag": "ital",
      "min": 0,
      "minFrozen": True,
      "max": 1,
      "maxFrozen": True,
      "default": 0,
      "defaultFrozen": True,
      "hidden": False
    },
    "optical size": {
      "tag": "opsz",
      "min": 1,
      "max": 18,
      "default": 9,
      "defaultFrozen": False,
      "hidden": True
    },
    "slant": {
      "tag": "slnt",
      "min": -90,
      "minFrozen": True,
      "max": 90,
      "maxFrozen": True,
      "default": 0,
      "defaultFrozen": True,
      "hidden": False
    },
    "width": {
      "tag": "wdth",
      "min": 50,
      "max": 200,
      "default": 100,
      "defaultFrozen": True,
      "hidden": False
    },
    "weight": {
      "tag": "wght",
      "min": 1,
      "minFrozen": False,
      "max": 1000,
      "maxFrozen": False,
      "default": 400,
      "defaultFrozen": True,
      "hidden": False
    }
  }

  def __init__(self, parent=None):
    super(QWizardPage, self).__init__(parent)
    self.setTitle("Let's define our axes!")
    self.layout = QVBoxLayout()
    self.setLayout(self.layout)
    self.parent = parent

    self.axesWidget = QWidget()
    self.axesLayout = QGridLayout()
    self.axesWidget.setLayout(self.axesLayout)
    self.layout.addWidget(self.axesWidget)
    self.addButton = QPushButton("Add another")
    self.addButton.clicked.connect(self.addRow)
    self.layout.addWidget(self.addButton)

  def initializePage(self):
    self.designspace = self.parent.designspace
    if not self.designspace.axes:
      self.designspace.axes = [AxisDescriptor(
        name="weight",
        tag = self.registeredAxes["weight"]["tag"],
        minimum = self.registeredAxes["weight"]["min"],
        maximum = self.registeredAxes["weight"]["max"],
        default = self.registeredAxes["weight"]["default"],
        hidden = self.registeredAxes["weight"]["hidden"],
        )]
    self.setupAxes()

  @pyqtSlot()
  def addRow(self):
    self.designspace.axes.append(AxisDescriptor())
    self.setupAxes()
    self.completeChanged.emit()
    print("Row added")
    self.parent.dirty = True

  @pyqtSlot()
  def removeRow(self):
    del self.designspace.axes[self.sender().ix]
    self.setupAxes()
    self.completeChanged.emit()
    print("Row removed")
    self.parent.dirty = True

  def setDefaultValues(self, ix):
    axis = self.designspace.axes[ix]
    name = axis.name.lower().strip()
    if name in self.registeredAxes:
      axisDefaults = self.registeredAxes[name]
      axis.tag = axisDefaults["tag"]
      axis.minimum = axisDefaults["min"]
      axis.maximum = axisDefaults["max"]
      axis.default = axisDefaults["default"]
      axis.hidden = axisDefaults["hidden"]
      self.axesLayout.itemAtPosition(ix+1,Col.TAG).widget().setText(axis.tag)
      self.axesLayout.itemAtPosition(ix+1,Col.MIN).widget().setValue(axis.minimum)
      self.axesLayout.itemAtPosition(ix+1,Col.MAX).widget().setValue(axis.maximum)
      self.axesLayout.itemAtPosition(ix+1,Col.DEFAULT).widget().setValue(axis.default)
      self.axesLayout.itemAtPosition(ix+1,Col.VISIBLE).widget().setChecked(not axis.hidden)
    elif not axis.tag or len(axis.tag) < 4:
      axis.tag = self.suggestTag(axis)
      self.axesLayout.itemAtPosition(ix+1,Col.TAG).widget().setText(axis.tag)

  def suggestTag(self, axis):
    name = axis.name.upper().replace(" ", '')
    return name[:max(len(name),4)]

  @pyqtSlot()
  def setName(self):
    ix = self.sender().ix
    axis = self.designspace.axes[ix]
    print("Name set")
    axis.name = self.sender().text()
    self.setDefaultValues(ix)
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def setTag(self):
    print("Tag set")
    axis = self.designspace.axes[self.sender().ix]
    axis.tag = self.sender().text()
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def setMin(self):
    print("Min set")
    ix = self.sender().ix
    axis = self.designspace.axes[ix]
    axis.minimum = float(self.sender().value())
    self.axesLayout.itemAtPosition(ix+1,Col.MAX).widget().setMinimum(axis.minimum)
    self.axesLayout.itemAtPosition(ix+1,Col.DEFAULT).widget().setMinimum(axis.minimum)
    print(axis.serialize())
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def setMax(self):
    print("Max set")
    ix = self.sender().ix
    axis = self.designspace.axes[ix]
    axis.maximum = float(self.sender().value())
    self.axesLayout.itemAtPosition(ix+1,Col.MIN).widget().setMinimum(axis.minimum)
    self.axesLayout.itemAtPosition(ix+1,Col.DEFAULT).widget().setMinimum(axis.minimum)
    print(axis.serialize())
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def setDefault(self):
    print("Default set")
    axis = self.designspace.axes[self.sender().ix]
    axis.default = float(self.sender().value())
    print(axis.serialize())
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def setHidden(self):
    print("Hidden set")
    axis = self.designspace.axes[self.sender().ix]
    axis.hidden = not self.sender().isChecked()
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def showMap(self):
    axis = self.designspace.axes[self.sender().ix]
    MapEditor(self, axis).exec_()

  def _createFixedWidthLabel(self, text, width, tooltip=None):
    w = QLabel(text)
    w.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    w.setMaximumWidth(width)
    if tooltip:
      w.setToolTip(tooltip)
    return w

  def setupAxes(self):
    self._clearLayout(self.axesLayout)
    self.axesLayout.addWidget(QLabel("Axis name"), 0,Col.NAME)
    self.axesLayout.addWidget(self._createFixedWidthLabel("Tag", 75,tagToolTip),0,Col.TAG)
    self.axesLayout.addWidget(self._createFixedWidthLabel("Min", 85, minToolTip),0,Col.MIN)
    self.axesLayout.addWidget(self._createFixedWidthLabel("Default", 85, defaultToolTip),0,Col.DEFAULT)
    self.axesLayout.addWidget(self._createFixedWidthLabel("Max", 85, maxToolTip),0,Col.MAX)
    self.axesLayout.addWidget(self._createFixedWidthLabel("Show in UI?", 85, hiddenToolTip),0,Col.VISIBLE)

    for ix,ax in enumerate(self.designspace.axes):
      name = QLineEdit()
      name.ix = ix
      name.setPlaceholderText("Name")
      if ax.name:
        name.setText(ax.name)
      name.textChanged.connect(self.setName)
      self.axesLayout.addWidget(name,ix+1,Col.NAME)

      tag = QLineEdit()
      tag.ix = ix
      tag.setPlaceholderText("Tag")
      tag.setToolTip(tagToolTip)
      # validator XXX
      tag.setMaxLength(4)
      tag.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      tag.setMaximumWidth(75)
      if ax.tag:
        tag.setText(ax.tag)
      tag.textChanged.connect(self.setTag)
      self.axesLayout.addWidget(tag,ix+1,Col.TAG)

      minBox = QSpinBox()
      minBox.ix = ix
      minBox.setToolTip(minToolTip)
      minBox.setMinimum(0)
      minBox.setMaximum(1000)
      # XXX Validator
      if ax.minimum is not None:
        minBox.setValue(ax.minimum)
      minBox.valueChanged.connect(self.setMin)
      self.axesLayout.addWidget(minBox,ix+1,Col.MIN)

      default = QSpinBox()
      default.ix = ix
      default.setToolTip(defaultToolTip)
      default.setMinimum(ax.minimum)
      default.setMaximum(ax.maximum)
      if ax.default is not None:
        default.setValue(ax.default)
      default.valueChanged.connect(self.setDefault)
      self.axesLayout.addWidget(default,ix+1,Col.DEFAULT)

      maxBox = QSpinBox()
      maxBox.ix = ix
      maxBox.setToolTip(maxToolTip)
      maxBox.setMinimum(ax.minimum)
      maxBox.setMaximum(ax.maximum)
      maxBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      maxBox.setMaximumWidth(85)
      if ax.maximum is not None:
        maxBox.setValue(ax.maximum)
      maxBox.valueChanged.connect(self.setMax)
      self.axesLayout.addWidget(maxBox,ix+1,Col.MAX)

      visibleInUI = QCheckBox("")
      visibleInUI.ix = ix
      visibleInUI.setToolTip(hiddenToolTip)
      visibleInUI.setMaximumWidth(85)
      visibleInUI.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

      if not ax.hidden:
        visibleInUI.setChecked(True)
      else:
        visibleInUI.setChecked(False)
      visibleInUI.stateChanged.connect(self.setHidden)
      self.axesLayout.addWidget(visibleInUI,ix+1,Col.VISIBLE)

      mapButton = QPushButton("Map")
      mapButton.ix = ix
      mapButton.setToolTip(mapToolTip)
      mapButton.clicked.connect(self.showMap)
      self.axesLayout.addWidget(mapButton,ix+1,Col.MAP)

      removeButton = QPushButton("x")
      removeButton.setToolTip("Removes the axis from the designspace")
      removeButton.ix = ix
      removeButton.clicked.connect(self.removeRow)
      self.axesLayout.addWidget(removeButton,ix+1,Col.REMOVE)

  def isComplete(self):
    if len(self.designspace.axes) < 1: return False
    for axis in self.designspace.axes:
      if not axis.name: return False
      if not axis.tag: return False
      if not axis.minimum: return False
      if not axis.maximum: return False
      if not axis.default: return False
      if axis.minimum > axis.maximum: return False
      if not (axis.minimum <= axis.default <= axis.maximum): return False
    return True


