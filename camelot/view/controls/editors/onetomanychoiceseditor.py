
from camelot.view.model_thread import post
from choiceseditor import ChoicesEditor

class OneToManyChoicesEditor(ChoicesEditor):
  
    def __init__(self, parent, editable=True, target=None, **kwargs):
        ChoicesEditor.__init__(self, parent, editable, **kwargs)
        assert target!=None
        
        def get_choices():
            return [(o, unicode(o)) for o in target.query.all()]
      
        post(get_choices, self.set_choices) 
