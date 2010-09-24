from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core import constants
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading

class FloatDelegate( CustomDelegate ):
    """Custom delegate for float values"""

    __metaclass__ = DocumentationMetaclass

    editor = editors.FloatEditor

    def __init__( self,
                 minimum = constants.camelot_minfloat,
                 maximum = constants.camelot_maxfloat,
                 precision = 2,
                 parent = None,
                 unicode_format = None,
                 **kwargs ):
        """
    :param precision:  The number of digits after the decimal point displayed.  This defaults
    to the precision specified in the definition of the Field.     
    """
        CustomDelegate.__init__( self, parent = parent,
                                precision = precision, **kwargs )
        self.precision = precision
        self.unicode_format = unicode_format

    def paint( self, painter, option, index ):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject(index.model().data(index, Qt.EditRole))
          
        if value in (None, ValueLoading):
            value_str = ''
        else:
            value_str = QtCore.QString("%L1").arg(float(value),0,'f',self.precision)

        if self.unicode_format is not None:
            value_str = self.unicode_format(value)
        
        self.paint_text( painter, option, index, value_str )
        painter.restore()
