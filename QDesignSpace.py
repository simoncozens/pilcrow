from beziers.path import BezierPath
from fontTools.ttLib import TTFont
from fontTools.designspaceLib import DesignSpaceDocument
import defcon
from beziers.path.representations.Nodelist import NodelistRepresentation, Node
from beziers.path.representations.Segment import SegmentRepresentation
from beziers.affinetransformation import AffineTransformation
from beziers.point import Point
from mpl_toolkits.mplot3d import art3d
from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from matplotlib.figure import Figure
import sys
import matplotlib.patches as patches

class DesignSpaceVisualizer(QWidget):
  def __init__(self, designspace, parent = None, draw_glyph = False):
    super().__init__(parent)
    self.designspace = designspace
    self.draw_glyph = draw_glyph
    self.layout = QVBoxLayout(self)
    self.figure = Figure()
    self.canvas = FigureCanvas(self.figure)
    self.layout.addWidget(self.canvas)
    self.axis_count = len(self.designspace.axes)
    self.ax = self.setup_axes()
    self.refresh()


  def clearLayout(self):
    self._clearLayout(self.layout)

  def _clearLayout(self,layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self._clearLayout(item.layout())

  def refresh(self):
    self.labels_and_limits()
    if self.draw_glyph:
      self.designspace.loadSourceFonts(defcon.Font)
      if self.axis_count == 3:
        self.do_three_axis()
      elif 1 <= self.axis_count <= 2:
        self.do_one_or_two_axis()
    self.canvas.draw()

  def glyph_to_paths(self, glyph):
    paths = []
    for c in glyph:
      path = BezierPath()
      path.closed = False
      nodeList = []
      for p in c:
        t = p.segmentType
        if t is None:
          t = "offcurve"
        elif "line" in t:
          t = "line"
        else:
          t = "curve"
        nodeList.append(Node(p.x,p.y,t))
      path.activeRepresentation = NodelistRepresentation(path, nodeList)
      if nodeList[0].point != nodeList[-1].point:
        nodeList.append(nodeList[0])
      paths.append(path)
    return paths

  def do_three_axis(self):
    x_axis, y_axis, z_axis = self.designspace.axes[0:3]
    styles_are_unique = len(set([s.styleName for s in self.designspace.sources])) == len(self.designspace.sources)

    for source in self.designspace.sources:
      loc = source.location
      if x_axis.name not in loc or y_axis.name not in loc or z_axis.name not in loc:
        continue
      at = AffineTransformation.scaling(
          (x_axis.maximum-x_axis.minimum)/10000,
          (z_axis.maximum-z_axis.minimum)/10000,
          )
      if styles_are_unique:
        fn = source.styleName
      else:
        fn = source.filename
      fn = fn.replace("-","-\n")
      fn = fn.replace(" ","\n")
      z_shift = 1.0/10*(z_axis.maximum-z_axis.minimum)
      xloc = x_axis.map_backward(loc[x_axis.name])
      yloc = y_axis.map_backward(loc[y_axis.name])
      zloc = z_axis.map_backward(loc[z_axis.name])
      self.ax.text(xloc, yloc, zloc+z_shift, fn, None, wrap=True, size="x-small")
      at.translate(Point(xloc,zloc))
      if self.draw_glyph in source.font:
        a = source.font[self.draw_glyph]
        self.do_draw_glyph(a, at, z_loc=yloc)

  def do_one_or_two_axis(self):
    x_axis = self.designspace.axes[0]
    styles_are_unique = len(set([s.styleName for s in self.designspace.sources])) == len(self.designspace.sources)
    if self.axis_count >= 2:
      y_axis = self.designspace.axes[1]
    else:
      self.figure.subplots_adjust(bottom=0.2)
    for source in self.designspace.sources:
      at = AffineTransformation.scaling(
          (self.ax.get_xlim()[1]-self.ax.get_xlim()[0])/10000,
          (self.ax.get_ylim()[1]-self.ax.get_ylim()[0])/10000,
          )
      loc = source.location
      if x_axis.name not in loc:
        continue
      if styles_are_unique:
        fn = source.styleName
      else:
        fn = source.filename
      fn = fn.replace("-","-\n")
      fn = fn.replace(" ","\n")
      y_shift = 1.0/10*(self.ax.get_ylim()[1]-self.ax.get_ylim()[0])
      if self.axis_count == 2:
        if y_axis.name not in loc:
          continue
        yloc = y_axis.map_backward(loc[y_axis.name])
      else:
        yloc = 0
      xloc = x_axis.map_backward(loc[x_axis.name])
      # print(fn, xloc, yloc)
      self.ax.text(xloc, yloc+y_shift, fn, None, wrap=True, size="x-small")
      at.translate(Point(xloc,yloc))
      if self.draw_glyph in source.font:
        a = source.font[self.draw_glyph]
        self.do_draw_glyph(a, at)

  def do_draw_glyph(self, glyph, transformation, z_loc=None):
      paths = self.glyph_to_paths(glyph)
      bounds = paths[0].bounds()
      for p in paths[1:]:
        bounds.extend(p.bounds())
      width = bounds.width/2
      height = bounds.height/2
      for p in paths:
        seg2 = [ x.translated(Point(-width/2,-height/2)).transformed(transformation) for x in p.asSegments()]
        p.activeRepresentation = SegmentRepresentation(p, seg2)
        mp = p.asMatplot()

        patch = patches.PathPatch(mp, fill=True,clip_on=False, linewidth=0)
        self.ax.add_patch(patch)
        if self.ax.name == "3d":
          art3d.pathpatch_2d_to_3d(patch, z=z_loc,zdir="y")

  def setup_axes(self):
    if len(self.designspace.axes) > 2:
      ax = self.canvas.figure.add_subplot(111, projection='3d')
    else:
      ax = self.canvas.figure.add_subplot(111)
    if self.axis_count == 1:
      ax.yaxis.set_visible(False)
      ax.spines["top"].set_visible(False)
      ax.spines["right"].set_visible(False)
      ax.spines["left"].set_visible(False)
    return ax

  def labels_and_limits(self):
    self.ax.clear()
    methods = [
      ("set_xlim", "set_xlabel"),
      ("set_ylim", "set_ylabel"),
      ("set_zlim", "set_zlabel")
    ]
    for i, axis in enumerate(self.designspace.axes):
      if i >= self.axis_count:
        break
      getattr(self.ax,methods[i][0])([axis.minimum, axis.maximum])
      getattr(self.ax,methods[i][1])(axis.name)


if __name__ == "__main__":
  qapp = QApplication(sys.argv)
  designspace = DesignSpaceDocument.fromfile("amstelvar/AmstelvarDB.designspace")
  designspace.axes[2].maximum=18

  app = DesignSpaceVisualizer(designspace, draw_glyph="e")
  app.show()
  qapp.exec_()

