
from customdelegate import *

class DateDelegate(CustomDelegate):
  """Custom delegate for date values"""

  __metaclass__ = DocumentationMetaclass
  
  editor = editors.DateEditor
  
  
  def __init__(self, parent=None, editable=True, **kwargs):
    CustomDelegate.__init__(self, parent, editable)
    
    locale = QtCore.QLocale()
    
    self.date_format = locale.dateFormat(locale.ShortFormat)

  def paint(self, painter, option, index):
    
    
    painter.save()
    self.drawBackground(painter, option, index)
    
    dateObj = variant_to_pyobject(index.model().data(index, Qt.EditRole))
    if dateObj and dateObj != camelot.view.proxy.ValueLoading:
      formattedDate = QtCore.QDate(dateObj).toString(self.date_format)
    else:
      formattedDate = ""

    editor = editors.DateEditor( None, 
                                 self.editable )
    
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
    rect = QtCore.QRect(option.rect.left()+23,
                        option.rect.top(),
                        option.rect.width()-23,
                        option.rect.height())
    painter.drawText(rect.x()+2,
                     rect.y(),
                     rect.width()-4,
                     rect.height(),
                     Qt.AlignVCenter | Qt.AlignRight,
                     str(formattedDate))
    painter.restore()
    
    
    
    
#    myoption = QtGui.QStyleOptionViewItem(option)
#    myoption.displayAlignment |= Qt.AlignRight | Qt.AlignVCenter
#    QtGui.QItemDelegate.paint(self, painter, myoption, index)

  def sizeHint(self, option, index):
    return editors.DateEditor().sizeHint()
