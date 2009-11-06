import datetime

from PyQt4 import QtGui

from customeditor import AbstractCustomEditor
from camelot.core import constants

class TimeEditor(QtGui.QTimeEdit, AbstractCustomEditor):
  
    def __init__(self,
                 parent,
                 editable=True,
                 format=constants.camelot_time_format,
                 **kwargs):
        QtGui.QTimeEdit.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setDisplayFormat(format)
        self.setEnabled(editable)
        
    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value:
            self.setTime(value)
        else:
            self.setTime(self.minimumTime())
            
    def get_value(self):
        value = self.time()
        value = datetime.time(hour=value.hour(),
                              minute=value.minute(),
                              second=value.second())
        return AbstractCustomEditor.get_value(self) or value
      
    def set_enabled(self, editable=True):
        self.setEnabled(editable)
