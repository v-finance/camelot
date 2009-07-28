
from customdelegate import *

class ColorDelegate(CustomDelegate):
  """
.. image:: ../_static/color.png
"""

  editor = editors.ColorEditor
  
  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    if (option.state & QtGui.QStyle.State_Selected):
      pass
    elif not self.editable:
      painter.fillRect(option.rect, QtGui.QColor(not_editable_background))
    color = index.model().data(index, Qt.EditRole).toPyObject()
    if color:
      pixmap = QtGui.QPixmap(16, 16)
      qcolor = QtGui.QColor()
      qcolor.setRgb(*color)
      pixmap.fill(qcolor)
      QtGui.QApplication.style().drawItemPixmap(painter,
                                                option.rect,
                                                Qt.AlignVCenter,
                                                pixmap)
    painter.restore()
