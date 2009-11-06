from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.core import constants
from camelot.view.proxy import ValueLoading

class CurrencyDelegate(CustomDelegate):
    """Custom delegate for float values"""
  
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.FloatEditor
    
    def __init__(self,
                 minimum=constants.camelot_minfloat,
                 maximum=constants.camelot_maxfloat,
                 precision=2,
                 editable=True,
                 parent=None,
                 prefix="",
                 suffix="",
                 **kwargs):
        """
    :param precision:  The number of digits after the decimal point displayed.  This defaults
    to the precision specified in the definition of the Field.     
    """
        CustomDelegate.__init__(self, parent=parent, editable=editable, minimum=minimum, maximum=maximum,
                                precision=precision, prefix=prefix, suffix=suffix, **kwargs)
        self.minimum = minimum
        self.maximum = maximum
        self.precision = precision
        self.editable = editable
        self.prefix = prefix
        self.suffix = suffix
        
    def setEditorData(self, editor, index):
        value = variant_to_pyobject(index.model().data(index, Qt.EditRole))
        editor.set_value(value)
    
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject(index.model().data(index, Qt.EditRole))
        if value in (None, ValueLoading):
            value = 0.0
        rect = option.rect
        rect = QtCore.QRect(rect.left()+3, rect.top()+6, 16, 16)
        
        
        background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
        
        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
            fontColor = QtGui.QColor()
            if self.editable:
                Color = option.palette.highlightedText().color()
                fontColor.setRgb(Color.red(), Color.green(), Color.blue())
            else:
                fontColor.setRgb(130,130,130)
        else:
            if self.editable:
                painter.fillRect(option.rect, background_color)
                fontColor = QtGui.QColor()
                fontColor.setRgb(0,0,0)
            else:
                painter.fillRect(option.rect, option.palette.window())
                fontColor = QtGui.QColor()
                fontColor.setRgb(130,130,130)
                
        value_str_formatted  = QtCore.QString("%L1").arg(value,0,'f',2)
        
        painter.setPen(fontColor.toRgb())
        rect = QtCore.QRect(option.rect.left()+23,
                            option.rect.top(),
                            option.rect.width()-23,
                            option.rect.height())
        
        painter.drawText(rect.x()+2,
                         rect.y(),
                         rect.width()-4,
                         rect.height(),
                         Qt.AlignVCenter | Qt.AlignRight,
                         value_str_formatted)
        
        painter.restore()
