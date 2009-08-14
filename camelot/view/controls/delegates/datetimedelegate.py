
from customdelegate import *

class DateTimeDelegate(CustomDelegate):
  
  __metaclass__ = DocumentationMetaclass
  
  editor = editors.DateTimeEditor
  
  def __init__(self, parent, editable, **kwargs):
    CustomDelegate.__init__(self, parent, editable=editable, **kwargs)
    
    locale = QtCore.QLocale()
    
    self.dateTime_format = locale.dateTimeFormat(locale.ShortFormat)

    
    
    #self._dummy_editor = self.editor(parent, editable=editable, **kwargs)
    
    
  def paint(self, painter, option, index):
    painter.save()
    
    self.drawBackground(painter, option, index)
    
    
    dateTime = index.model().data(index, Qt.EditRole).toDateTime()
  
    
    formattedDateTime = dateTime.toString(self.dateTime_format)
    
    
    editor = editors.DateTimeEditor( None, 
                                 self.editable )
    
    #print formattedDateTime
    
    rect = option.rect
    rect = QtCore.QRect(rect.left()+3, rect.top()+6, 16, 16)
    
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
        
        
    painter.setPen(fontColor.toRgb())
    rect = QtCore.QRect(option.rect.left(),
                        option.rect.top(),
                        option.rect.width(),
                        option.rect.height())
    
    painter.drawText(rect.x()+2,
                     rect.y(),
                     rect.width()-4,
                     rect.height(),
                     Qt.AlignVCenter | Qt.AlignRight,
                     str(formattedDateTime))
    
    #print str(formattedDateTime)
    
    
    painter.restore()
    
    
    

