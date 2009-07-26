
from customeditor import *
from choiceseditor import ChoicesEditor

class OneToManyChoicesEditor(ChoicesEditor):
  
  def __init__(self, parent, editable=True, target=None, **kwargs):
    ChoicesEditor.__init__(self, parent, editable, **kwargs)
    assert target!=None
    
    def get_choices():
      return [(o, unicode(o)) for o in target.query.all()]

    from camelot.view.model_thread import get_model_thread
    get_model_thread().post(get_choices, self.set_choices) 
