#  ==================================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ==================================================================================
"""Set of classes to store persons, organizations, relationships and permissions

These structures are modeled like described in 'The Data Model Resource Book' by
Len Silverston, Chapter 2
"""

import camelot
import camelot.types

from camelot.model import *

__metadata__ = metadata

from camelot.view.elixir_admin import EntityAdmin
import datetime

_current_person_ = None

def getCurrentPerson():
  """Get the currently logged in person"""
  global _current_person_
  if not _current_person_:
    import getpass
    _current_person_ = Person.getOrCreatePerson(getpass.getuser())
  return _current_person_

def updateLastLogin():
  """Update the last login of the current person to now"""
  from elixir import session
  person = getCurrentPerson()
  person.last_login = datetime.datetime.now()
  session.flush([person])

# Enumeration of the different types of relationships that are covered, the key
# in the dictionary is the value that should be in party_relationship_type,
# the value is a tuple containing the (from_role, to_role, from_type, to_type) role of the relationship.  Eventually
# this structure could be put into the database as well, but this would have serious
# implications for the GUI
party_relationship_types = {
#                            1:('supplier', 'customer', 'Organization', 'Person'),
                            2:('employer', 'employee', 'Organization', 'Person'),
                            }
  
class PartyRelationship(Entity):
  using_options(tablename='party_relationship')
  established_from = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
  established_to = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
  party_relationship_type = Field(Integer(), colname='party_relationship_type_id', required=True)
  valid_time_start = Field(Date(), default=datetime.date.today, required=True, index=True)
  valid_time_end = Field(Date(), default=datetime.date(year=2400, month=12, day=31), required=True, index=True)
  comment = Field(Unicode())

  @property
  def to_role(self):
    return party_relationship_types[self.party_relationship_type][1]

  @property
  def from_role(self):
    return party_relationship_types[self.party_relationship_type][0]
    
  class FromAdmin(EntityAdmin):
    name = 'Relationships'
    list_display = ['established_to', 'valid_time_start', 'valid_time_end']
    fields = ['established_to', 'comment', 'valid_time_start', 'valid_time_end']
    field_attributes = {'established_to':{'name':'Name'}}
    
  class ToAdmin(EntityAdmin):
    name = 'Relationships'
    list_display = ['established_from', 'valid_time_start', 'valid_time_end']
    fields = ['established_from', 'comment', 'valid_time_start', 'valid_time_end']
    field_attributes = {'established_from':{'name':'Name'}}
  
def relationships(entity_names):
  """Generate a list of relationship types applicable for a certain entity names
  @return: [(relationship_type_id, field_name, inverse), ...]"""
  for key,value in party_relationship_types.items():
    if value[2] in entity_names:
      yield (key, '%ss'%value[1], 'established_from')
    if value[3] in entity_names:
      yield (key, '%ss'%value[0], 'established_to')

def relationship_type_filter(type_id):
  """Closure to generate a ClauseElement to filter relationships on their type"""
  
  def filter_function(c):
    return c.party_relationship_type_id==type_id
  
  return filter_function

class Party(Entity):
  """Base class for persons and organizations.  Use this base class to refer to either persons or
  organisations in building authentication systems, contact management or CRM"""
  using_options(tablename='party')
  for type_id, field, inverse in relationships(('Party', 'Organization', 'Person',)):
    filter_function = relationship_type_filter(type_id)
    has_many(field, of_kind='PartyRelationship', inverse=inverse, filter=filter_function)
    
  class Admin(EntityAdmin):
    name = 'Parties'
    fields = [r[1] for r in relationships(('Party',))]
    field_attributes = dict((field_name,{'admin':{'established_from':PartyRelationship.FromAdmin, 'established_to':PartyRelationship.ToAdmin}[inverse]}) 
                            for relationship_type_id, field_name, inverse in relationships(('Party', 'Organization', 'Person'))  )
      
class Organization(Party):
  """An organization represents any internal or external organization.  Organizations can include
  businesses and groups of individuals"""
  using_options(tablename='organization', inheritance='multi')
  name = Field(Unicode(40), required=True, index=True)
  tax_id = Field(Unicode(15))  
  
  def __unicode__(self):
    return self.name
  
  class Admin(Party.Admin):
    name = 'Organizations'
    section = 'configuration'
    list_display = ['name', 'tax_id',]
    fields = ['name', 'tax_id',] + Party.Admin.fields + [r[1] for r in relationships(('Organization',))]
      
class Person(Party):
  """Person represents natural persons, these can be given access to the system, and
  as such require a username.
  
  Username is required, other fields are optional, there is no password because
  authentication is supposed to happen through the operating system services or other.
  """
  using_options(tablename='person', inheritance='multi')
  username = Field(Unicode(40), required=True, index=True, unique=True)
  first_name = Field(Unicode(40))
  last_name =  Field(Unicode(40))
  middle_name = Field(Unicode(40))
  personal_title = Field(Unicode(10))
  suffix = Field(Unicode(3))
  sex = Field(Unicode(1))
  birthdate = Field(Date())
  martial_status = Field(Unicode(1))
  social_security_number = Field(Unicode(12))
  passport_number = Field(Unicode(20))
  passport_expiry_date = Field(Date())
  is_staff = Field(Boolean, default=False, index=True)
  is_active = Field(Boolean, default=True, index=True)
  is_superuser = Field(Boolean, default=False, index=True)
  last_login = Field(DateTime(), default=datetime.datetime.now)
  date_joined = Field(DateTime(), default=datetime.datetime.now)
  picture = Field(camelot.types.Image(upload_to='person-pictures'), deferred=True)
  comment = Field(Unicode())
      
  def __unicode__(self):
    return self.username
  
  @classmethod
  def getOrCreatePerson(cls, username):
    person = cls.query.filter_by(username=username).first()
    if not person:
      person = cls(username=username)
      from elixir import session
      session.flush([person])
    return person

  class Admin(Party.Admin):
    name = 'Persons'
    section = 'configuration'
    list_display = ['username', 'first_name', 'last_name', 'last_login']
    fields = ['username', 'first_name', 'last_name', 'birthdate', 'social_security_number', 'passport_number', 
              'passport_expiry_date', 'is_staff', 'is_active', 'is_superuser', 'last_login', 'date_joined', 
              'comment'] + Party.Admin.fields  + [r[1] for r in relationships(('Person',))]
    list_filter = ['is_active', 'is_staff', 'is_superuser']
                            

      