
from customeditor import *

class TextEditEditor(QtGui.QTextEdit, AbstractCustomEditor):

  def __init__(self, parent, length=20, editable=True, **kwargs):
    QtGui.QTextEdit.__init__(self, parent)
    AbstractCustomEditor.__init__(self)

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
