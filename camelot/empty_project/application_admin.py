from camelot.view.application_admin import ApplicationAdmin
from camelot.view import art

class MyApplicationAdmin(ApplicationAdmin):
  
  def __init__(self):
    super(MyApplicationAdmin, self).__init__([('relations', ('Relations', art.icon24('apps/system-users'))),
                                              ('configuration',('Configuration', art.icon24('categories/preferences-system'))),]
                                              )
    from camelot.model.memento import Memento
    from camelot.model.authentication import Person, Organization
    from camelot.model.i18n import Translation
    self.register(Memento, Memento.Admin)
    self.register(Person, Person.Admin)
    self.register(Organization, Organization.Admin)
    self.register(Translation, Translation.Admin)

  def getName(self):
    return u'Probis Partnerplan'

  def getAbout(self):
    return """<b>Probis Partnerplan</b><br/>
               <p>
              Copyright &copy; 2009 Probis.
              All rights reserved.
              </p>"""

