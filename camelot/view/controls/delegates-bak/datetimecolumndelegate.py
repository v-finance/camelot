
from customdelegate import *

class DateTimeColumnDelegate(CustomDelegate):
  
  editor = editors.DateTimeEditor
  
  def __init__(self, parent, editable, **kwargs):
    CustomDelegate.__init__(self, parent, editable=editable, **kwargs)
    self._dummy_editor = self.editor(parent, editable=editable, **kwargs)
    
  def sizeHint(self, option, index):
    return self._dummy_editor.sizeHint()
