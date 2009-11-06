from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
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
                 unicode_format=None,
                 **kwargs):
        CustomDelegate.__init__(self,
                                parent=parent,
                                editable=editable,
                                minimum=minimum,
                                maximum=maximum,
                                precision=precision,
                                unicode_format=unicode_format,
                                **kwargs)
        self.minimum = minimum
        self.maximum = maximum
        self.precision = precision
        self.editable = editable
        self.unicode_format = unicode_format
        
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = index.model().data(index, Qt.EditRole).toDouble()[0]
        color = index.model().data(index, Qt.BackgroundRole)
        background_color = QtGui.QColor(color)
        fontColor = QtGui.QColor()
        
        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            if not self.editable:
                painter.fillRect(option.rect, option.palette.window())
            else:
                painter.fillRect(option.rect, background_color)
          
          
          
          
            
      
          
        if value >= 0:
            if value == 0:
                QtGui.QIcon(Icon('tango/16x16/actions/zero.png').getQPixmap()).paint(painter, option.rect.top(), option.rect.left()+1, option.rect.height(), option.rect.height(), Qt.AlignVCenter)
                #QtGui.QApplication.style().drawItemPixmap(painter, rect, 1, icon)
                fontColor.setRgb(0, 0, 0)
            else:
                QtGui.QIcon(Icon('tango/16x16/actions/go-up.png').getQPixmap()).paint(painter, option.rect.left(), option.rect.top()+1, option.rect.height(), option.rect.height(), Qt.AlignVCenter)
                #QtGui.QApplication.style().drawItemPixmap(painter, rect, 1, icon)
                fontColor.setRgb(0, 255, 0)
        else:
            QtGui.QIcon(Icon('tango/16x16/actions/go-down-red.png').getQPixmap()).paint(painter, option.rect.left(), option.rect.top()+1, option.rect.height(), option.rect.height(), Qt.AlignVCenter)
#      QtGui.QApplication.style().drawItemPixmap(painter, rect, 1, icon)
            fontColor.setRgb(255, 0, 0)
      
        value_str = '%.*f'%(self.precision, value)
        if self.unicode_format != None:
            value_str = self.unicode_format(value)
            
            
            
        
    
    
    
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
