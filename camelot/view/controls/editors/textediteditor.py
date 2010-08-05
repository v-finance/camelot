from wideeditor import WideEditor
from customeditor import AbstractCustomEditor, QtGui


class TextEditEditor(QtGui.QTextEdit, AbstractCustomEditor, WideEditor):

    def __init__(self, parent, length=20, editable=True, **kwargs):
        QtGui.QTextEdit.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setReadOnly(not editable)

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        #if value:
        #    self.setText(unicode(value))
        #else:
        #    self.setText('')
        self.setText(unicode(value))
        return value

    def get_value(self):
        val = AbstractCustomEditor.get_value(self)
        if val is not None: # we need to distinguish between None
            return val      # and other falsy values
        return unicode(self.toPlainText())


    def set_enabled(self, editable=True):
        self.setEnabled(editable)
