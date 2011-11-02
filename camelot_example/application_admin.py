from camelot.view.art import Icon
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.section import Section
from camelot.core.utils import ugettext_lazy as _

class MyApplicationAdmin(ApplicationAdmin):

    name = 'Camelot Video Store'

# begin sections
    def get_sections(self):
        
        from camelot.model.memento import Memento
        from camelot.model.authentication import Person, Organization
        from camelot.model.i18n import Translation
        
        from camelot_example.model import Movie, Tag, VisitorReport
        from camelot_example.view import VisitorsPerDirector
# begin import action
        from camelot_example.importer import ImportCovers
# end import action
        
        return [
# begin section with action
                Section( _('Movies'),
                         self,
                         Icon('tango/22x22/mimetypes/x-office-presentation.png'),
                         items = [ Movie, 
                                   Tag, 
                                   VisitorReport, 
                                   VisitorsPerDirector,
                                   ImportCovers() ]),
# end section with action
                Section( _('Relation'),
                         self,
                         Icon('tango/22x22/apps/system-users.png'),
                         items = [ Person, 
                                   Organization ]),
                Section( _('Configuration'),
                         self,
                         Icon('tango/22x22/categories/preferences-system.png'),
                         items = [ Memento, 
                                   Translation ])
                ]
# end sections

# begin actions
    def get_actions(self):
        from camelot.admin.action import OpenNewView
        from camelot_example.model import Movie
        
        new_movie_action = OpenNewView( self.get_related_admin(Movie) )
        new_movie_action.icon = Icon('tango/22x22/mimetypes/x-office-presentation.png')

        return [new_movie_action]
# end actions