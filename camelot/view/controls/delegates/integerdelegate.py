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
        field_attributes = variant_to_pyobject( index.model().data( index, Qt.UserRole ) )
        
        editable, prefix, suffix, background_color = True, '', '', None
        if field_attributes != ValueLoading:
            editable = field_attributes.get( 'editable', True )
            prefix = field_attributes.get( 'prefix', '' )
            suffix = field_attributes.get( 'suffix', '' )
            background_color = field_attributes.get( 'background_color', None )

        background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
        
        rect = option.rect
        rect = QtCore.QRect(rect.left()+3, rect.top()+6, 16, 16)
        #fontColor = QtGui.QColor()
        
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
          
        if value in (None, ValueLoading):
            value_str = ''
        else:
            value_str = QtCore.QString("%L1").arg( int(value) )

        if self.unicode_format is not None:
            value_str = self.unicode_format(value)

        value_str = unicode( prefix ) + u' ' + unicode( value_str ) + u' ' + unicode( suffix )
        value_str = value_str.strip()
        #fontColor = fontColor.darker()
        
    
    
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
                         value_str)
        painter.restore()
    
#    def setEditorData(self, editor, index):
#        value = index.model().data(index, Qt.EditRole).toInt()[0]
#        editor.set_value(value)
