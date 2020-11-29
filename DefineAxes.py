from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from MapEditor import MapEditor
from fontTools.designspaceLib import AxisDescriptor
from PyQt5.QtCore import Qt, pyqtSlot, QRegularExpression
from PyQt5 import QtGui
from PyQt5.QtGui import QValidator
import re

tagToolTip =  """<qt>Four letter tag for this axis. Some might be registered at the OpenType specification. Privately-defined axis tags must begin with an uppercase letter and use only uppercase letters or digits.</qt>"""
minToolTip = "<qt>The minimum value for this axis in user space.</qt>"
maxToolTip = "<qt>The maximum value for this axis in user space.</qt>"
defaultToolTip = """<qt>The default value for this axis, i.e. when a new location is created, this is the value this axis will get in user space.</qt>"""
hiddenToolTip = """While most axes are intended to be exposed to the user through a \"slider\" or other interface, some axes (such as <i>opsz</i> or parametric axes) are normally hidden. If this checkbox is set, the axis will be exposed to the user."""
mapToolTip = """<qt>Edits the mapping between userspace and designspace coordinates (avar table).</qt>"""
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
tag_re = "^("+ "|".join([x["tag"] for x in registeredAxes.values()])+ r"|[A-Z]{4})$"


class TagValidator(QValidator):
    def validate(self, s, pos):
        if re.match(tag_re, s):
            return (QValidator.Acceptable, s, pos)
        if s and not re.match(r"^([a-z]+|[A-Z]+)$",s):
            return (QValidator.Invalid, s, pos)
        return (QValidator.Intermediate, s, pos)

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
        tag = registeredAxes["weight"]["tag"],
        minimum = registeredAxes["weight"]["min"],
        maximum = registeredAxes["weight"]["max"],
        default = registeredAxes["weight"]["default"],
        hidden = registeredAxes["weight"]["hidden"],
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

  def setDefaultValuesByName(self, ix):
    axis = self.designspace.axes[ix]
    name = axis.name.lower().strip()
    if name in registeredAxes.keys():
      axisDefaults = registeredAxes[name]
      axis.tag = axisDefaults["tag"]
      self.getWidget(ix, Col.TAG).blockSignals(True)
      self.getWidget(ix, Col.TAG).setText(axis.tag)
      self.getWidget(ix, Col.TAG).blockSignals(False)
      self.setDefaultValues(ix, axisDefaults)
    elif not axis.tag or len(axis.tag) < 4:
      axis.tag = self.suggestTag(axis)
      self.getWidget(ix, Col.TAG).setText(axis.tag)

  def setDefaultValuesByTag(self, ix):
    axis = self.designspace.axes[ix]
    tag = axis.tag
    for name, axisDefaults in registeredAxes.items():
      if tag != axisDefaults["tag"]:
        continue
      axis.name = name
      self.getWidget(ix, Col.NAME).blockSignals(True)
      self.getWidget(ix, Col.NAME).setText(name)
      self.getWidget(ix, Col.NAME).blockSignals(False)
      self.setDefaultValues(ix, axisDefaults)
      break

  def setDefaultValues(self, ix, axisDefaults):
      axis = self.designspace.axes[ix]
      axis.minimum = axisDefaults["min"]
      axis.maximum = axisDefaults["max"]
      axis.default = axisDefaults["default"]
      axis.hidden = axisDefaults["hidden"]
      self.getWidget(ix, Col.MIN).setValue(axis.minimum)
      self.getWidget(ix, Col.MAX).setValue(axis.maximum)
      self.getWidget(ix, Col.DEFAULT).setValue(axis.default)
      self.getWidget(ix, Col.VISIBLE).setChecked(not axis.hidden)

  def suggestTag(self, axis):
    name = axis.name.upper().replace(" ", '')
    return name[:max(len(name),4)]

  @pyqtSlot()
  def setName(self):
    ix = self.sender().ix
    axis = self.designspace.axes[ix]
    print("Name set")
    axis.name = self.sender().text()
    self.setDefaultValuesByName(ix)
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def setTag(self):
    ix = self.sender().ix
    print("Tag set")
    axis = self.designspace.axes[ix]
    axis.tag = self.sender().text()
    self.setDefaultValuesByTag(ix)
    self.parent.dirty = True
    self.completeChanged.emit()

  def getWidget(self, ix, col):
    return self.axesLayout.itemAtPosition(ix+1,col).widget()

  @pyqtSlot()
  def setMin(self):
    print("Min set")
    ix = self.sender().ix
    axis = self.designspace.axes[ix]
    axis.minimum = float(self.sender().value())
    # self.getWidget(ix, Col.DEFAULT).setMinimum(axis.minimum)
    print(axis.serialize())
    self.completeChanged.emit()
    self.updateMap(axis)
    self.parent.dirty = True

  @pyqtSlot()
  def setMax(self):
    print("Max set")
    ix = self.sender().ix
    axis = self.designspace.axes[ix]
    print(axis.serialize())
    axis.maximum = float(self.sender().value())
    # self.getWidget(ix, Col.DEFAULT).setMaximum(axis.maximum)
    print(axis.serialize())
    self.completeChanged.emit()
    self.updateMap(axis)
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

  def updateMap(self, axis):
    if not axis.map:
      return
    bottom, top = axis.map[0], axis.map[-1]
    if bottom[0] != axis.minimum:
      axis.map[0] = (axis.minimum, bottom[1])
    if top[0] != axis.maximum:
      axis.map[-1] = (axis.maximum, top[1])

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
      tag.setValidator(TagValidator())
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
      # if ax.minimum is not None:
      #   default.setMinimum(ax.minimum)
      # if ax.maximum is not None:
      #   default.setMaximum(ax.maximum)
      if ax.default is not None:
        default.setValue(ax.default)
      default.valueChanged.connect(self.setDefault)
      self.axesLayout.addWidget(default,ix+1,Col.DEFAULT)

      maxBox = QSpinBox()
      maxBox.ix = ix
      maxBox.setToolTip(maxToolTip)
      maxBox.setMinimum(0)
      maxBox.setMaximum(1000)
      if ax.maximum is not None:
        maxBox.setValue(ax.maximum)
      maxBox.valueChanged.connect(self.setMax)
      self.axesLayout.addWidget(maxBox,ix+1,Col.MAX)

      visibleInUI = QCheckBox("")
      visibleInUI.ix = ix
      visibleInUI.setToolTip(hiddenToolTip)

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
    seenAxis = {}
    firstError = None
    # Validate whole form
    for ix,axis in enumerate(self.designspace.axes):

      nameW = self.getWidget(ix,Col.NAME)
      if not axis.name:
        nameW.setStyleSheet("border-color: #B00020")
        firstError = firstError or nameW
      else:
        nameW.setStyleSheet("")

      axisW = self.getWidget(ix,Col.TAG)
      if not axis.tag or not re.match(tag_re, axis.tag) or axis.tag in seenAxis:
        axisW.setStyleSheet("border-color: #B00020")
        firstError = firstError or axisW
      else:
        axisW.setStyleSheet("")
      seenAxis[axis.tag] = True

      minW = self.getWidget(ix,Col.MIN)
      if not axis.minimum or axis.minimum > axis.maximum:
        minW.setStyleSheet("border-color: #B00020")
        firstError = firstError or minW
      else:
        minW.setStyleSheet("")

      maxW = self.getWidget(ix,Col.MAX)
      if not axis.maximum:
        maxW.setStyleSheet("border-color: #B00020")
        firstError = firstError or maxW
      else:
        maxW.setStyleSheet("")

      defaultW = self.getWidget(ix,Col.DEFAULT)
      if not axis.default or not (axis.minimum <= axis.default <= axis.maximum):
        defaultW.setStyleSheet("border-color: #B00020")
        firstError = firstError or defaultW
      else:
        defaultW.setStyleSheet("")
    return not firstError

