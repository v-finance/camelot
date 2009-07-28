
from customeditor import *

class TextLineEditor(QtGui.QLineEdit, AbstractCustomEditor):
 
  def __init__(self, parent, length, editable=True, **kwargs):
    QtGui.QLineEdit.__init__(self, parent)
    AbstractCustomEditor.__init__(self)
    if length:
      self.setMaxLength(length)
    if not editable:
      self.setEnabled(False)
    
  def set_value(self, value):
    value = AbstractCustomEditor.set_value(self, value)
    if value:
      self.setText(unicode(value))
    else:
      self.setText('')
      
  def get_value(self):
    return AbstractCustomEditor.get_value(self) or unicode(self.text())
