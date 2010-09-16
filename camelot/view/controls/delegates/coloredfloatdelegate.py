from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.proxy import ValueLoading

from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.view.art import Icon

class ColoredFloatDelegate(CustomDelegate):
    """Custom delegate for float values, representing them in green when they are
  positive and in red when they are negative.
  """
  
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.ColoredFloatEditor
    
    def __init__(self,
                 parent=None,
                 minimum=-1e15,
                 maximum=1e15,
                 precision=2,
                 editable=True,
                 reverse=False,
                 neutral=False,
                 unicode_format=None,
                 **kwargs):
        CustomDelegate.__init__(self,
                                parent=parent,
                                editable=editable,
                                minimum=minimum,
                                maximum=maximum,
                                reverse=reverse,
                                neutral=neutral,
                                precision=precision,
                                unicode_format=unicode_format,
                                **kwargs)
        self.minimum = minimum
        self.maximum = maximum
        self.precision = precision
        self.editable = editable
        self.reverse = reverse
        self.neutral = neutral
        self.unicode_format = unicode_format
        if not self.reverse:
            if not self.neutral:
                self.icons = {
                    1:QtGui.QIcon(Icon('tango/16x16/actions/go-up.png').getQPixmap()), 
                    -1:QtGui.QIcon(Icon('tango/16x16/actions/go-down-red.png').getQPixmap()),
                    0:QtGui.QIcon(Icon('tango/16x16/actions/zero.png').getQPixmap())
                }    
            else:            
                self.icons = {
                    1:QtGui.QIcon(Icon('tango/16x16/actions/go-up-blue.png').getQPixmap()), 
                    -1:QtGui.QIcon(Icon('tango/16x16/actions/go-down-blue.png').getQPixmap()),
                    0:QtGui.QIcon(Icon('tango/16x16/actions/zero.png').getQPixmap())
                }
        else:
            self.icons = {
                -1:QtGui.QIcon(Icon('tango/16x16/actions/go-up.png').getQPixmap()), 
                1:QtGui.QIcon(Icon('tango/16x16/actions/go-down-red.png').getQPixmap()),
                0:QtGui.QIcon(Icon('tango/16x16/actions/zero.png').getQPixmap())
            }


    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject( index.model().data(index, Qt.EditRole) )
        field_attributes = variant_to_pyobject(index.data(Qt.UserRole))
        fontColor = QtGui.QColor()
        editable, prefix, suffix, background_color, arrow = True, '', '', None, None
        
        if field_attributes != ValueLoading:
            editable = field_attributes.get( 'editable', True )
            prefix = field_attributes.get( 'prefix', '' )
            suffix = field_attributes.get( 'suffix', '' )
            background_color = field_attributes.get( 'background_color', None )
            arrow = field_attributes.get('arrow', None)

        fontColor = QtGui.QColor()
        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            if editable:
                painter.fillRect(option.rect, background_color or option.palette.base())
                fontColor.setRgb(0,0,0)
            else:
                painter.fillRect(option.rect, background_color or option.palette.window())
                fontColor.setRgb(130,130,130)

        if arrow:
            comparator = arrow.y
        else:
            comparator = value
        self.icons[cmp(comparator,0)].paint(painter, option.rect.left(), option.rect.top()+1, option.rect.height(), option.rect.height(), Qt.AlignVCenter)

        value_str = u''
        if value != None and value != ValueLoading:
            if self.unicode_format != None:
                value_str = self.unicode_format(value)
            else:
                value_str = QtCore.QString("%L1").arg(float(value),0,'f',self.precision)
        value_str = unicode( prefix ) + u' ' + unicode( value_str ) + u' ' + unicode( suffix )
       
        fontColor = fontColor.darker()
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
