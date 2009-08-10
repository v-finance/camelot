
from customdelegate import *

class BoolDelegate(CustomDelegate):
  """Custom delegate for boolean values"""

  __metaclass__ = DocumentationMetaclass
  
  editor = editors.BoolEditor

  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    checked = index.model().data(index, Qt.EditRole).toBool()
    check_option = QtGui.QStyleOptionButton()
    
    rect = QtCore.QRect(option.rect.left()+40,
                        option.rect.top(),
                        option.rect.width()-23,
                        option.rect.height())
    
    check_option.rect = rect
    check_option.palette = option.palette
    if (option.state & QtGui.QStyle.State_Selected):
      painter.fillRect(option.rect, option.palette.highlight())
    elif not self.editable:
      painter.fillRect(option.rect, QtGui.QColor(not_editable_background))
      
    if checked:
      check_option.state = option.state | QtGui.QStyle.State_On
    else:
      check_option.state = option.state | QtGui.QStyle.State_Off
      
      
      
    QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_CheckBox,
                                           check_option,
                                           painter)
    
    
    painter.restore()


