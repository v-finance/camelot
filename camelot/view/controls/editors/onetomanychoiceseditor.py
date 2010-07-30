
from camelot.view.model_thread import post
from choiceseditor import ChoicesEditor

class OneToManyChoicesEditor(ChoicesEditor):
  
    def __init__(self, parent, target=None, **kwargs):
        ChoicesEditor.__init__(self, parent, **kwargs)
        assert target!=None
        
        def get_choices():
            return [(o, unicode(o)) for o in target.query.all()]
      
        post(get_choices, self.set_choices)

    def set_field_attributes(self, editable=True, **kwargs):
        """Makes sure choices are not reset when changing the
        field attributes"""
        self.setEnabled(editable!=False)