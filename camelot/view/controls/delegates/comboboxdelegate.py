
from customdelegate import *

class ComboBoxDelegate(CustomDelegate):
  
  __metaclass__ = DocumentationMetaclass

  editor = editors.ChoicesEditor
  
  def __init__(self, parent, choices, editable=True, **kwargs):
    CustomDelegate.__init__(self, parent, editable=editable, **kwargs)
    self.choices = choices
              
  def setEditorData(self, editor, index):
    value = index.data(Qt.EditRole).toPyObject()
    
    def create_choices_getter(model, row):
      
      def choices_getter():
        return list(self.choices(model._get_object(row)))
      
      return choices_getter
    
    editor.set_value(value)
    from camelot.view.model_thread import get_model_thread
    get_model_thread().post(create_choices_getter(index.model(),
                                                  index.row()),
                                                  editor.set_choices)
