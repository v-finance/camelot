#  ============================================================================
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
#  ============================================================================
"""Set of classes to store persons, organizations, relationships and
permissions

These structures are modeled like described in 'The Data Model Resource Book'
by Len Silverston, Chapter 2
"""

import camelot
import camelot.types

from camelot.model import *
from camelot.model.synchronization import *

__metadata__ = metadata

from camelot.view.elixir_admin import EntityAdmin
from camelot.view.forms import Form, TabForm, VBoxForm, HBoxForm, WidgetOnlyForm
import datetime

_current_authentication_ = None

def end_of_times():
  return datetime.date(year=2400, month=12, day=31)

def getCurrentAuthentication():
  """Get the currently logged in person"""
  global _current_authentication_
  if not _current_authentication_:
    import getpass
    _current_authentication_ = UsernameAuthenticationMechanism.getOrCreateAuthentication(unicode(getpass.getuser()))
  return _current_authentication_

def updateLastLogin():
  """Update the last login of the current person to now"""
  from elixir import session
  authentication = getCurrentAuthentication()
  authentication.last_login = datetime.datetime.now()
  session.flush([authentication])

class PartyRelationship(Entity):
  using_options(tablename='party_relationship')
  from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
  thru_date = Field(Date(), default=end_of_times, required=True, index=True)
  comment = Field(camelot.types.RichText())
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
    
class DirectedDirector(PartyRelationship):
  """Relation from a directed organization to a director"""
  using_options(tablename='party_relationship_dir', inheritance='multi')
  established_from = ManyToOne('Organization', required=True, ondelete='cascade', onupdate='cascade')
  established_to = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
  title = Field(Unicode(256))
  represented_by = OneToMany('RepresentedRepresentor', inverse='established_to')
  
  class DirectorAdmin(EntityAdmin):
    name = 'Directors'
    list_display = ['established_to', 'from_date', 'thru_date']
    fields = ['established_to', 'title', 'from_date', 'thru_date', 'represented_by', 'comment']
    field_attributes = {'established_to':{'name':'Name'}}
    
  class DirectedAdmin(EntityAdmin):
    name = 'Directed organizations'
    list_display = ['established_from', 'from_date', 'thru_date']
    fields = ['established_from', 'from_date', 'thru_date', 'represented_by', 'comment']
    field_attributes = {'established_from':{'name':'Name'}}
    
class RepresentedRepresentor(Entity):
  """Relation from a representing party to the person representing the party"""
  using_options(tablename='party_representor')
  from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
  thru_date = Field(Date(), default=end_of_times, required=True, index=True)
  comment = Field(camelot.types.RichText())
  established_from = ManyToOne('Person', required=True, ondelete='cascade', onupdate='cascade')
  established_to = ManyToOne('DirectedDirector', required=True, ondelete='cascade', onupdate='cascade')
  
  class Admin(EntityAdmin):
    name = 'Represented by'
    list_display = ['established_from', 'from_date', 'thru_date']
    form_display = ['established_from', 'from_date', 'thru_date', 'comment']
    field_attributes = {'established_from':{'name':'Name'}}
    
class SupplierCustomer(PartyRelationship):
  """Relation from supplier to customer"""
  using_options(tablename='party_relationship_suppl', inheritance='multi')
  established_from = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
  established_to = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
  
  class CustomerAdmin(EntityAdmin):
    name = 'Customers'
    list_display = ['established_to',]
    fields = ['established_to', 'comment', 'from_date', 'thru_date']
    field_attributes = {'established_to':{'name':'Name'}}
    
  class SupplierAdmin(EntityAdmin):
    name = 'Suppliers'
    list_display = ['established_from',]
    fields = ['established_from', 'comment', 'from_date', 'thru_date']
    field_attributes = {'established_from':{'name':'Name'}}
    
class SharedShareholder(PartyRelationship):
  """Relation from a shared organization to a shareholder"""
  using_options(tablename='party_relationship_shares', inheritance='multi')
  established_from = ManyToOne('Organization', required=True, ondelete='cascade', onupdate='cascade')
  established_to = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
  shares = Field(Integer())
  
  class ShareholderAdmin(EntityAdmin):
    name = 'Shareholders'
    list_display = ['established_to', 'shares', 'from_date', 'thru_date']
    fields = ['established_to', 'shares', 'from_date', 'thru_date', 'comment']
    field_attributes = {'established_to':{'name':'Shareholder name'}}
    
  class SharedAdmin(EntityAdmin):
    name = 'Shares'
    list_display = ['established_from', 'shares', 'from_date', 'thru_date']
    fields = ['established_from', 'shares', 'from_date', 'thru_date', 'comment']
    field_attributes = {'established_from':{'name':'Name'}}
    
class Party(Entity):
  """Base class for persons and organizations.  Use this base class to refer to either persons or
  organisations in building authentication systems, contact management or CRM"""
  using_options(tablename='party')
  is_synchronized('synchronized', lazy=True)
  addresses = OneToMany('PartyAddress', lazy=True)
  contact_mechanisms = OneToMany('PartyContactMechanism', lazy=True)
  shares = OneToMany('SharedShareholder', inverse='established_to')
  directed_organizations = OneToMany('DirectedDirector', inverse='established_to')
    
  @property
  def name(self):
    return unicode(self)
  
  class Admin(EntityAdmin):
    name = 'Parties'
    list_display = ['name']
    list_size = (1000, 700)
    fields = ['addresses', 'contact_mechanisms', 'shares', 'directed_organizations']
    field_attributes = dict(suppliers={'admin':SupplierCustomer.SupplierAdmin}, 
                            customers={'admin':SupplierCustomer.CustomerAdmin},
                            employers={'admin':EmployerEmployee.EmployerAdmin},
                            employees={'admin':EmployerEmployee.EmployeeAdmin},
                            directed_organizations={'admin':DirectedDirector.DirectedAdmin},
                            directors={'admin':DirectedDirector.DirectorAdmin},
                            shares={'admin':SharedShareholder.SharedAdmin},
                            shareholders={'admin':SharedShareholder.ShareholderAdmin},
                            sex=dict(choices=lambda obj:[(u'M',u'Male'), (u'F',u'Female')],),
                            name=dict(minimal_column_width=50),
                            )
      
class Organization(Party):
  """An organization represents any internal or external organization.  Organizations can include
  businesses and groups of individuals"""
  using_options(tablename='organization', inheritance='multi')
  name = Field(Unicode(50), required=True, index=True)
  logo = Field(camelot.types.Image(upload_to='organization-logo'), deferred=True)
  tax_id = Field(Unicode(20))
  directors = OneToMany('DirectedDirector', inverse='established_from')
  employees = OneToMany('EmployerEmployee', inverse='established_from')
  suppliers = OneToMany('SupplierCustomer', inverse='established_to')
  customers = OneToMany('SupplierCustomer', inverse='established_from')
  shareholders = OneToMany('SharedShareholder', inverse='established_from')
  
  def __unicode__(self):
    return self.name
  
  def __repr__(self):
    return self.name
  
  @property
  def number_of_shares_issued(self):
    return sum((shareholder.shares for shareholder in self.shareholders), 0)
  
  class Admin(Party.Admin):
    name = 'Organizations'
    section = 'relations'
    list_display = ['name', 'tax_id',]
    form_display = TabForm([('Basic', Form(['name', 'tax_id', 'addresses', 'contact_mechanisms'])),
                            ('Employment', Form(['employees'])),
                            ('Customers', Form(['customers'])),
                            ('Suppliers', Form(['suppliers'])),
                            ('Corporate', Form(['directors', 'shareholders', 'shares'])),
                            ('Branding', Form(['logo'])), ])

class AuthenticationMechanism(Entity):
  using_options(tablename='authentication_mechanism')
  last_login = Field(DateTime(), default=datetime.datetime.now)
  is_active = Field(Boolean, default=True, index=True)
  
  class Admin(EntityAdmin):
    name = 'Authentication mechanism'
  
class UsernameAuthenticationMechanism(AuthenticationMechanism):
  using_options(tablename='authentication_mechanism_username', inheritance='multi')
  username = Field(Unicode(40), required=True, index=True, unique=True)
  password = Field(Unicode(200), required=False, index=False, default=None)
  
  @classmethod
  def getOrCreateAuthentication(cls, username):
    authentication = cls.query.filter_by(username=username).first()
    if not authentication:
      authentication = cls(username=username)
      from elixir import session
      session.flush([authentication])
    return authentication
  
  def __unicode__(self):
    return self.username
  
  class Admin(EntityAdmin):
    name = 'Authentication mechanism'
    list_display = ['username', 'last_login', 'is_active']
  
class Person(Party):
  """Person represents natural persons, these can be given access to the system
  and as such require a username.
  
  Username is required, other fields are optional, there is no password because
  authentication is supposed to happen through the operating system services or
  other.
  """
  using_options(tablename='person', inheritance='multi')
  first_name = Field(Unicode(40))
  last_name =  Field(Unicode(40))
  middle_name = Field(Unicode(40))
  personal_title = Field(Unicode(10))
  suffix = Field(Unicode(3))
  sex = Field(Unicode(1), default=u'M')
  birthdate = Field(Date())
  martial_status = Field(Unicode(1))
  social_security_number = Field(Unicode(12))
  passport_number = Field(Unicode(20))
  passport_expiry_date = Field(Date())
  is_staff = Field(Boolean, default=False, index=True)
  is_superuser = Field(Boolean, default=False, index=True)
  picture = Field(camelot.types.Image(upload_to='person-pictures'), deferred=True)
  comment = Field(camelot.types.RichText())
  employers = OneToMany('EmployerEmployee', inverse='established_to')
      
  @property
  def name(self):
    if self.last_name and self.first_name:
      return u'%s %s'%(self.first_name, self.last_name)
    else:
      return self.username
  
  def __repr__(self):
    return self.name
  
  def __unicode__(self):
    return self.name

  class Admin(Party.Admin):
    name = 'Persons'
    section = 'relations'
    list_display = ['first_name', 'last_name', ]
    form_display = TabForm([('Basic', Form([HBoxForm([Form(['first_name', 'last_name', 'sex']),
                                                      Form(['picture',]),
                                                     ]), 
                                                     'contact_mechanisms',  'comment',], scrollbars=True)),
                            ('Official', Form(['birthdate', 'social_security_number', 'passport_number','passport_expiry_date','addresses',], scrollbars=True)),
                            ('Work', Form(['employers', 'directed_organizations', 'shares'], scrollbars=True))
                            ])
    
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
    form_size = (700,150)
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
    form_size = (700,150)
    list_display = ['code', 'name', 'country']
    
class Address(Entity):
  using_options(tablename='address')
  street1 = Field(Unicode(128), required=True)
  street2 = Field(Unicode(128))
  city = ManyToOne('City', required=True, ondelete='cascade', onupdate='cascade')
  is_synchronized('synchronized', lazy=True)
  
  def __unicode__(self):
    return u'%s, %s'%(self.street1, self.city)
  
  def showMap(self):
    from PyQt4 import QtGui, QtCore
    QtGui.QDesktopServices.openUrl (QtCore.QUrl('http://www.google.be/maps?f=q&source=s_q&geocode=%s&q=%s+%s'%(self.city.country.code, self.street1, self.city.name))) 
  
  class Admin(EntityAdmin):
    name = 'Addresses'
    list_display = ['street1', 'street2', 'city']
    form_size = (700,150)
    form_actions = [('Show map',lambda address:address.showMap())]
  
class PartyAddressRoleType(Entity):
  using_options(tablename='party_address_role_type')
  code = Field(Unicode(10))
  description = Field(Unicode(40))
  
  class Admin(EntityAdmin):
    name = 'Address role type'
    list_display = ['code', 'description']
  
class PartyAuthentication(Entity):
  using_options(tablename='party_authentication')
  address = ManyToOne('AuthenticationMechanism', required=True, ondelete='cascade', onupdate='cascade')
  from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
  thru_date = Field(Date(), default=end_of_times, required=True, index=True)
  comment = Field(Unicode(256))
    
class PartyAddress(Entity):
  using_options(tablename='party_address')
  party = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
  address = ManyToOne('Address', required=True, ondelete='cascade', onupdate='cascade')
  from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
  thru_date = Field(Date(), default=end_of_times, required=True, index=True)
  comment = Field(Unicode(256))
  
  def __unicode__(self):
    return '%s : %s'%(unicode(self.party), unicode(self.address))
  
  def showMap(self):
    if self.address:
      self.address.showMap()
  
  class Admin(EntityAdmin):
    name = 'Address'
    list_display = ['address', 'comment']
    fields = ['address', 'comment', 'from_date', 'thru_date']
    form_size = (700,200)
    form_actions = [('Show map',lambda address:address.showMap())]
    
class ContactMechanism(Entity):
  using_options(tablename='contact_mechanism')
  mechanism = Field(camelot.types.VirtualAddress(256), required=True)
  party_address = ManyToOne('PartyAddress', ondelete='set null', onupdate='cascade')
  
  def __unicode__(self):
    if self.mechanism:
      return u'%s : %s'%(self.mechanism[0], self.mechanism[1])
  
  class Admin(EntityAdmin):
    form_size = (700,150)
    name = 'Contact mechanism'
    list_display = ['mechanism']
    form = Form(['mechanism', 'party_address'])

class PartyContactMechanism(Entity):
  using_options(tablename='party_contact_mechanism')
  party = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
  contact_mechanism = ManyToOne('ContactMechanism', required=True, ondelete='cascade', onupdate='cascade')
  from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
  thru_date = Field(Date(), default=end_of_times, index=True)
  comment = Field(Unicode(256))

  def __unicode__(self):
    return unicode(self.contact_mechanism)
  
  class Admin(EntityAdmin):
    form_size = (700,200)
    name = 'Party contact mechanisms'
    list_display = ['contact_mechanism', 'comment', 'from_date',]
    form_display = Form(['contact_mechanism', 'comment', 'from_date', 'thru_date',])
