from camelot.view.art import Icon
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.section import Section

class MyApplicationAdmin(ApplicationAdmin):
  
    def get_sections(self):
        from camelot.model.memento import Memento
        from camelot.model.authentication import Person, Organization
        from camelot.model.i18n import Translation
        return [Section('relation',
                        Icon('tango/24x24/apps/system-users.png'),
                        items = [Person, Organization]),
                Section('configuration',
                        Icon('tango/24x24/categories/preferences-system.png'),
                        items = [Memento, Translation])
                ]
