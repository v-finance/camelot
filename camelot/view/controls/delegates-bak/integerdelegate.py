
from customdelegate import *

class IntegerDelegate(CustomDelegate):
  """Custom delegate for integer values"""

  editor = editors.IntegerEditor

  def paint(self, painter, option, index):
    self.drawBackground(painter, option, index)
    painter.save()
    if (option.state & QtGui.QStyle.State_Selected):
      painter.fillRect(option.rect, option.palette.highlight())
      painter.setPen(option.palette.highlightedText().color())
    elif not self.editable:
      painter.fillRect(option.rect, QtGui.Color(_not_editable_background_))
      painter.setPen(QtGui.Color(_not_editable_foreground_))
    value =  index.model().data(index, Qt.DisplayRole).toString()
    painter.drawText(option.rect.x()+2,
                     option.rect.y(),
                     option.rect.width()-4,
                     option.rect.height(),
                     Qt.AlignVCenter | Qt.AlignRight,
                     value)
    painter.restore()

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toInt()[0]
    editor.set_value(value)
