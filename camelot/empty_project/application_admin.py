from camelot.view.application_admin import ApplicationAdmin
from camelot.view.art import TangoIcon

class MyApplicationAdmin(ApplicationAdmin):
  
  def __init__(self):
    super(MyApplicationAdmin, self).__init__([
      ('relations',
       ('Relations',
        TangoIcon('system-users', folder='apps', size='24x24').fullpath())),
      ('configuration',
        ('Configuration',
         TangoIcon('preferences-system', folder='categories', size='24x24'))),
    ])

    from camelot.model.memento import Memento
    from camelot.model.authentication import Person, Organization
    from camelot.model.i18n import Translation
    self.register(Memento, Memento.Admin)
    self.register(Person, Person.Admin)
    self.register(Organization, Organization.Admin)
    self.register(Translation, Translation.Admin)
