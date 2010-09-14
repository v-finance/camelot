import datetime

from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core.utils import create_constant_function, variant_to_pyobject
from camelot.view.proxy import ValueLoading

class TimeDelegate(CustomDelegate):
 
    __metaclass__ = DocumentationMetaclass
   
    editor = editors.TimeEditor
      
    def __init__(self, parent=None, editable=True, **kwargs):
        CustomDelegate.__init__(self, parent, editable)
        locale = QtCore.QLocale()
        self.time_format = locale.timeFormat(locale.ShortFormat)
        
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject( index.model().data( index, Qt.EditRole ) )
        
        value_str = u''
        if value not in (None, ValueLoading):
            time = QtCore.QTime(value.hour, value.minute, value.second)
            value_str = time.toString(self.time_format)

        self.paint_text(painter, option, index, value_str)
        painter.restore()
      
    def setModelData(self, editor, model, index):
        value = editor.time()
        t = datetime.time(hour=value.hour(),
                          minute=value.minute(),
                          second=value.second())
        model.setData(index, create_constant_function(t))
