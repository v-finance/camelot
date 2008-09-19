#
# Example model file, populate this file with your own models
# to get started quickly
#

from datetime import datetime

import camelot.types
from camelot.model import *
from camelot.view.elixir_admin import EntityAdmin

__metadata__ = metadata


class Director(Entity):

    name = Field(Unicode(60))
    movies = OneToMany('Movie', inverse='director')
    using_options(tablename='directors')

    def __repr__(self):
      return self.name

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
        name = 'Directors'
        # the section attributed specifies where in the left panel of the
        # main window a link to a list of this entities will appear. Have
        # a look in main.py for the definition of the sections
        section = 'movies'
        # the list_display attribute specifies which entity attributes should
        # be visible in the table view
        list_display = ['name']
        # the fields attribute specifies which entity attributes should be
        # visible in the form view
        fields = ['name', 'movies']


class Movie(Entity):
    title = Field(Unicode(60))
    description = Field(Unicode(512))
    releasedate = Field(Date)
    director = ManyToOne('Director', inverse='movies')
    actors = ManyToMany('Actor', inverse='movies', tablename='movie_casting')
    #
    # Camelot includes custom sqlalchemy types, like Image, which stores an
    # PIL image on disk and keeps the reference to it in the database.
    #
    cover = Field(camelot.types.Image(upload_to='covers'))
    using_options(tablename='movies')

    def burn_to_disk(self):
      print 'burn burn burn'

    class Admin(EntityAdmin):
        name = 'Movies'
        section = 'movies'
        list_display = ['title', 'releasedate', 'director']
        fields = ['title', 'releasedate', 'director', 'cover', 'actors']
        #
        # create a list of actions available for the user on the form view
        # those actions will be executed within the model thread
        #
        form_actions = [('Burn DVD', lambda o: o.burn_to_disk())]

    def __repr__(self):
      return self.title


class Actor(Entity):
    name = Field(Unicode(60))
    movies = ManyToMany('Movie', inverse='actors', tablename='movie_casting')
    using_options(tablename='actors')

    class Admin(EntityAdmin):
        name = 'Actor'
        section = 'movies'
        list_display = ['name', ]
        fields = ['name', 'movies']

    def __repr__(self):
      return self.name
