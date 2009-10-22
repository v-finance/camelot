#
# Example model file, populate this file with your own models
# to get started quickly
#

import camelot.types
from camelot.model import metadata, Entity, Field, ManyToOne, OneToMany, ManyToMany, \
                          Unicode, Date, Integer, Boolean, using_options
from camelot.view.elixir_admin import EntityAdmin
from camelot.view.forms import Form, TabForm, WidgetOnlyForm, HBoxForm
from camelot.view.controls import delegates
from camelot.view.filters import ComboBoxFilter

__metadata__ = metadata

#
# Some helper functions that will be used later on
#

def genre_choices(entity_instance):
  """Generate choices for the possible movie genres"""
  yield (('action'),('Action'))
  yield (('animation'),('Animation'))
  yield (('comedy'),('Comedy'))
  yield (('drama'),('Drama'))
  yield (('sci-fi'),('Sci-Fi'))
  yield (('war'),('War'))

def burn_to_disk(o_getter):
  print 'burn burn burn'
    
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
  tags = ManyToMany('Tag')
  genre = Field(Unicode(15))
  rating = Field(camelot.types.Rating())
  #
  # Camelot includes custom sqlalchemy types, like Image, which stores an
  # PIL image on disk and keeps the reference to it in the database.
  #
  cover = Field(camelot.types.Image(upload_to='covers'))
  #
  # Or File, which stores a file in the upload_to directory and stores a
  # reference to it in the database
  #
  script = Field(camelot.types.File(upload_to='script'))
  description = Field(camelot.types.RichText)
  #
  # Each Entity subclass can have a subclass of EntityAdmin as
  # its inner class.  The EntityAdmin class defines how the Entity
  # class will be displayed in the GUI.  Its behaviour can be steered
  # by specifying some class attributes
  #
  # To fully customize the way the entity is visualized, the EntityAdmin
  # subclass should overrule some of the EntityAdmin's methods
  #
  class Admin(EntityAdmin):
    # the list_display attribute specifies which entity attributes should
    # be visible in the table view        
    list_display = ['title', 'releasedate', 'director', 'description']
    # define filters to be available in the table view
    list_filter = ['genre', ComboBoxFilter('director.full_name')]
    # if the search function needs to look in related object attributes,
    # those should be specified within list_search
    list_search = ['director.full_name']
    # the form_display attribute specifies which entity attributes should be
    # visible in the form view
    form_display = TabForm([
      ('Movie', Form([
        HBoxForm([['title', 'rating'], WidgetOnlyForm('cover')]),
        'short_description',
        'releasedate', 
        'director',
        'script', 
        'genre', 
        'description', 'tags'], scrollbars=True)),
      ('Cast', WidgetOnlyForm('cast'))
    ])
    
    # create a list of actions available for the user on the form view
    # those actions will be executed within the model thread
    #
    form_actions = [('Burn DVD', burn_to_disk)]
    #
    # additional attributes for a field can be specified in the
    # field_attributes dictionary
    #
    field_attributes = dict(cast=dict(create_inline=True),
                            genre=dict(choices=genre_choices),
                            rating=dict(tooltip=lambda o:'''<table>
                                                              <tr><td>1 star</td><td>Not that good</td></tr>
                                                              <tr><td>2 stars</td><td>Almost good</td></tr>
                                                              <tr><td>3 stars</td><td>Good</td></tr>
                                                              <tr><td>4 stars</td><td>Very good</td></tr>
                                                              <tr><td>5 stars</td><td>Awesome !</td></tr>
                                                            </table>'''),
                            smiley=dict(delegate=delegates.SmileyDelegate))

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