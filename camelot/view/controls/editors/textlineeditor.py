from PyQt4 import QtGui

from customeditor import AbstractCustomEditor

class TextLineEditor(QtGui.QLineEdit, AbstractCustomEditor):

    def __init__(self, parent, length=20, editable=True, **kwargs):
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
      
    def set_enabled(self, editable=True):
        value = self.text()
        self.setEnabled(editable)
        self.setText(value)
