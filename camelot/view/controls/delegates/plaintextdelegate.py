from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading

class PlainTextDelegate(CustomDelegate):
    """Custom delegate for simple string values"""
  
    __metaclass__ = DocumentationMetaclass
  
    editor = editors.TextLineEditor
      
    def __init__(self, parent=None, length=20, editable=True, **kwargs):
        CustomDelegate.__init__(self, parent, editable, length=length, **kwargs)
        self.editable = editable
        self.length = length
    
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        text = variant_to_pyobject(index.model().data(index, Qt.EditRole)) 
        
        background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))  
    
        rect = option.rect
        rect = QtCore.QRect(rect.left(), rect.top(), rect.width(), rect.height())  
    
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
      
        if text!=ValueLoading:
            text = text or ''
        else:
            text = ''
            
        painter.setPen(fontColor.toRgb())
        rect = QtCore.QRect(option.rect.left(),
                            option.rect.top(),
                            option.rect.width(),
                            option.rect.height())
        painter.drawText(rect.x() + 2,
                         rect.y(),
                         rect.width() - 4,
                         rect.height(),
                         Qt.AlignVCenter | Qt.AlignLeft,
                         unicode(text))
        painter.restore()
