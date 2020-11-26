import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D


class DraggablePoint:

    # http://stackoverflow.com/questions/21654008/matplotlib-drag-overlapping-points-interactively

    lock = None #  only one can be animated at a time

    def __init__(self, parent, x=0.1, y=0.1, size=0.1, prev=None):
        self.parent = parent
        x_min, x_max = parent.fig.axes[0].get_xlim()
        x_range = x_max-x_min
        y_min, y_max = parent.fig.axes[0].get_ylim()
        y_range = y_max-y_min

        self.point = patches.Ellipse((x, y), size/100*x_range, size/100*y_range, fc='r', alpha=0.5, edgecolor='r', clip_on=False)
        self.x = x
        self.y = y
        parent.fig.axes[0].add_patch(self.point)
        self.press = None
        self.background = None
        self.prev = prev
        self.connect()
        # if another point already exist we draw a line
        if self.prev:
            self.setLine()

    def setLine(self):
        line_x = [self.prev.x, self.x]
        line_y = [self.prev.y, self.y]
        print("Drawing line",line_x, line_y)
        self.line = Line2D(line_x, line_y, color='r', alpha=0.5, clip_on=False)
        self.parent.fig.axes[0].add_line(self.line)


    def connect(self):

        'connect to all the events we need'

        self.cidpress = self.point.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = self.point.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = self.point.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)


    def on_press(self, event):

        if event.inaxes != self.point.axes: return
        if DraggablePoint.lock is not None: return
        contains, attrd = self.point.contains(event)
        if not contains: return
        self.press = (self.point.center), event.xdata, event.ydata
        DraggablePoint.lock = self
        self.parent.setLastSelected(self)

        # draw everything but the selected rectangle and store the pixel buffer
        canvas = self.point.figure.canvas
        axes = self.point.axes
        self.point.set_animated(True)

        # TODO also the line of some other points needs to be released
        point_number =  self.parent.list_points.index(self)

        if self == self.parent.list_points[0]:
            self.parent.list_points[1].line.set_animated(True)
        elif self == self.parent.list_points[-1]:
            self.line.set_animated(True)
        else:
            self.line.set_animated(True)
            self.parent.list_points[point_number+1].line.set_animated(True)




        canvas.draw()
        self.background = canvas.copy_from_bbox(self.point.axes.bbox)

        # now redraw just the rectangle
        axes.draw_artist(self.point)

        # and blit just the redrawn area
        canvas.blit(axes.bbox)


    def on_motion(self, event):

        if DraggablePoint.lock is not self:
            return
        if event.inaxes != self.point.axes: return
        self.point.center, xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        self.point.center = (self.point.center[0]+dx, self.point.center[1]+dy)

        canvas = self.point.figure.canvas
        axes = self.point.axes
        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current rectangle
        axes.draw_artist(self.point)

        point_number =  self.parent.list_points.index(self)
        self.x = self.point.center[0]
        self.y = self.point.center[1]





        # We check if the point is A or B
        if self == self.parent.list_points[0]:
            # or we draw the other line of the point
            self.parent.list_points[1].line.set_animated(True)
            axes.draw_artist(self.parent.list_points[1].line)

        elif self == self.parent.list_points[-1]:
            # we draw the line of the point
            axes.draw_artist(self.line)

        else:
            # we draw the line of the point
            axes.draw_artist(self.line)
            #self.parent.list_points[point_number+1].line.set_animated(True)
            axes.draw_artist(self.parent.list_points[point_number+1].line)




        if self == self.parent.list_points[0]:
            # The first point is especial because it has no line
            line_x = [self.x, self.parent.list_points[1].x]
            line_y = [self.y, self.parent.list_points[1].y]
            # this is were the line is updated
            self.parent.list_points[1].line.set_data(line_x, line_y)

        elif self == self.parent.list_points[-1]:
            line_x = [self.parent.list_points[-2].x, self.x]
            line_y = [self.parent.list_points[-2].y, self.y]
            self.line.set_data(line_x, line_y)
        else:
            # The first point is especial because it has no line
            line_x = [self.x, self.parent.list_points[point_number+1].x]
            line_y = [self.y, self.parent.list_points[point_number+1].y]
            # this is were the line is updated
            self.parent.list_points[point_number+1].line.set_data(line_x, line_y)

            line_x = [self.parent.list_points[point_number-1].x, self.x]
            line_y = [self.parent.list_points[point_number-1].y, self.y]
            self.line.set_data(line_x, line_y)

        # blit just the redrawn area
        canvas.blit(axes.bbox)
        self.parent.selectionMoved.emit()


    def on_release(self, event):

        'on release we reset the press data'
        if DraggablePoint.lock is not self:
            return

        self.press = None
        DraggablePoint.lock = None

        # turn off the rect animation property and reset the background
        self.point.set_animated(False)

        point_number =  self.parent.list_points.index(self)

        if self == self.parent.list_points[0]:
            self.parent.list_points[1].line.set_animated(False)
        elif self == self.parent.list_points[-1]:
            self.line.set_animated(False)
        else:
            self.line.set_animated(False)
            self.parent.list_points[point_number+1].line.set_animated(False)


        self.background = None

        # redraw the full figure
        self.point.figure.canvas.draw()

        self.x = self.point.center[0]
        self.y = self.point.center[1]
        self.parent.toMap()

    def disconnect(self):

        'disconnect all the stored connection ids'

        self.point.figure.canvas.mpl_disconnect(self.cidpress)
        self.point.figure.canvas.mpl_disconnect(self.cidrelease)
        self.point.figure.canvas.mpl_disconnect(self.cidmotion)
