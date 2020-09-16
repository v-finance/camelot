#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
from camelot.view.art import FontIcon
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
        from camelot.model.batch_job import BatchJob, BatchJobType
        
        from camelot_example.model import Movie, Tag, VisitorReport
        from camelot_example.view import VisitorsPerDirector
# begin import action
        from camelot_example.importer import ImportCovers
# end import action
        
        return [
# begin section with action
                Section( _('Movies'),
                         self,
                         FontIcon('film'),
                         items = [ Movie, 
                                   Tag, 
                                   VisitorReport, 
                                   VisitorsPerDirector,
                                   ImportCovers() ]),
# end section with action
                Section( _('Relation'),
                         self,
                         FontIcon('users'),
                         items = [ Person, 
                                   Organization,
                                   PartyCategory ]),
                Section( _('Configuration'),
                         self,
                         FontIcon('cog'),
                         items = [ Memento, 
                                   Translation,
                                   BatchJobType,
                                   BatchJob 
                                   ])
                ]
# end sections

# begin actions
    def get_actions(self):
        from camelot.admin.action import OpenNewView
        from camelot.model.party import Party
        from camelot_example.model import Movie
        
        new_movie_action = OpenNewView( self.get_related_admin(Movie) )
        new_movie_action.icon = FontIcon('film')

        return [new_movie_action, OpenNewView(self.get_related_admin(Party))]
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
        movies_action.icon = FontIcon('film')
        persons_action = application_action.OpenTableView( self.get_related_admin( Person ) )
        persons_action.icon = FontIcon('users')
        
        if toolbar_area == Qt.LeftToolBarArea:
            return [ movies_action,
                     persons_action,
                     list_action.AddNewObject(),
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
        return art.read('stylesheet/black.qss').decode('utf-8')
    
# end mini admin

