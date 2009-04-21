from camelot.view.art import Icon
from camelot.view.application_admin import ApplicationAdmin

class MyApplicationAdmin(ApplicationAdmin):
  
  def __init__(self):
    icon_relations = Icon('tango/24x24/apps/system-users.png').fullpath()
    icon_config = Icon('tango/24x24/categories/preferences-system.png').fullpath()

    super(MyApplicationAdmin, self).__init__([
      ('relations', ('Relations', icon_relations)),
      ('configuration', ('Configuration', icon_config)),
    ])

    from camelot.model.memento import Memento
    from camelot.model.authentication import Person, Organization
    from camelot.model.i18n import Translation
    self.register(Memento, Memento.Admin)
    self.register(Person, Person.Admin)
    self.register(Organization, Organization.Admin)
    self.register(Translation, Translation.Admin)
