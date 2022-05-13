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
from camelot.core.utils import ugettext_lazy as _

# begin application admin
class MyApplicationAdmin(ApplicationAdmin):

    name = 'Camelot Video Store'

# begin actions
    def get_actions(self):
        from camelot.admin.action import OpenNewView
        from camelot.model.party import Party
        from camelot_example.model import Movie
        
        new_movie_action = OpenNewView( self.get_related_admin(Movie) )
        new_movie_action.icon = FontIcon('film')

        return [new_movie_action, OpenNewView(self.get_related_admin(Party))]
# end actions

app_admin = MyApplicationAdmin()

# begin sections

movies = app_admin.add_navigation_menu(_('Movies'), FontIcon('film'))
relations = app_admin.add_navigation_menu(_('Relations'), FontIcon('users'))
configuration = app_admin.add_navigation_menu(_('Configuration'), FontIcon('cog'))

from camelot.model.memento import Memento
from camelot.model.party import ( Person, Organization, 
                                  PartyCategory )
from camelot.model.i18n import Translation

from camelot_example.model import Movie, Tag

# begin import action
from camelot_example.importer import ImportCovers
# end import action
        
# begin section with action

app_admin.add_navigation_entity_table(Movie, movies)
app_admin.add_navigation_entity_table(Tag, movies)
app_admin.add_navigation_action(ImportCovers(), movies)

# end section with action

app_admin.add_navigation_entity_table(Person, relations)
app_admin.add_navigation_entity_table(Organization, relations)
app_admin.add_navigation_entity_table(PartyCategory, relations)


app_admin.add_navigation_entity_table(Memento, configuration)
app_admin.add_navigation_entity_table(Translation, configuration)

# end sections
    
# end application admin
