
from customdelegate import *

class TimeDelegate(CustomDelegate):
  
  editor = editors.TimeEditor
  
  def setModelData(self, editor, model, index):
    value = editor.time()
    t = datetime.time(hour=value.hour(),
                      minute=value.minute(),
                      second=value.second())
    model.setData(index, create_constant_function(t))
