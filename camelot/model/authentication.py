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
from camelot.model.synchronization import *

__metadata__ = metadata

from camelot.view.elixir_admin import EntityAdmin
import datetime

_current_person_ = None

def end_of_times():
  return datetime.date(year=2400, month=12, day=31)

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

class PartyRelationship(Entity):
  using_options(tablename='party_relationship')
  from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
  thru_date = Field(Date(), default=end_of_times, required=True, index=True)
  comment = Field(Unicode())
  is_synchronized('synchronized', lazy=True)
  
class EmployerEmployee(PartyRelationship):
  """Relation from employer to employee"""
  using_options(tablename='party_relationship_empl', inheritance='multi')
  established_from = ManyToOne('Organization', required=True, ondelete='cascade', onupdate='cascade')
  established_to = ManyToOne('Person', required=True, ondelete='cascade', onupdate='cascade')
  
  class EmployeeAdmin(EntityAdmin):
    name = 'Employees'
    list_display = ['established_to', 'from_date', 'thru_date']
    fields = ['established_to', 'comment', 'from_date', 'thru_date']
    field_attributes = {'established_to':{'name':'Name'}}
    
  class EmployerAdmin(EntityAdmin):
    name = 'Employers'
    list_display = ['established_from', 'from_date', 'thru_date']
    fields = ['established_from', 'comment', 'from_date', 'thru_date']
    field_attributes = {'established_from':{'name':'Name'}}
    
class SupplierCustomer(PartyRelationship):
  """Relation from supplier to customer"""
  using_options(tablename='party_relationship_suppl', inheritance='multi')
  established_from = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
  established_to = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
  
  class CustomerAdmin(EntityAdmin):
    name = 'Customers'
    list_display = ['established_to', 'from_date', 'thru_date']
    fields = ['established_to', 'comment', 'from_date', 'thru_date']
    field_attributes = {'established_to':{'name':'Name'}}
    
  class SupplierAdmin(EntityAdmin):
    name = 'Suppliers'
    list_display = ['established_from', 'from_date', 'thru_date']
    fields = ['established_from', 'comment', 'from_date', 'thru_date']
    field_attributes = {'established_from':{'name':'Name'}}
    
class Party(Entity):
  """Base class for persons and organizations.  Use this base class to refer to either persons or
  organisations in building authentication systems, contact management or CRM"""
  using_options(tablename='party')
  is_synchronized('synchronized', lazy=True)
  addresses = OneToMany('PartyAddress')
    
  class Admin(EntityAdmin):
    name = 'Parties'
    fields = ['suppliers', 'customers', 'addresses']
    field_attributes = dict(suppliers={'admin':SupplierCustomer.SupplierAdmin}, 
                            customers={'admin':SupplierCustomer.CustomerAdmin},
                            employers={'admin':EmployerEmployee.EmployerAdmin},
                            employees={'admin':EmployerEmployee.EmployeeAdmin})
      
class Organization(Party):
  """An organization represents any internal or external organization.  Organizations can include
  businesses and groups of individuals"""
  using_options(tablename='organization', inheritance='multi')
  name = Field(Unicode(50), required=True, index=True)
  tax_id = Field(Unicode(20))
  employees = OneToMany('EmployerEmployee', inverse='established_from')
  suppliers = OneToMany('SupplierCustomer', inverse='established_to')
  customers = OneToMany('SupplierCustomer', inverse='established_from')  
  
  def __unicode__(self):
    return self.name
  
  class Admin(Party.Admin):
    name = 'Organizations'
    section = 'relations'
    list_display = ['name', 'tax_id',]
    fields = ['name', 'tax_id',] + Party.Admin.fields + ['employees']
      
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
  employers = OneToMany('EmployerEmployee', inverse='established_to')
      
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
    section = 'relations'
    list_display = ['username', 'first_name', 'last_name', ]
    fields = ['username', 'first_name', 'last_name', 'birthdate', 'social_security_number', 'passport_number', 
              'passport_expiry_date', 'is_staff', 'is_active', 'is_superuser',
              'comment', 'addresses', 'employers']
    list_filter = ['is_active', 'is_staff', 'is_superuser']
    
class GeographicBoundary(Entity):
  using_options(tablename='geographic_boundary')
  code = Field(Unicode(10))
  name = Field(Unicode(40), required=True)

  def __unicode__(self):
    return u'%s %s'%(self.code, self.name)
    
class Country(GeographicBoundary):
  using_options(tablename='geographic_boundary_country', inheritance='multi')
  
  @classmethod
  def getOrCreate(cls, code, name):
    country = Country.query.filter_by(code=code).first()
    if not country:
      from elixir import session
      country = Country(code=code, name=name)
      session.flush([country])
    return country
  
  class Admin(EntityAdmin):
    name = 'Countries'
    list_display = ['name', 'code']
    
class City(GeographicBoundary):
  using_options(tablename='geographic_boundary_city', inheritance='multi')
  country = ManyToOne('Country', required=True, ondelete='cascade', onupdate='cascade')
  
  @classmethod
  def getOrCreate(cls, country, code, name):
    city = City.query.filter_by(code=code, country=country).first()
    if not city:
      from elixir import session
      city = City(code=code, name=name, country=country)
      session.flush([city])
    return city
  
  class Admin(EntityAdmin):
    name = 'Cities'
    list_display = ['code', 'name', 'country']
    
class Address(Entity):
  using_options(tablename='address')
  street1 = Field(Unicode('128'), required=True)
  street2 = Field(Unicode('128'))
  city = ManyToOne('City', required=True, ondelete='cascade', onupdate='cascade')
  is_synchronized('synchronized', lazy=True)
  
  def __unicode__(self):
    return u'%s, %s'%(self.street1, self.city)
  
  class Admin(EntityAdmin):
    name = 'Addresses'
    list_display = ['street1', 'street2', 'city']
  
class PartyAddressRoleType(Entity):
  using_options(tablename='party_address_role_type')
  code = Field(Unicode(10))
  description = Field(Unicode(40))
  
class PartyAddress(Entity):
  using_options(tablename='party_address')
  party = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
  address = ManyToOne('Address', required=True, ondelete='cascade', onupdate='cascade')
  from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
  thru_date = Field(Date(), default=end_of_times, required=True, index=True)
  comment = Field(Unicode('256'))
  
  class Admin(EntityAdmin):
    name = 'Address'
    list_display = ['address', 'comment']
    fields = ['address', 'comment', 'from_date', 'thru_date']    