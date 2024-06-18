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

import time
import datetime

# begin basic imports
from camelot.core.orm import Entity
from camelot.admin.entity_admin import EntityAdmin

from sqlalchemy import orm
from sqlalchemy.schema import Column, ForeignKey, Table
import sqlalchemy.types
# end basic imports

import camelot.types
from camelot.core.sql import metadata
from camelot.admin.action import Action
from camelot.admin.action import list_filter
from camelot.core.utils import ugettext_lazy as _
from camelot.model.party import Person
from camelot.view import action_steps
from camelot.view.forms import Form, TabForm, WidgetOnlyForm, HBoxForm, Stretch
from camelot.view.art import ColorScheme

from camelot_example.change_rating import ChangeRatingAction
from camelot_example.drag_and_drop import DropAction

#
# Some helper functions that will be used later on
#

def genre_choices( entity_instance ):
    """Choices for the possible movie genres"""
    return [
    ((None),('')),
    (('action'),('Action')),
    (('animation'),('Animation')),
    (('comedy'),('Comedy')),
    (('drama'),('Drama')),
    (('sci-fi'),('Sci-Fi')),
    (('war'),('War')),
    (('thriller'),('Thriller')),
    (('family'),('Family')) ]

# begin simple action definition
class BurnToDisk( Action ):
    
    verbose_name = _('Burn to disk')
    name = 'burn'
    
    def model_run( self, model_context ):
        yield action_steps.UpdateProgress( 0, 3, _('Formatting disk') )
        time.sleep( 0.7 )
        yield action_steps.UpdateProgress( 1, 3, _('Burning movie') )
        time.sleep( 0.7 )
        yield action_steps.UpdateProgress( 2, 3, _('Finishing') )
        time.sleep( 0.5 )
# end simple action definition

    def get_state( self, model_context ):
        """Turn the burn to disk button on, only if the title of the
        movie is entered"""
        state = super( BurnToDisk, self ).get_state( model_context )
        for obj in model_context.get_selection():
            if obj.title:
                state.enabled = True
            else:
                state.enabled = False
                break
        return state
    
# begin short movie definition
class Movie( Entity ):

    __tablename__ = 'movies'
    
    title = Column( sqlalchemy.types.Unicode(60), nullable = False )
    short_description = Column( sqlalchemy.types.Unicode(512) )
    releasedate = Column( sqlalchemy.types.Date )
    genre = Column( sqlalchemy.types.Unicode(15) )
    rating = Column( sqlalchemy.types.Integer() )
    #
    # All relation types are covered with their own editor
    #
    director_party_id = Column(sqlalchemy.types.Integer(), ForeignKey(Person.party_id))
    director = orm.relationship(Person)

# end short movie definition
    #
    # Camelot includes custom sqlalchemy types, like Image, which stores an
    # image on disk and keeps the reference to it in the database.
    #
# begin image definition
    cover = Column( camelot.types.File( upload_to = 'covers' ) )
# end image definition
    #
    # Or File, which stores a file in the upload_to directory and stores a
    # reference to it in the database
    #
    script = Column( camelot.types.File( upload_to = 'script' ) )
    description = Column( camelot.types.RichText )

    #
    # Each Entity subclass can have a subclass of EntityAdmin as
    # its inner class.  The EntityAdmin class defines how the Entity
    # class will be displayed in the GUI.  Its behavior can be steered
    # by specifying some class attributes
    #
    # To fully customize the way the entity is visualized, the EntityAdmin
    # subclass should overrule some of the EntityAdmin's methods
    #
    bar = 3
    class Admin(EntityAdmin):
        # the list_display attribute specifies which entity attributes should
        # be visible in the table view
        list_display = ['cover', 'title', 'releasedate', 'rating',]
        lines_per_row = 5
        # if the search function needs to look in related object attributes,
        # those should be specified within list_search
        list_search = ['director.full_name']
        # begin list_actions
        #
        # the action buttons that should be available in the list view
        #
        list_actions = [ChangeRatingAction()]
        # end list_actions
        drop_action = DropAction()
        # the form_display attribute specifies which entity attributes should be
        # visible in the form view
        form_display = TabForm([
          ('Movie', Form([
            HBoxForm([WidgetOnlyForm('cover'), ['title', 'rating', Stretch()]]),
            'short_description',
            'releasedate',
            'director',
            'script',
            'genre',
            'description',], columns = 2)),
          ('Cast', WidgetOnlyForm('cast')),
          ('Tags', WidgetOnlyForm('tags'))
        ])

        # begin form_actions
        #
        # create a list of actions available for the user on the form view
        #
        form_actions = [BurnToDisk()]
        # end form_actions
        #
        # additional attributes for a field can be specified in the
        # field_attributes dictionary
        #
        field_attributes = dict(cast=dict(create_inline=True),
                                genre=dict(choices=genre_choices, editable=lambda o:bool(o.title and len(o.title))),
                                releasedate=dict(background_color=lambda o:ColorScheme.orange_1 if o.releasedate and o.releasedate < datetime.date(1920,1,1) else None),
                                rating=dict(tooltip='''<table>
                                                          <tr><td>1 star</td><td>Not that good</td></tr>
                                                          <tr><td>2 stars</td><td>Almost good</td></tr>
                                                          <tr><td>3 stars</td><td>Good</td></tr>
                                                          <tr><td>4 stars</td><td>Very good</td></tr>
                                                          <tr><td>5 stars</td><td>Awesome !</td></tr>
                                                       </table>'''),
                                script=dict(remove_original=True))

    def __unicode__(self):
        return self.title or ''

# define filters to be available in the table view
Movie.Admin.list_filter = [
    list_filter.GroupBoxFilter(Movie.genre),
    list_filter.GroupBoxFilter(Person.full_name, joins=[Movie.director])
]

class Cast( Entity ):
    
    __tablename__ = 'cast'

    role = Column( sqlalchemy.types.Unicode(60) )
    movie_id = Column(sqlalchemy.types.Integer(), ForeignKey(Movie.id), nullable=False)
    movie = orm.relationship(Movie, backref='cast')
    actor_id = Column(sqlalchemy.types.Integer(), ForeignKey(Person.id), nullable=False)
    actor = orm.relationship(Person)

    class Admin( EntityAdmin ):
        verbose_name = 'Actor'
        list_display = ['actor', 'role']

    def __unicode__(self):
        if self.actor:
            return self.actor.name
        return ''

class Tag(Entity):

    __tablename__ = 'tags'

    name = Column( sqlalchemy.types.Unicode(60), nullable = False )

    def __unicode__( self ):
        return self.name

    class Admin( EntityAdmin ):
        form_size = (400,200)
        list_display = ['name']

t = Table('tags_movies__movies_tags', metadata, Column('movies_id', sqlalchemy.types.Integer(), ForeignKey(Movie.id), primary_key=True),
          Column('tags_id', sqlalchemy.types.Integer(), ForeignKey(Tag.id), primary_key=True))
Tag.movies = orm.relationship(Movie, backref='tags', secondary=t, foreign_keys=[t.c.movies_id, t.c.tags_id])
