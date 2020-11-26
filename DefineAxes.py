from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from MapEditor import MapEditor
from fontTools.designspaceLib import AxisDescriptor
from PyQt5.QtCore import Qt, pyqtSlot, QPoint
from PyQt5 import QtGui

class SliderWithValue(QSlider):
    def  __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setStyleSheet("padding: 40px 0 0 0")
    def paintEvent(self, event):
        QSlider.paintEvent(self, event)

        curr_value = self.value()
        if (self.maximum() - self.minimum()) == 0:
          return
        ratio = (self.value() - self.minimum()) / (self.maximum() - self.minimum())
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(Qt.black))

        font_metrics = QtGui.QFontMetrics(self.font())
        font_width = font_metrics.boundingRect(str(curr_value)).width()
        font_height = font_metrics.boundingRect(str(curr_value)).height()

        rect = self.geometry()
        if self.orientation() == Qt.Horizontal:
            horizontal_x_pos = ratio*rect.width() - font_width/2
            horizontal_y_pos = rect.height() * 0.5 - font_height

            painter.drawText(QPoint(horizontal_x_pos, horizontal_y_pos), str(curr_value))

        elif self.orientation() == Qt.Vertical:
            painter.drawText(QPoint(rect.width() / 2.0 - font_width / 2.0, rect.height() - 5), str(round_value))
        else:
            pass

        painter.drawRect(rect)


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
    self.axesLayout = QVBoxLayout()
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
        default = self.registeredAxes["weight"]["default"]
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

  def setDefaultValues(self, group, axis):
    name = axis.name.lower().strip()
    if name in self.registeredAxes:
      axisDefaults = self.registeredAxes[name]
      axis.tag = axisDefaults["tag"]
      group.tag.setText(axis.tag)
      axis.minimum = axisDefaults["min"]
      group.min.setValue(axis.minimum)
      axis.maximum = axisDefaults["max"]
      group.max.setValue(axis.maximum)
      axis.default = axisDefaults["default"]
      group.default.setValue(axis.default)
    elif not axis.tag or len(axis.tag) < 4:
      axis.tag = self.suggestTag(axis)
      group.tag.setText(axis.tag)

  def suggestTag(self, axis):
    name = axis.name.upper().replace(" ", '')
    return name[:max(len(name),4)]

  @pyqtSlot()
  def setName(self):
    group = self.sender().parent()
    axis = group.axis
    print("Name set")
    axis.name = self.sender().text()
    self.setDefaultValues(group, axis)
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def setTag(self):
    print("Tag set")
    axis = self.sender().parent().axis
    axis.tag = self.sender().text()
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def setMin(self):
    print("Min set")
    group = self.sender().parent()
    axis = group.axis
    axis.minimum = self.sender().value()
    group.max.setMinimum(axis.minimum)
    group.default.setMinimum(axis.minimum)
    print(axis.serialize())
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def setMax(self):
    print("Max set")
    group = self.sender().parent()
    axis = group.axis
    axis.maximum = self.sender().value()
    group.min.setMaximum(axis.maximum)
    group.default.setMaximum(axis.maximum)
    print(axis.serialize())
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def setDefault(self):
    print("Default set")
    group = self.sender().parent()
    axis = group.axis
    axis.default = self.sender().value()
    print(axis.serialize())
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def setHidden(self):
    print("Hidden set")
    group = self.sender().parent()
    axis = group.axis
    axis.hidden = self.sender().isChecked()
    self.completeChanged.emit()
    self.parent.dirty = True

  @pyqtSlot()
  def showMap(self):
    group = self.sender().parent()
    axis = group.axis
    print(group, axis)
    MapEditor(self, axis).exec_()

  def setupAxes(self):
    self._clearLayout(self.axesLayout)
    for ix,ax in enumerate(self.designspace.axes):
      group = QWidget()
      group.axis = ax
      group_layout = QHBoxLayout()
      group.setLayout(group_layout)

      group.name = QLineEdit(group)
      group.name.setPlaceholderText("Name")
      if ax.name:
        group.name.setText(ax.name)
      group.name.textChanged.connect(self.setName)

      group.tag = QLineEdit(group)
      group.tag.setPlaceholderText("Tag")
      group.tag.setMaxLength(4)
      group.tag.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      group.tag.setMaximumWidth(75)
      if ax.tag:
        group.tag.setText(ax.tag)
      group.tag.textChanged.connect(self.setTag)

      group.min = QSpinBox(group)
      group.min.setMinimum(0)
      group.min.setMaximum(1000)
      group.min.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      group.min.setMaximumWidth(85)
      if ax.minimum is not None:
        group.min.setValue(ax.minimum)
      group.min.valueChanged.connect(self.setMin)

      group.default = SliderWithValue(Qt.Horizontal, group)
      if ax.minimum is not None:
        group.default.setMinimum(ax.minimum)
      else:
        group.default.setMinimum(0)
      if ax.maximum is not None:
        group.default.setMaximum(ax.maximum)
      else:
        group.default.setMaximum(1000)
      if ax.default is not None:
        group.default.setValue(ax.default)
      group.default.valueChanged.connect(self.setDefault)

      group.max = QSpinBox(group)
      group.max.setMinimum(0)
      group.max.setMaximum(1000)
      group.max.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      group.max.setMaximumWidth(85)
      if ax.maximum is not None:
        group.max.setValue(ax.maximum)
      group.max.valueChanged.connect(self.setMax)

      group.hidden = QCheckBox("Hidden", group)
      if ax.hidden:
        group.hidden.setChecked(True)
      group.hidden.stateChanged.connect(self.setHidden)

      group.map = QPushButton("Map", group)
      group.map.clicked.connect(self.showMap)

      group_layout.addWidget(group.name)
      group_layout.addWidget(group.tag)
      group_layout.addWidget(group.min)
      group_layout.addWidget(group.default)
      group_layout.addWidget(group.max)
      group_layout.addWidget(group.hidden)
      group_layout.addWidget(group.map)
      removeButton = QPushButton("x")
      removeButton.ix = ix
      group_layout.addWidget(removeButton)
      removeButton.clicked.connect(self.removeRow)
      self.axesLayout.addWidget(group)

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


