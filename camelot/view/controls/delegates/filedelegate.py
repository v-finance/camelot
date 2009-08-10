
from customdelegate import *

class FileDelegate(CustomDelegate):
  """Delegate for camelot.types.file fields
 
.. image:: ../_static/file_delegate.png 
"""
  
  editor = editors.FileEditor
  
  def paint(self, painter, option, index):
    self.drawBackground(painter, option, index)
    painter.save()
    if (option.state & QtGui.QStyle.State_Selected):
      painter.fillRect(option.rect, option.palette.highlight())
      painter.setPen(option.palette.highlightedText().color())
    elif not self.editable:
      painter.fillRect(option.rect, QtGui.QColor(not_editable_background))
      painter.setPen(QtGui.QColor(not_editable_foreground))
    value =  index.model().data(index, Qt.EditRole).toPyObject()
    if value:
      
      painter.drawText(option.rect.x()+2,
                       option.rect.y(),
                       option.rect.width()-4,
                       option.rect.height(),
                       Qt.AlignVCenter | Qt.AlignLeft,
                       value.verbose_name)
      
    painter.restore()
