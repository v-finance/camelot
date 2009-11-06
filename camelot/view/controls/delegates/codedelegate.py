from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading

class CodeDelegate(CustomDelegate):
  
    __metaclass__ = DocumentationMetaclass
      
    editor = editors.CodeEditor
    
    def __init__(self, parent=None, parts=[], **kwargs):
        CustomDelegate.__init__(self, parent=parent, parts=parts, **kwargs)
        self.parts = parts
    
    def paint(self, painter, option, index):
        painter.save()
        numParts = len(self.parts)
        self.drawBackground(painter, option, index)
        
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
                
          
        rect = option.rect
        rect = QtCore.QRect(rect.left()+3, rect.top()+6, rect.width(), rect.height()-3)
        
        
        if numParts != 0:
            value = variant_to_pyobject(index.model().data(index, Qt.EditRole)) or []
            if value == ValueLoading:
                value = []
            value = '.'.join([unicode(i) for i in value])
            
            
            painter.setPen(fontColor.toRgb())
            
            painter.drawText(rect.x(),
                           rect.y()-4,
                           rect.width()-6,
                           rect.height(),
                           Qt.AlignVCenter | Qt.AlignRight,
                           value)  
            
      
              
            
        
        painter.restore()
      
    
#  def sizeHint(self, option, index):
#    return self._dummy_editor.sizeHint() 
