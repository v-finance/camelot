from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors

class TextEditDelegate(CustomDelegate):
    """Custom delegate for simple string values"""
  
    __metaclass__ = DocumentationMetaclass
  
    editor = editors.TextEditEditor
      
    def __init__(self, parent=None, editable=True, **kwargs):
        CustomDelegate.__init__(self, parent, editable)
        
        self.editable = editable
    
    
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject( index.model().data( index, Qt.EditRole ) )
        
        value_str = u''
        if value not in (None, ValueLoading):
            value_str = ugettext(value)

        self.paint_text(painter, option, index, value_str)
        painter.restore()
