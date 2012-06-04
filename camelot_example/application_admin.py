from camelot.view.art import Icon
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.section import Section
from camelot.core.utils import ugettext_lazy as _

# begin application admin
class MyApplicationAdmin(ApplicationAdmin):

    name = 'Camelot Video Store'

# begin sections
    def get_sections(self):
        
        from camelot.model.memento import Memento
        from camelot.model.party import ( Person, Organization, 
                                          PartyCategory )
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
                                   Organization,
                                   PartyCategory ]),
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

# end application admin

class MiniApplicationAdmin( MyApplicationAdmin ):
    """An application admin for an application with a reduced number of
    widgets on the main window.
    """

# begin mini admin

    def get_toolbar_actions( self, toolbar_area ):
        from PyQt4.QtCore import Qt
        from camelot.model.party import Person
        from camelot.admin.action import application_action, list_action
        from model import Movie
        
        movies_action = application_action.OpenTableView( self.get_related_admin( Movie ) )
        movies_action.icon = Icon('tango/22x22/mimetypes/x-office-presentation.png')
        persons_action = application_action.OpenTableView( self.get_related_admin( Person ) )
        persons_action.icon = Icon('tango/22x22/apps/system-users.png')
        
        if toolbar_area == Qt.LeftToolBarArea:
            return [ movies_action,
                     persons_action,
                     list_action.OpenNewView(),
                     list_action.OpenFormView(),
                     list_action.DeleteSelection(),
                     application_action.Exit(),]
            
    def get_actions( self ):
        return []
    
    def get_sections( self ):
        return None
    
    def get_main_menu( self ):
        return None
    
    def get_stylesheet(self):
        from camelot.view import art
        return art.read('stylesheet/black.qss')
    
# end mini admin
