
from customdelegate import *

class TextEditDelegate(QItemDelegate):
  """Edit plain text with a QTextEdit widget"""
  
  def __init__(self, parent=None, editable=True, **kwargs):
    QItemDelegate.__init__(self, parent)
    self.editable = editable
    
  def createEditor(self, parent, option, index):
    editor = QtGui.QTextEdit(parent)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toString()
    editor.setText(value)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(unicode(editor.toPlainText())))
