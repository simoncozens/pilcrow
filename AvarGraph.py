import sys
from PyQt5 import QtWidgets, QtGui

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from fontTools.designspaceLib import AxisDescriptor
from PyQt5.QtCore import pyqtSignal

# Personnal modules
from DraggablePoint import DraggablePoint


class AvarGraph(FigureCanvas):
    selectionChanged = pyqtSignal()
    selectionMoved = pyqtSignal()

    def __init__(self, axis, parent=None):

        self.fig = Figure()
        self.axis = axis

        self.axes = self.fig.add_subplot(111)
        self.lastSelected = None

        if not axis.map:
          self.axis.map = [(axis.minimum, axis.minimum), (axis.maximum, axis.maximum)]

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.list_points = []

        self.connect()
        self.show()
        self.fromMap()
        self.updateFigure()

    def fromMap(self):
        self.axes.clear()
        self.setLimits()
        del(self.list_points[:])
        self.list_points = [DraggablePoint(self, self.axis.map[0][1], self.axis.map[0][0], 5)]
        for y,x in self.axis.map[1:]:
          self.list_points.append(DraggablePoint(self, x, y, 5, prev=self.list_points[-1]))

    def toMap(self):
        self.axis.map = [(p.y,p.x) for p in self.list_points]

    def connect(self):
        self.cidpress = self.mpl_connect('button_press_event', self.on_press)

    def on_press(self, event):
        if not event.dblclick:
            return
        # If I'm sitting on a point, remove it;

        # If not, add one.
        cx, cy = event.xdata, event.ydata
        for ix,p in enumerate(self.list_points):
          if p.point.contains(event)[0]:
            if ix == 0 or ix == len(self.list_points)-1:
              break
            # linked list deletion!
            self.list_points[ix+1].prev = self.list_points[ix-1]
            self.list_points[ix].line.remove()
            self.list_points[ix].point.remove()
            self.list_points[ix+1].line.remove()
            self.list_points[ix+1].setLine()
            del(self.list_points[ix])
            self.setLastSelected(None)
            break

          elif p.x < cx:
            continue
          # Adding

          newpoint = DraggablePoint(self,cx,cy,5, prev = self.list_points[ix-1])
          self.list_points[ix].prev = newpoint
          self.list_points.insert(ix, newpoint)
          self.list_points[ix].on_press(event)
          self.list_points[ix].on_motion(event)
          self.list_points[ix].on_release(event)
          self.setLastSelected(newpoint)
          break

        self.updateFigure()

    def setLimits(self):
        # X axis = designspace = element 1 of map list
        self.axes.grid(True)
        self.axes.set_xlabel("Design space")
        self.axes.set_ylabel("User space")
        self.axes.set_ylim(self.axis.minimum, self.axis.maximum)
        dsCoords = [ x[1] for x in self.axis.map ]
        self.axes.set_xlim(min(dsCoords), max(dsCoords))

    def updateFigure(self):
        """Update the graph. Necessary, to call after each plot"""
        self.toMap()
        self.setLimits()
        self.draw()
        self.update()

    def setLastSelected(self, pt):
        self.lastSelected = pt
        self.selectionChanged.emit()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    axis = AxisDescriptor(minimum=400, maximum=1000, default=2)
    ex = AvarGraph(axis)
    sys.exit(app.exec_())
