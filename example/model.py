#
# Example model file, populate this file with your own models
# to get started quickly
#

import camelot.types
from camelot.model import metadata, Entity, Field, ManyToOne, OneToMany, Unicode, Date, Integer, using_options
from camelot.view.elixir_admin import EntityAdmin
from camelot.view.forms import Form, TabForm, WidgetOnlyForm, HBoxForm

__metadata__ = metadata

def genre_choices(entity_instance):
  yield (('action'),('Action'))
  yield (('animation'),('Animation'))
  yield (('comedy'),('Comedy'))
  yield (('drama'),('Drama'))
  yield (('sci-fi'),('Sci-Fi'))
  yield (('war'),('War'))
  
class Movie(Entity):
  using_options(tablename='movies')
  title = Field(Unicode(60), required=True)
  short_description = Field(Unicode(512))
  releasedate = Field(Date)
  director = ManyToOne('Person')
  cast = OneToMany('Cast')
  genre = Field(Unicode(15))
  rating = Field(Integer())
  #
  # Camelot includes custom sqlalchemy types, like Image, which stores an
  # PIL image on disk and keeps the reference to it in the database.
  #
  cover = Field(camelot.types.Image(upload_to='covers'))
  description = Field(Unicode())
  
  def burn_to_disk(self):
    print 'burn burn burn'

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
    name = 'Movies'
    # the section attributed specifies where in the left panel of the
    # main window a link to a list of this entities will appear. Have
    # a look in main.py for the definition of the sections        
    section = 'movies'
    # the list_display attribute specifies which entity attributes should
    # be visible in the table view        
    list_display = ['title', 'releasedate', 'director']
    # define filters to be available in the table view
    list_filter = ['genre']
    # the form_display attribute specifies which entity attributes should be
    # visible in the form view        
    form_display = TabForm([('Movie', Form([HBoxForm([['title', 'rating'],WidgetOnlyForm('cover')]), 'short_description', 'releasedate', 'director', 'description'])),
                            ('Cast', WidgetOnlyForm('cast'))])
    #
    # create a list of actions available for the user on the form view
    # those actions will be executed within the model thread
    #
    form_actions = [('Burn DVD', lambda o: o.burn_to_disk())]
    # additional attributes for a field can be specified int the field_attributes dictionary
    field_attributes = dict(cast=dict(create_inline=True),
                            genre=dict(choices=genre_choices))

  def __repr__(self):
    return self.title or ''

class Cast(Entity):
  using_options(tablename='cast')
  movie = ManyToOne('Movie')
  actor = ManyToOne('Person', required=True)
  role = Field(Unicode(60))
  
  class Admin(EntityAdmin):
      name = 'Actor'
      list_display = ['actor', 'role']
      form_display = ['actor', 'role']

  def __repr__(self):
    return self.name or ''
