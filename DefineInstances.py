from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from fontTools.designspaceLib import InstanceDescriptor
from PyQt5.QtCore import Qt, pyqtSlot, QPoint, pyqtSignal
from PyQt5 import QtGui
import re, os
from QDesignSpace import DesignSpaceVisualizer


class InstanceNameDialog(QDialog):
  def __init__(self, instance, parent=None):
    super(QDialog, self).__init__(parent)
    self.instance = instance
    self.layout = QVBoxLayout()
    self.setLayout(self.layout)
    self.form = QFormLayout()
    self.layout.addLayout(self.form)

    fieldsmap = [
      ("Style Name", "styleName"),
      ("Family Name", "familyName"),
      ("Filename", "filename"),
      ("Name", "name"),
    ]

    self.formFields = []
    self.filenameManuallySet = False
    self.nameManuallySet = False

    for label, attr in fieldsmap:
      w = QLineEdit()
      w.attr = attr
      if getattr(instance, attr):
        w.setText(getattr(instance,attr))
      w.textChanged.connect(self.updateWidget)
      self.formFields.append(w)
      self.form.addRow(label, w)

    if instance.filename:
      self.filenameManuallySet = True
    if instance.name:
      self.filenameManuallySet = True

    bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    self.layout.addWidget(bbox)
    bbox.accepted.connect(self.accept)
    bbox.rejected.connect(self.reject)

  def accept(self):
    if not self.instance.name:
      self.formFields[-1].setFocus()
      return
    if not self.instance.styleName:
      self.formFields[2].setFocus()
      return
    super().accept()

  def makeAFilename(self):
    self.instance.filename = "%s-%s.ufo" % (self.instance.familyName, self.instance.styleName)
    self.instance.filename.replace(" ", "-")
    self.formFields[2].blockSignals(True)
    self.formFields[2].setText(self.instance.filename)
    self.formFields[2].blockSignals(False)

  def makeAName(self):
    self.instance.name = "%s %s" % (self.instance.familyName, self.instance.styleName)
    self.formFields[-1].blockSignals(True)
    self.formFields[-1].setText(self.instance.name)
    self.formFields[-1].blockSignals(False)

  @pyqtSlot()
  def updateWidget(self):
    sender = self.sender()
    setattr(self.instance, sender.attr, sender.text())
    if not self.filenameManuallySet and sender.attr != "filename":
      self.makeAFilename()
    if not self.filenameManuallySet and sender.attr != "name":
      self.makeAName()
    if sender.attr == "filename":
      self.filenameManuallySet = True
    if sender.attr == "name":
      self.nameManuallySet = True

class DefineInstances(MyWizardPage):
  disableEnter = True

  def __init__(self, parent=None):
    super(QWizardPage, self).__init__(parent)
    self.parent = parent
    self.designspace = parent.designspace

    self.setTitle("Do you want any named instances?")
    self.splitter = QSplitter()
    self.layout = QHBoxLayout()
    self.layout.addWidget(self.splitter)
    self.setLayout(self.layout)
    self.splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.left = QWidget()
    self.left_layout = QVBoxLayout()
    self.left.setLayout(self.left_layout)
    self.instancesScroll = QScrollArea()
    self.instancesWidget = QWidget()
    self.instancesScroll.setWidget(self.instancesWidget)
    self.instancesScroll.setWidgetResizable(True)
    self.instancesLayout = QVBoxLayout()
    self.instancesWidget.setLayout(self.instancesLayout)
    self.left_layout.addWidget(self.instancesScroll)

    self.addButton = QPushButton("Add another")
    self.addButton.clicked.connect(self.addInstance)
    self.left_layout.addWidget(self.addButton)

    self.splitter.addWidget(self.left)

    self.right = DesignSpaceVisualizer(self.designspace)
    self.splitter.addWidget(self.right)


  def initializePage(self):
    self.designspace = self.parent.designspace
    self.right.setParent(None)
    self.right.deleteLater()
    self.right = DesignSpaceVisualizer(self.designspace, draw_glyph="e")
    self.splitter.addWidget(self.right)
    width = qApp.desktop().availableGeometry(self).width()
    self.splitter.setSizes([width * 2/3, width * 1/3])

    self.setupInstances()
    self.completeChanged.emit()

  @pyqtSlot()
  def addInstance(self):
    print("Instance added")
    self.parent.dirty = True
    instance = InstanceDescriptor()
    instance.location = { x.name: x.default for x in self.designspace.axes }
    instance.familyName = self.designspace.sources[0].familyName

    self.designspace.instances.append(instance)
    self.initializePage()
    self.right.refresh()

  @pyqtSlot()
  def removeRow(self):
    print("Removed")
    del self.designspace.instances[self.sender().ix]
    self.parent.dirty = True
    self.initializePage()

  @pyqtSlot()
  def locationChanged(self):
    print("Location changed")
    self.parent.dirty = True
    loc = self.sender()
    instance = loc.instance
    if not instance.location:
      instance.location = {}
    instance.location[loc.name] = loc.value()
    print(self.designspace.tostring())
    self.right.refresh()

  @pyqtSlot()
  def setNames(self):
    group = self.sender().parent()
    InstanceNameDialog(group.instance).exec_()
    group.name.setText(group.instance.name)
    self.completeChanged.emit()

  def setupInstances(self):
    self._clearLayout(self.instancesLayout)
    headergroup = QWidget()
    headergroup_layout = QHBoxLayout()
    headergroup.setLayout(headergroup_layout)
    headergroup_layout.addWidget(QLabel("Instance"))
    headergroup_layout.addWidget(QLabel(" "))
    for ax in self.designspace.axes:
      headergroup_layout.addWidget(QLabel(ax.name))
    headergroup_layout.addWidget(QLabel("Remove"))
    self.instancesLayout.addWidget(headergroup)

    for ix,instance in enumerate(self.designspace.instances):
      if not instance.location:
        instance.location = {}
      group = QWidget()
      group.instance = instance
      group_layout = QHBoxLayout()
      group.setLayout(group_layout)

      group.name = QLabel()
      if instance.name:
        group.name.setText(instance.name)
      group.name.setWordWrap(True)
      group_layout.addWidget(group.name)

      group.names = QPushButton("Names")
      group.names.clicked.connect(self.setNames)
      group_layout.addWidget(group.names)

      for ax in self.designspace.axes:
        name = ax.name
        loc = QSpinBox()
        loc.tag = ax.tag
        loc.name = ax.name
        loc.instance = instance
        loc.setMinimum(ax.minimum)
        loc.setMaximum(ax.maximum)
        if name in instance.location:
          loc.setValue(instance.location[name])
        else:
          loc.setValue(ax.default)
        loc.valueChanged.connect(self.locationChanged)
        group_layout.addWidget(loc)

      removeButton = QPushButton("Remove")
      removeButton.ix = ix
      group_layout.addWidget(removeButton)
      removeButton.clicked.connect(self.removeRow)
      self.instancesLayout.addWidget(group)

  def isComplete(self):
    for instance in self.designspace.instances:
      if not instance.name:
        return False
      if not instance.styleName:
        return False
      if not instance.familyName:
        instance.familyName = self.designspace.sources[0].familyName
      if not instance.familyName:
        return False
      if not instance.filename:
        return False
    return True
    return len(self.designspace.sources) > 1

