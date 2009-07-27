
from customdelegate import *

class CodeDelegate(CustomDelegate):
  
  editor = editors.CodeEditor
  
  def __init__(self, parent=None, parts=[], **kwargs):
    CustomDelegate.__init__(self, parent=parent, parts=parts, **kwargs)
    self._dummy_editor = editors.CodeEditor(parent=None, parts=parts)

  def sizeHint(self, option, index):
    return self._dummy_editor.sizeHint() 
