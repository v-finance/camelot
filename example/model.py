from datetime               import datetime

from camelot.model import *
__metadata__ = metadata

from camelot.view.elixir_admin import EntityAdmin

#
# application model
#

class Director(Entity):
    name = Field(Unicode(60))
    movies = OneToMany('Movie', inverse='director')
    using_options(tablename='directors')

    class Admin(EntityAdmin):
        name = 'Directors'
        section = 'movies'
        list_display = ['name']
    

class Movie(Entity):
    title = Field(Unicode(60))
    description = Field(Unicode(512))
    releasedate = Field(DateTime)
    director = ManyToOne('Director', inverse='movies')
    actors = ManyToMany('Actor', inverse='movies', tablename='movie_casting')
    using_options(tablename='movies')

    class Admin(EntityAdmin):
        name = 'Movies'
        section = 'movies'
        list_display = ['title', 'releasedate', 'director']

class Actor(Entity):
    name = Field(Unicode(60))
    movies = ManyToMany('Movie', inverse='actors', tablename='movie_casting')
    using_options(tablename='actors')
   
    class Admin(EntityAdmin):
        name = 'Actor'
        section = 'movies'
        list_display = ['name',]
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
