from camelot.view.model_thread import post
from choiceseditor import ChoicesEditor

class OneToManyChoicesEditor(ChoicesEditor):
  
    def __init__(self, parent, target=None, **kwargs):
        super(OneToManyChoicesEditor, self).__init__(parent, **kwargs)
        assert target!=None
        self._target = target
        post(self.get_choices, self.set_choices)

    def get_choices(self):
            return [(o, unicode(o)) for o in self._target.query.all()]
        
    def set_field_attributes(self, editable=True, **kwargs):
        """Makes sure choices are not reset when changing the
        field attributes"""
        self.setEnabled(editable!=False)