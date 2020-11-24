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
    self.axis_count = len(designspace.axes)
    self.draw_glyph = draw_glyph
    self.canvas = FigureCanvas(Figure())
    self.layout = QVBoxLayout(self)
    self.ax = self.setup_axes()
    self.layout.addWidget(self.canvas)

    if self.draw_glyph:
      designspace.loadSourceFonts(defcon.Font)
      if self.axis_count == 3:
        self.do_three_axis()
      elif 1 <= self.axis_count <= 2:
        self.do_one_or_two_axis()

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

    for source in self.designspace.sources:
      at = AffineTransformation.scaling(
          (x_axis.maximum-x_axis.minimum)/10000,
          (z_axis.maximum-z_axis.minimum)/10000,
          )
      a = source.font[self.draw_glyph]
      loc = source.location
      fn = source.filename.replace("-","-\n")
      z_shift = 1.0/10*(z_axis.maximum-z_axis.minimum)
      self.ax.text(loc[x_axis.tag], loc[y_axis.tag], loc[z_axis.tag]+z_shift, fn, None, wrap=True, size="x-small")
      at.translate(Point(loc[x_axis.tag],loc[z_axis.tag]))
      self.do_draw_glyph(a, at, z_loc=loc[y_axis.tag])

  def do_one_or_two_axis(designspace, axis_count = 2):
    x_axis = designspace.axes[0]
    if axis_count >= 2:
      y_axis = designspace.axes[1]

    for source in designspace.sources:
      at = AffineTransformation.scaling(
          (ax.get_xlim()[1]-ax.get_xlim()[0])/10000,
          (ax.get_ylim()[1]-ax.get_ylim()[0])/10000,
          )
      a = source.font[self.draw_glyph]
      loc = source.location
      fn = source.filename.replace("-","-\n")
      y_shift = 1.0/10*(ax.get_ylim()[1]-ax.get_ylim()[0])
      if axis_count == 2:
        yloc = loc[y_axis.tag]
      else:
        yloc = 0
      ax.text(loc[x_axis.tag], yloc+y_shift, fn, None, wrap=True, size="x-small")
      at.translate(Point(loc[x_axis.tag],yloc))
      self.do_draw_glyph(a, at)

  def do_draw_glyph(self, glyph, transformation, z_loc=None):
      paths = self.glyph_to_paths(glyph)
      bounds = paths[0].bounds()
      for p in paths[1:]:
        bounds.extend(p.bounds())
      width = bounds.width/2
      for p in paths:
        seg2 = [ x.translated(Point(-width/2,0)).transformed(transformation) for x in p.asSegments()]
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

    methods = [
      ("set_xlim", "set_xlabel"),
      ("set_ylim", "set_ylabel"),
      ("set_zlim", "set_zlabel")
    ]
    for i, axis in enumerate(self.designspace.axes):
      if i >= self.axis_count:
        break
      getattr(ax,methods[i][0])([axis.minimum, axis.maximum])
      getattr(ax,methods[i][1])(axis.name)

    return ax


if __name__ == "__main__":
  qapp = QApplication(sys.argv)
  designspace = DesignSpaceDocument.fromfile("amstelvar/AmstelvarDB.designspace")
  designspace.axes[2].maximum=18

  app = DesignSpaceVisualizer(designspace, draw_glyph="e")
  app.show()
  qapp.exec_()

