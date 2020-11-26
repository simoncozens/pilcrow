from PyQt5.QtWidgets import *
from AvarGraph import AvarGraph
from copy import deepcopy


class MapEditor(QDialog):
    def __init__(self, parent, axis):
        super().__init__(parent)
        self.orig_axis = axis
        self.axis = deepcopy(axis)
        self.layout = QVBoxLayout()

        self.top = QWidget()
        self.top_layout = QHBoxLayout()
        self.top.setLayout(self.top_layout)
        self.top_layout.addWidget(QLabel("Design space coordinate:"))
        self.dx = QSpinBox()
        self.dx.setMinimum(axis.minimum)
        self.dx.setMaximum(axis.maximum)
        self.top_layout.addWidget(self.dx)

        self.top_layout.addWidget(QLabel("User space coordinate:"))
        self.dy = QSpinBox()
        self.dy.setMinimum(axis.minimum)
        self.dy.setMaximum(axis.maximum)
        self.top_layout.addWidget(self.dy)

        self.bottom = AvarGraph(axis)
        self.bottom.selectionChanged.connect(self.movePoint)
        self.bottom.selectionMoved.connect(self.movePoint)

        self.layout.addWidget(self.top)
        self.layout.addWidget(self.bottom)
        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.layout.addWidget(bbox)
        self.setLayout(self.layout)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)

    def movePoint(self):
        if self.bottom.lastSelected:
            self.dx.setValue(self.bottom.lastSelected.x)
            self.dy.setValue(self.bottom.lastSelected.y)
        else:
            self.dx.setValue(None)
            self.dy.setValue(None)

    def accept(self):
        self.orig_axis.map = self.bottom.axis.map
        print(self.bottom.axis.map)
        super().accept()
