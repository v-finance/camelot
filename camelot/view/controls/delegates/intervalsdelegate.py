
from customdelegate import *

class IntervalsDelegate(QItemDelegate):
  """Custom delegate for visualizing camelot.container.IntervalsContainer
data
"""

  def __init__(self, parent=None, **kwargs):
    QItemDelegate.__init__(self, parent)

  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    intervals = index.model().data(index, Qt.EditRole).toPyObject()
    if intervals and intervals!=ValueLoading:
      rect = option.rect
      xscale = float(rect.width()-4)/(intervals.max-intervals.min)
      xoffset = intervals.min * xscale + rect.x()
      yoffset = rect.y() + rect.height()/2
      for interval in intervals.intervals:
        qcolor = QtGui.QColor()
        qcolor.setRgb(*interval.color)
        pen = QtGui.QPen(qcolor)
        pen.setWidth(3)
        painter.setPen(pen)
        x1, x2 =  xoffset + interval.begin*xscale, xoffset + interval.end*xscale
        painter.drawLine(x1, yoffset, x2, yoffset)
        painter.drawEllipse(x1-1, yoffset-1, 2, 2)
        painter.drawEllipse(x2-1, yoffset-1, 2, 2)
        pen = QtGui.QPen(Qt.white)      
        
    painter.restore()

  def createEditor(self, parent, option, index):
    pass

  def setEditorData(self, editor, index):
    pass

  def setModelData(self, editor, model, index):
    pass
