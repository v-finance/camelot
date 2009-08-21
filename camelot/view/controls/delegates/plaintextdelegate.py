
from customdelegate import *


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
          fontColor = QtGui.QColor()
          fontColor.setRgb(0,0,0)
        else:
          painter.fillRect(option.rect, option.palette.window())
          fontColor = QtGui.QColor()
          fontColor.setRgb(130,130,130)

    text = text or ''
      
    painter.setPen(fontColor.toRgb())
    rect = QtCore.QRect(option.rect.left(),
                        option.rect.top(),
                        option.rect.width(),
                        option.rect.height())
    painter.drawText(rect.x(),
                     rect.y(),
                     rect.width(),
                     rect.height(),
                     Qt.AlignVCenter | Qt.AlignLeft,
                     unicode(text))
    painter.restore()
