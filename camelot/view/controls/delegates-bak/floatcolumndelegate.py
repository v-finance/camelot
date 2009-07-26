
from customdelegate import *

class FloatColumnDelegate(CustomDelegate):
  """Custom delegate for float values"""

  editor = editors.FloatEditor
  
  def __init__(self,
               minimum=-1e15,
               maximum=1e15,
               precision=2,
               editable=True,
               parent=None,
               **kwargs):
    """
:param precision:  The number of digits after the decimal point displayed.  This defaults
to the precision specified in the definition of the Field.     
"""
    CustomDelegate.__init__(self, parent=parent, editable=editable)
    self.minimum = minimum
    self.maximum = maximum
    self.precision = precision
    self.editable = editable

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toDouble()[0]
    editor.set_value(value)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(editor.get_value()))
