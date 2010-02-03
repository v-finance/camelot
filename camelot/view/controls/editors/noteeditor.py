from PyQt4 import QtGui, QtCore

from customeditor import AbstractCustomEditor

class NoteEditor(QtGui.QLabel, AbstractCustomEditor):
    """An editor that behaves like a note, the editor hides itself when
    there is no text to display"""
    
    def __init__(self, parent, **kwargs):
        QtGui.QLabel.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setTextFormat(QtCore.Qt.RichText)
        from camelot.view.art import ColorScheme
        style = """
        QLabel {
          margin: 0px;
          padding: 3px;
          border: 1px solid black;
          color: black;
          background-color: %s;
        }
        """%(ColorScheme.yellow_1.name())
        self.setStyleSheet( style );
    
        
    def set_value(self, value):
        value = super(NoteEditor, self).set_value(value)
        self.setVisible(value!=None)
        if value:
            self.setText(unicode(value))
    


