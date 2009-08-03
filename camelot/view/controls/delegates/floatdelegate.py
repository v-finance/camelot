
from customdelegate import *
from camelot.core.constants import *

class FloatDelegate(CustomDelegate):
  """Custom delegate for float values"""

  editor = editors.FloatEditor
  
  def __init__(self,
               minimum=camelot_minfloat,
               maximum=camelot_maxfloat,
               precision=2,
               editable=True,
               parent=None,
               **kwargs):
    """
:param precision:  The number of digits after the decimal point displayed.  This defaults
to the precision specified in the definition of the Field.     
"""
    CustomDelegate.__init__(self, parent=parent, editable=editable, minimum=minimum, maximum=maximum,
                            precision=precision, **kwargs)
    self.minimum = minimum
    self.maximum = maximum
    self.precision = precision
    self.editable = editable

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toDouble()[0]
    editor.set_value(value)
