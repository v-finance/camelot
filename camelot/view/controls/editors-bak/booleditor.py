
from customeditor import *

class BoolEditor(QtGui.QCheckBox, AbstractCustomEditor):
  
  def __init__(self, parent, editable=True, **kwargs):
    QtGui.QCheckBox.__init__(self, parent)
    AbstractCustomEditor.__init__(self)
    self.setEnabled(editable)
    
  def set_value(self, value):
    value = AbstractCustomEditor.set_value(self, value)
    if value:
      self.setChecked(True)
    else:
      self.setChecked(False)
      
  def get_value(self):
    return AbstractCustomEditor.get_value(self) or self.isChecked()
