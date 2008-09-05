# 
# Example model file, populate this file with your own models
# to get started quickly
#

from datetime               import datetime

import camelot.types
from camelot.model import *

__metadata__ = metadata

from camelot.view.elixir_admin import EntityAdmin

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
        # main window a link to a list of this entities will appear.  Have
        # a look in main.py for the definition of the sections
        section = 'movies'
        # the list_display attribute specifies which entity attributes should
        # be visible in the table view
        list_display = ['name']
        # the fields attribute specifies which entity attributes should be visible
        # in the form view
        fields = ['name', 'movies']

class Movie(Entity):
    title = Field(Unicode(60))
    description = Field(Unicode(512))
    releasedate = Field(Date)
    director = ManyToOne('Director', inverse='movies')
    actors = ManyToMany('Actor', inverse='movies', tablename='movie_casting')
    #
    # Camelot includes custom sqlalchemy types, like Image, which stores an PIL image
    # on disk and keeps the reference to it in the database.
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
        form_actions = [('Burn DVD',lambda o:o.burn_to_disk())]

class Actor(Entity):
    name = Field(Unicode(60))
    movies = ManyToMany('Movie', inverse='actors', tablename='movie_casting')
    using_options(tablename='actors')
   
    class Admin(EntityAdmin):
        name = 'Actor'
        section = 'movies'
        list_display = ['name',]
        fields = ['name', 'movies']
#
# identity model
# 

class Visit(Entity):
    visit_key = Field(String(40), primary_key=True)
    created = Field(DateTime, required=True, default=datetime.now)
    expiry = Field(DateTime)
    using_options(tablename='visit')
    
    @classmethod
    def lookup_visit(cls, visit_key):
        return Visit.get(visit_key)

class VisitIdentity(Entity):
    visit_key = Field(String(40), primary_key=True)
    user = ManyToOne('User')
    using_options(tablename='visit_identity')

class Group(Entity):
    group_name = Field(Unicode(16), unique=True)
    display_name = Field(Unicode(255))
    created = Field(DateTime, default=datetime.now)
    users = ManyToMany('User', inverse='groups')
    permissions = ManyToMany('Permission', inverse='groups')
    using_options(tablename='tg_group')

    class Admin(EntityAdmin):
        name = 'Groups'
        section = 'configuration'
        list_display = ['group_name', 'display_name', 'created']
                        
class User(Entity):
    user_name = Field(Unicode(16), unique=True)
    email_address = Field(Unicode(255), unique=True)
    display_name = Field(Unicode(255))
    password = Field(Unicode(40))
    created = Field(DateTime, default=datetime.now)
    groups = ManyToMany('Group', inverse='users')
    using_options(tablename='tg_user')
    
    @property
    def permissions(self):
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms
    
    class Admin(EntityAdmin):
        name = 'Users'
        section = 'configuration'
        list_display = ['user_name', 'email_address', 'display_name', 'created']

class Permission(Entity):
    permission_name = Field(Unicode(16), unique=True)
    description = Field(Unicode(255))
    groups = ManyToMany('Group', inverse='permissions')
    using_options(tablename='permission')
    
    class Admin(EntityAdmin):
        name = 'Permissions'
        section = 'configuration'
        list_display = ['permission_name', 'description',]
