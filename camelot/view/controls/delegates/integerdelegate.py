from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.core import constants
from camelot.view.proxy import ValueLoading

class IntegerDelegate(CustomDelegate):
    """Custom delegate for integer values"""
  
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.IntegerEditor
  
    def __init__(self,
                 minimum=constants.camelot_minint,
                 maximum=constants.camelot_maxint,
                 parent=None,
                 unicode_format = None,
                 **kwargs):
  
        CustomDelegate.__init__(self, parent=parent, minimum=minimum, maximum=maximum, **kwargs)
        self.minimum = minimum
        self.maximum = maximum
        self.unicode_format = unicode_format
        
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject(index.model().data(index, Qt.EditRole))
          
        if value in (None, ValueLoading):
            value_str = ''
        else:
            value_str = QtCore.QString("%L1").arg( int(value) )

        if self.unicode_format is not None:
            value_str = self.unicode_format(value)
        
        self.paint_text( painter, option, index, value_str )
        painter.restore()
    

