from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customeditor import CustomEditor
import re

class CodeEditor(CustomEditor):
  
    def __init__(self, parent=None, parts=['99','AA'], editable=True, **kwargs):
        CustomEditor.__init__(self, parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.parts = parts
        self.part_editors = []
        layout = QtGui.QHBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft)
        for part in parts:
            part = re.sub('\W*', '', part)
            part_length = len(part)
            editor = QtGui.QLineEdit()
            editor.setInputMask(part)
            if not editable:
                editor.setEnabled(False)
            space_width = editor.fontMetrics().size(Qt.TextSingleLine, 'A').width()
            editor.setMaximumWidth(space_width*(part_length+1))
            editor.installEventFilter(self)
            self.part_editors.append(editor)
            layout.addWidget(editor)
            self.connect(editor,
                         QtCore.SIGNAL('editingFinished()'),
                         self.editingFinished)
      
        self.setLayout(layout)
        self.setAutoFillBackground(True)
    
    def editingFinished(self):
        self.emit(QtCore.SIGNAL('editingFinished()'))
        
      
    def set_enabled(self, editable=True):
        for editor in self.part_editors:
            value = editor.text()
            editor.setEnabled(editable)
            editor.setText(value)
      
    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value:
            for part_editor, part in zip(self.part_editors, value):
                part_editor.setText(unicode(part))
        else:
            for part_editor in self.part_editors:
                part_editor.setText(u'')
        
    def get_value(self):
        value = []
        for part in self.part_editors:
            value.append(unicode(part.text()))
        return CustomEditor.get_value(self) or value
