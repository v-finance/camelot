from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass, not_editable_background, not_editable_foreground
from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading

class FileDelegate(CustomDelegate):
    """Delegate for camelot.types.file fields
   
  .. image:: ../_static/file_delegate.png 
  """
    
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.FileEditor
    
    def paint(self, painter, option, index, background_color=QtGui.QColor("white")):
        painter.save()
        self.drawBackground(painter, option, index)
        if (option.state & QtGui.QStyle.State_Selected):
            painter.fillRect(option.rect, option.palette.highlight())
            painter.setPen(option.palette.highlightedText().color())
        elif not self.editable:
            painter.fillRect(option.rect, QtGui.QColor(not_editable_background))
            painter.setPen(QtGui.QColor(not_editable_foreground))
        else:
            painter.fillRect(option.rect, background_color)
        value =  variant_to_pyobject(index.model().data(index, Qt.EditRole))
        if value not in (None, ValueLoading):
          
            painter.drawText(option.rect.x()+2,
                             option.rect.y(),
                             option.rect.width()-4,
                             option.rect.height(),
                             Qt.AlignVCenter | Qt.AlignLeft,
                             value.verbose_name)
            
        painter.restore()
