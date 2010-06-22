
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core.utils import ugettext as _

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
    
class TextBoolDelegate(CustomDelegate):

    editor = editors.TextBoolEditor
    def __init__(self, parent=None, editable=True, yes='Yes', no='No', color_yes=None, color_no=None, **kwargs):
        CustomDelegate.__init__(self, parent, editable, **kwargs)
        self.yes = yes
        self.no = no
        self.color_no = color_no
        self.color_yes = color_yes

    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
    
        background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
        rect = option.rect
        
        value = index.model().data(index, Qt.EditRole).toBool()
        font_color = QtGui.QColor()
        if value:
            text = self.yes
            if self.color_yes:
                color = self.color_yes
        else:
            text = self.no
            if self.color_no:
                color = self.color_no
        font_color.setRgb(color.red(), color.green(), color.blue()) 
        if self.editable:
            painter.fillRect(option.rect, background_color)
        else:
            painter.fillRect(option.rect, option.palette.window())
              
        painter.setPen(font_color.toRgb())
        painter.drawText(
            rect.x() + 2,
            rect.y(),
            rect.width() - 4,
            rect.height(),
            Qt.AlignVCenter | Qt.AlignLeft,
            _(text)
        )
        painter.restore()