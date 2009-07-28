
from customdelegate import *

def _paint_not_editable(painter, option, index):
  text = index.model().data(index, Qt.DisplayRole).toString()
  painter.save()
  if (option.state & QtGui.QStyle.State_Selected):
    painter.fillRect(option.rect, option.palette.highlight())
    painter.setPen(option.palette.highlightedText().color())
  else:
    painter.fillRect(option.rect, QtGui.QColor(not_editable_background))
    painter.setPen(QtGui.QColor(not_editable_foreground))
  painter.drawText(option.rect.x()+2,
                   option.rect.y(),
                   option.rect.width()-4,
                   option.rect.height(),
                   Qt.AlignVCenter,
                   text)
  painter.restore()

class PlainTextDelegate(CustomDelegate):
  """Custom delegate for simple string values"""

  editor = editors.TextLineEditor

  def paint(self, painter, option, index):
    if (option.state & QtGui.QStyle.State_Selected):
      QItemDelegate.paint(self, painter, option, index)
    elif not self.editable:
      _paint_not_editable(painter, option, index)
    else:
      QItemDelegate.paint(self, painter, option, index)
