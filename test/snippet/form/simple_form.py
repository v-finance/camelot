from sqlalchemy.schema import Column
from sqlalchemy.types import Unicode, Date
from camelot.admin.entity_admin import EntityAdmin
from camelot.core.orm import Entity
from camelot.view import forms

class Movie( Entity ):    
    title = Column( Unicode(60), nullable=False )
    short_description = Column( Unicode(512) )
    releasedate = Column( Date )
  
    class Admin(EntityAdmin):
        form_display = forms.Form( ['title', 'short_description', 'releasedate'] )
