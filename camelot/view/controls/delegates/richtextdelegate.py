from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.view.proxy import ValueLoading

class RichTextDelegate(CustomDelegate):
    """Custom delegate for rich text (HTML) string values
  """
  
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.RichTextEditor
    
    def __init__(self, parent=None, editable=True, **kwargs):
        CustomDelegate.__init__(self, parent, editable)
        self.editable = editable
        self._height = self._height * 10
        self._width = self._width * 3
    
    def paint(self, painter, option, index):
        from camelot.view.utils import text_from_richtext
          
        painter.save()
        self.drawBackground(painter, option, index)
        value = unicode(index.model().data(index, Qt.EditRole).toString())

        value_str = u''
        if value not in (None, ValueLoading):
            value_str = text_from_richtext(value, newlines=False)[:256]

        self.paint_text(painter, option, index, value_str)
        painter.restore()        
    
