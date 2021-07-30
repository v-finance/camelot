from camelot.admin.entity_admin import EntityAdmin
from camelot.core.orm import Entity
from camelot.core.sql import metadata
from camelot.model.party import Person
from sqlalchemy import orm, schema, types


class PersonOnMailingGroupAdmin(EntityAdmin):
    list_display = ['first_name', 'last_name', 'street1', 'city']

class MailingGroup(Entity):
    name = schema.Column(types.Unicode(30), nullable=False)

    class Admin(EntityAdmin):
        list_display = ['name']
        form_display = ['name', 'persons']
        field_attributes = {'persons': {'admin': PersonOnMailingGroupAdmin}
                            }

t = schema.Table('mailing_group_table', metadata, schema.Column('person_id', types.Integer(), schema.ForeignKey(Person.id), primary_key=True),
                         schema.Column('mailing_group_id', types.Integer(), schema.ForeignKey(MailingGroup.id), primary_key=True))
MailingGroup.persons = orm.relationship(Person, backref=orm.backref('mailing_group'), secondary=t, foreign_keys=[t.c.person_id, t.c.mailing_group_id])