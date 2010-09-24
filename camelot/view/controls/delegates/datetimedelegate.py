
from customdelegate import CustomDelegate, DocumentationMetaclass, ValueLoading
from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

class DateTimeDelegate(CustomDelegate):
  
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.DateTimeEditor
    
    def __init__(self, parent=None, editable=True, **kwargs):
        CustomDelegate.__init__(self, parent, editable=editable, **kwargs)
        locale = QtCore.QLocale()
        self.datetime_format = locale.dateTimeFormat(locale.ShortFormat)
        
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject( index.model().data( index, Qt.EditRole ) )
        
        value_str = u''
        if value not in (None, ValueLoading):
            date_time = QtCore.QDateTime(
                value.year, 
                value.month, 
                value.day,
                value.hour, 
                value.minute, 
                value.second
            )
            value_str = date_time.toString(self.datetime_format)
            
        self.paint_text(painter, option, index, value_str)
        painter.restore()