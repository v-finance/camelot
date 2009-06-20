from camelot.view.art import Icon
from camelot.view.application_admin import ApplicationAdmin

class MyApplicationAdmin(ApplicationAdmin):
  
  name = 'Camelot Video Store'
  
  def __init__(self):
    icon_relations = Icon('tango/24x24/apps/system-users.png').fullpath()
    icon_config = Icon('tango/24x24/categories/preferences-system.png').fullpath()
    icon_movies = Icon('tango/24x24/mimetypes/x-office-presentation.png').fullpath()

    super(MyApplicationAdmin, self).__init__([
      ('movies', ('Movies', icon_movies)),
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
    from example.model import Movie, Tag
    self.register(Movie, Movie.Admin)
    self.register(Tag, Tag.Admin)
