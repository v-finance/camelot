
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors

class BoolDelegate(CustomDelegate):
    """Custom delegate for boolean values"""
  
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.BoolEditor
  
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        checked = index.model().data(index, Qt.EditRole).toBool()
        
        background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
        
        check_option = QtGui.QStyleOptionButton()
        
        rect = QtCore.QRect(option.rect.left(),
                            option.rect.top(),
                            option.rect.width(),
                            option.rect.height())
        
        check_option.rect = rect
        check_option.palette = option.palette
        if (option.state & QtGui.QStyle.State_Selected):
            painter.fillRect(option.rect, option.palette.highlight())
        elif not self.editable:
            painter.fillRect(option.rect, option.palette.window())
        else:
            painter.fillRect(option.rect, background_color)
            
        if checked:
            check_option.state = option.state | QtGui.QStyle.State_On
        else:
            check_option.state = option.state | QtGui.QStyle.State_Off
            
            
            
        QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_CheckBox,
                                               check_option,
                                               painter)
        
        
        painter.restore()
    
    
