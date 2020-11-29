from PyQt5.QtWidgets import *
from AvarGraph import AvarGraph
from copy import deepcopy
from PyQt5.QtCore import Qt


class MapEditor(QDialog):
    def __init__(self, parent, axis):
        super().__init__(parent)
        self.parent = parent
        self.orig_axis = axis
        self.axis = deepcopy(axis)
        self.layout = QVBoxLayout()

        self.top = QWidget()
        self.top_layout = QHBoxLayout()
        self.top.setLayout(self.top_layout)


        self.top_layout.addWidget(QLabel("Design space min/max:"))
        self.ds_min = QSpinBox()
        self.ds_min.editingFinished.connect(self.setDesignspaceLim)
        self.ds_min.setMinimum(0)
        self.ds_min.setMaximum(65535)
        self.top_layout.addWidget(self.ds_min)

        self.ds_min.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.ds_max = QSpinBox()
        self.ds_max.editingFinished.connect(self.setDesignspaceLim)
        self.ds_max.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.ds_max.setMinimum(0)
        self.ds_max.setMaximum(65535)
        self.top_layout.addWidget(self.ds_max)
        self.top_layout.addStretch()

        self.top_layout.addWidget(QLabel("Design space coordinate:"))
        self.dx = QSpinBox()
        self.dx.valueChanged.connect(self.manualMove)
        self.top_layout.addWidget(self.dx)

        self.top_layout.addWidget(QLabel("User space coordinate:"))
        self.dy = QSpinBox()
        self.dy.setMinimum(axis.minimum)
        self.dy.setMaximum(axis.maximum)
        self.dy.valueChanged.connect(self.manualMove)
        self.top_layout.addWidget(self.dy)

        self.bottom = AvarGraph(self.axis)
        self.bottom.selectionChanged.connect(self.movePoint)
        self.bottom.selectionMoved.connect(self.movePoint)

        self.dx.setEnabled(False)
        self.dy.setEnabled(False)

        dsCoords = [ x[1] for x in self.axis.map ]
        self.ds_min.setValue(min(dsCoords))
        self.ds_max.setValue(max(dsCoords))

        self.layout.addWidget(self.top)
        self.layout.addWidget(self.bottom)
        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.layout.addWidget(bbox)
        self.setLayout(self.layout)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        self.dontLoop = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            return
        super().keyPressEvent(event)

    def movePoint(self):
        if self.dontLoop:
          return
        self.dontLoop = True
        if self.bottom.lastSelected:
            self.parent.parent.dirty = True
            self.dx.setEnabled(True)
            self.dy.setEnabled(True)
            self.dx.setValue(self.bottom.lastSelected.x)
            self.dy.setValue(self.bottom.lastSelected.y)
        else:
            self.dx.setEnabled(False)
            self.dy.setEnabled(False)
        self.dontLoop = False

    def setDesignspaceLim(self):
        newmin, newmax = self.ds_min.value(), self.ds_max.value()
        for ix,pt in enumerate(self.axis.map):
            self.axis.map[ix] = (
                pt[0],
                max(newmin, min(newmax, pt[1]))
            )
        self.axis.map[0] = (self.axis.map[0][0], newmin)
        self.axis.map[-1] = (self.axis.map[-1][0], newmax)

        self.bottom.fromMap()
        self.bottom.updateFigure()

    def manualMove(self):
        pt = self.bottom.lastSelected
        if not pt or self.dontLoop:
            return
        self.dontLoop = True
        pt.setup_move(self.dy.value(), self.dx.value())
        pt.background = pt.point.figure.canvas.copy_from_bbox(pt.point.axes.bbox)
        pt.move_point(self.dy.value(), self.dx.value())
        pt.on_release(None)
        self.dontLoop = False


    def accept(self):
        self.orig_axis.map = self.bottom.axis.map
        super().accept()
