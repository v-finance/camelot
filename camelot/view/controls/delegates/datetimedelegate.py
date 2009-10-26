
from customdelegate import CustomDelegate, DocumentationMetaclass, ValueLoading
from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

class DateTimeDelegate(CustomDelegate):
  
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.DateTimeEditor
    
    def __init__(self, parent, editable, **kwargs):
        CustomDelegate.__init__(self, parent, editable=editable, **kwargs)
        locale = QtCore.QLocale()
        self.dateTime_format = locale.dateTimeFormat(locale.ShortFormat)
        
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        dateTime = variant_to_pyobject(index.model().data(index, Qt.EditRole))
        if dateTime not in (ValueLoading, None):
            dateTime = QtCore.QDateTime(dateTime.year, dateTime.month, dateTime.day,
                                        dateTime.hour, dateTime.minute, dateTime.second)
            formattedDateTime = dateTime.toString(self.dateTime_format)
        else:
            formattedDateTime = ''
        background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
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
                painter.fillRect(option.rect, background_color)
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
        painter.restore()
        
        
        
    
