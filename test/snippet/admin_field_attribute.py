from sqlalchemy import schema, types

from camelot.admin.entity_admin import EntityAdmin
from camelot.core.orm import ManyToMany, Entity
from camelot.model.party import Person

class PersonOnMailingGroupAdmin(EntityAdmin):
    list_display = ['first_name', 'last_name', 'street1', 'city']

class MailingGroup(Entity):
    name = schema.Column(types.Unicode(30), nullable=False)
    persons = ManyToMany(Person)
    
    class Admin(EntityAdmin):
        list_display = ['name']
        form_display = ['name', 'persons']
        field_attributes = {'persons': {'admin': PersonOnMailingGroupAdmin}
                            }