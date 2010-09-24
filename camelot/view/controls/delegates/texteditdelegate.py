from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.view.proxy import ValueLoading
from camelot.core.utils import ugettext, variant_to_pyobject

class TextEditDelegate(CustomDelegate):
    """Custom delegate for simple string values"""
  
    __metaclass__ = DocumentationMetaclass
  
    editor = editors.TextEditEditor
      
    def __init__(self, parent=None, **kwargs):
        CustomDelegate.__init__(self, parent, **kwargs)
    
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject( index.model().data( index, Qt.EditRole ) )
        
        value_str = u''
        if value not in (None, ValueLoading):
            value_str = ugettext(value)

        self.paint_text(painter, option, index, value_str)
        painter.restore()
