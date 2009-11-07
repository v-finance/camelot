from elixir import Entity, Field, ManyToOne
from sqlalchemy.types import Unicode, Date
from camelot.admin.entity_admin import EntityAdmin
from camelot.view import forms

class Movie(Entity):
    title = Field(Unicode(60), required=True)
    short_description = Field(Unicode(512))
    releasedate = Field(Date)
    director = ManyToOne('Person')
  
    class Admin(EntityAdmin):
        form_display = forms.Form(['title', 'short_description', 'director', 'release_date'])
