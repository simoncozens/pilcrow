import matplotlib.pyplot as plt
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


def glyph_to_paths(glyph):
  paths = []
  for c in glyph:
    path = BezierPath()
    path.closed = False
    nodeList = []
    for p in c:
      t = p.segmentType
      if t is None:
        t = "offcurve"
      nodeList.append(Node(p.x,p.y,t))
    path.activeRepresentation = NodelistRepresentation(path, nodeList)
    if nodeList[0].point == nodeList[-1].point:
      path.closed = True
    paths.append(path)
  return paths

designspace = DesignSpaceDocument.fromfile("amstelvar/AmstelvarDB.designspace")
designspace.loadSourceFonts(defcon.Font)

canvas = FigureCanvas(Figure())
app = QWidget()
layout = QVBoxLayout(app)
layout.addWidget(canvas)

# del(designspace.axes[2])
# del(designspace.axes[1])
designspace.axes[2].maximum = 14

def do_three_axis(designspace):
  ax = setup_axes(canvas.figure, designspace)
  x_axis, y_axis, z_axis = designspace.axes[0:3]

  for source in designspace.sources:
    at = AffineTransformation.scaling(
        (x_axis.maximum-x_axis.minimum)/10000,
        (z_axis.maximum-z_axis.minimum)/10000,
        )
    a = source.font["A"]
    loc = source.location
    fn = source.filename.replace("-","-\n")
    z_shift = 1.0/10*(z_axis.maximum-z_axis.minimum)
    ax.text(loc[x_axis.tag], loc[y_axis.tag], loc[z_axis.tag]+z_shift, fn, None, wrap=True, size="x-small")
    at.translate(Point(loc[x_axis.tag],loc[z_axis.tag]))
    draw_glyph(a, at, ax, z_loc=loc[y_axis.tag])

def do_one_or_two_axis(designspace, axis_count = 2):
  ax = setup_axes(canvas.figure, designspace)
  x_axis = designspace.axes[0]
  if axis_count >= 2:
    y_axis = designspace.axes[1]
  else:
    ax.yaxis.set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

  for source in designspace.sources:
    at = AffineTransformation.scaling(
        (ax.get_xlim()[1]-ax.get_xlim()[0])/10000,
        (ax.get_ylim()[1]-ax.get_ylim()[0])/10000,
        )
    a = source.font["A"]
    loc = source.location
    fn = source.filename.replace("-","-\n")
    y_shift = 1.0/10*(ax.get_ylim()[1]-ax.get_ylim()[0])
    if axis_count == 2:
      yloc = loc[y_axis.tag]
    else:
      yloc = 0
    ax.text(loc[x_axis.tag], yloc+y_shift, fn, None, wrap=True, size="x-small")
    at.translate(Point(loc[x_axis.tag],yloc))
    draw_glyph(a, at, ax)

def draw_glyph(glyph, transformation, ax, z_loc=None):
    paths = glyph_to_paths(glyph)
    bounds = paths[0].bounds()
    for p in paths[1:]:
      bounds.extend(p.bounds())
    width = bounds.width/2
    for p in paths:
      seg2 = [ x.translated(Point(-width/2,0)).transformed(transformation) for x in p.asSegments()]
      p.activeRepresentation = SegmentRepresentation(p, seg2)
      mp = p.asMatplot()
      print(mp)

      patch = patches.PathPatch(mp, fill=True,clip_on=False, linewidth=0)
      ax.add_patch(patch)
      if ax.name == "3d":
        art3d.pathpatch_2d_to_3d(patch, z=z_loc,zdir="y")

def setup_axes(fig, designspace):
  if len(designspace.axes) > 2:
    ax = fig.add_subplot(111, projection='3d')
  else:
    ax = fig.add_subplot(111)

  methods = [
    ("set_xlim", "set_xlabel"),
    ("set_ylim", "set_ylabel"),
    ("set_zlim", "set_zlabel")
  ]
  for i, axis in enumerate(designspace.axes):
    if i >= len(designspace.axes):
      break
    getattr(ax,methods[i][0])([axis.minimum, axis.maximum])
    getattr(ax,methods[i][1])(axis.name)

  return ax

if len(designspace.axes) == 3:
  do_three_axis(designspace)
elif 1 <= len(designspace.axes) <= 2:
  do_one_or_two_axis(designspace,axis_count = len(designspace.axes))

qapp = QApplication(sys.argv)
app.show()
qapp.exec_()
