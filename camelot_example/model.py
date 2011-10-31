#
# Example model file, populate this file with your own models
# to get started quickly
#

import time
import datetime

from sqlalchemy import sql

from elixir import ColumnProperty

import camelot.types
from camelot.model import metadata
from elixir import Entity, Field, ManyToOne, OneToMany, \
                   ManyToMany, using_options
from camelot.admin.action import Action
from camelot.admin.entity_admin import EntityAdmin
from camelot.view import action_steps
from camelot.view.forms import Form, TabForm, WidgetOnlyForm, HBoxForm
from camelot.view.controls import delegates
from camelot.view.filters import ComboBoxFilter
from camelot.core.utils import ugettext_lazy as _
from camelot.view.art import ColorScheme
from sqlalchemy.types import Unicode, Date, Integer

__metadata__ = metadata

from camelot_example.change_rating import ChangeRatingAction

# Some helper functions that will be used later on
#

def genre_choices(entity_instance):
    """Choices for the possible movie genres"""
    return [
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
        obj = model_context.get_object()
        if obj and obj.title:
            state.enabled = True
        else:
            state.enabled = False
        return state
    
# begin short movie definition
class Movie(Entity):
    using_options(tablename='movies')
    title = Field(Unicode(60), required=True)
    short_description = Field(Unicode(512))
    releasedate = Field(Date)
    #
    # All relation types are covered with their own editor
    #
    director = ManyToOne('Person')
    cast = OneToMany('Cast')
    visitor_reports = OneToMany('VisitorReport')
    tags = ManyToMany('Tag')
    genre = Field(Unicode(15))
    rating = Field(camelot.types.Rating())
# end short movie definition
    #
    # Camelot includes custom sqlalchemy types, like Image, which stores an
    # image on disk and keeps the reference to it in the database.
    #
# begin image definition
    cover = Field(camelot.types.Image(upload_to='covers'))
# end image definition
    #
    # Or File, which stores a file in the upload_to directory and stores a
    # reference to it in the database
    #
    script = Field(camelot.types.File(upload_to='script'))
    description = Field(camelot.types.RichText)

    #
    # Using a ColumnProperty, an sql query can be assigned to a field
    #
    @ColumnProperty
    def total_visitors(self):
        return sql.select([sql.func.sum(VisitorReport.visitors)],
                               VisitorReport.movie_id==self.id)

    #
    # Normal python properties can be used as well, but then the
    # delegate needs be specified
    #
    @property
    def visitors_chart(self):
        #
        # Container classes are used to transport chunks of data between
        # the model thread and the gui thread, in this case a chart
        #
        from camelot.container.chartcontainer import BarContainer
        return BarContainer(range(len(self.visitor_reports)),
                            [vr.visitors for vr in self.visitor_reports])

    #
    # Each Entity subclass can have a subclass of EntityAdmin as
    # its inner class.  The EntityAdmin class defines how the Entity
    # class will be displayed in the GUI.  Its behavior can be steered
    # by specifying some class attributes
    #
    # To fully customize the way the entity is visualized, the EntityAdmin
    # subclass should overrule some of the EntityAdmin's methods
    #
    class Admin(EntityAdmin):
        # the list_display attribute specifies which entity attributes should
        # be visible in the table view
        list_display = ['cover', 'title', 'releasedate', 'rating',]
        lines_per_row = 5
        # define filters to be available in the table view
        list_filter = ['genre', ComboBoxFilter('director.full_name')]
        # if the search function needs to look in related object attributes,
        # those should be specified within list_search
        list_search = ['director.full_name']
        # begin list_actions
        #
        # the action buttons that should be available in the list view
        #
        list_actions = [ChangeRatingAction()]
        # end list_actions
        # the form_display attribute specifies which entity attributes should be
        # visible in the form view
        form_display = TabForm([
          ('Movie', Form([
            HBoxForm([WidgetOnlyForm('cover'), ['title', 'rating']]),
            'short_description',
            'releasedate',
            'director',
            'script',
            'genre',
            'description',], columns = 2)),
          ('Cast', WidgetOnlyForm('cast')),
         # ('Visitors', WidgetOnlyForm('visitors_chart')),
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
                                visitors_chart=dict(delegate=delegates.ChartDelegate),
                                rating=dict(tooltip='''<table>
                                                          <tr><td>1 star</td><td>Not that good</td></tr>
                                                          <tr><td>2 stars</td><td>Almost good</td></tr>
                                                          <tr><td>3 stars</td><td>Good</td></tr>
                                                          <tr><td>4 stars</td><td>Very good</td></tr>
                                                          <tr><td>5 stars</td><td>Awesome !</td></tr>
                                                       </table>'''),
                                smiley=dict(delegate=delegates.SmileyDelegate),
                                script=dict(remove_original=True))

    def __unicode__(self):
        return self.title or ''

class Cast(Entity):
    using_options(tablename='cast')
    movie = ManyToOne('Movie')
    actor = ManyToOne('Person', required=True)
    role = Field(Unicode(60))

    class Admin(EntityAdmin):
        verbose_name = 'Actor'
        list_display = ['actor', 'role']
        form_display = ['actor', 'role']

    def __unicode__(self):
        if self.actor:
            return self.actor.name
        return ''

class Tag(Entity):
    using_options(tablename='tags')
    name = Field(Unicode(60), required=True)
    movies = ManyToMany('Movie')

    def __unicode__(self):
        return self.name

    class Admin(EntityAdmin):
        form_size = (400,200)
        list_display = ['name']
        form_display = ['name', 'movies']
        lines_per_row = 2

# begin visitor report definition
class VisitorReport(Entity):
    using_options(tablename='visitor_report')
    movie = ManyToOne('Movie', required=True)
    date = Field(Date, required=True, default=datetime.date.today)
    visitors = Field(Integer, required=True, default=0)
# end visitor report definition

    class Admin(EntityAdmin):
        verbose_name = _('Visitor Report')
        #list_display = ['movie', 'city', 'date', 'visitors']
        list_display = ['movie', 'date', 'visitors']
        field_attributes = {'visitors':{'minimum':0}}
