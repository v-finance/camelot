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
from camelot.model import metadata
from camelot.model import entities
from elixir.entity import Entity
from elixir.options import using_options
from elixir.fields import Field
from sqlalchemy.types import Date, Unicode, Integer, DateTime, Boolean
from elixir.relationships import ManyToOne, OneToMany
from elixir.properties import ColumnProperty
from sqlalchemy.sql.expression import and_
"""Set of classes to store persons, organizations, relationships and
permissions

These structures are modeled like described in 'The Data Model Resource Book'
by Len Silverston, Chapter 2
"""
from sqlalchemy import sql
from sqlalchemy.orm import aliased

import camelot.types

#from camelot.model import *

__metadata__ = metadata

from camelot.model.synchronization import is_synchronized
from camelot.core.document import documented_entity
from camelot.core.utils import ugettext_lazy as _

from camelot.view.elixir_admin import EntityAdmin
from camelot.view.forms import Form, TabForm, HBoxForm
from camelot.admin.form_action import FormActionFromModelFunction
import datetime
import threading


_current_authentication_ = threading.local()

def end_of_times():
    return datetime.date( year = 2400, month = 12, day = 31 )

from camelot.model.type_and_status import type_3_status

def getCurrentAuthentication():
    """Get the currently logged in person"""
    global _current_authentication_
    if not hasattr( _current_authentication_, 'mechanism' ):
        import getpass
        _current_authentication_.mechanism = UsernameAuthenticationMechanism.getOrCreateAuthentication( unicode( getpass.getuser() ) )
    return _current_authentication_.mechanism

def updateLastLogin():
    """Update the last login of the current person to now"""
    from elixir import session
    authentication = getCurrentAuthentication()
    authentication.last_login = datetime.datetime.now()
    session.flush( [authentication] )

class PartyRelationship( Entity ):
    using_options( tablename = 'party_relationship' )
    from_date = Field( Date(), default = datetime.date.today, required = True, index = True )
    thru_date = Field( Date(), default = end_of_times, required = True, index = True )
    comment = Field( camelot.types.RichText() )
    is_synchronized( 'synchronized', lazy = True )

    class Admin( EntityAdmin ):
        name = 'Relationship'
        list_display = ['from_date', 'thru_date']

class EmployerEmployee( PartyRelationship ):
    """Relation from employer to employee"""
    using_options( tablename = 'party_relationship_empl', inheritance = 'multi' )
    established_from = ManyToOne( 'Organization', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    established_to = ManyToOne( 'Person', required = True, ondelete = 'cascade', onupdate = 'cascade' )

    @ColumnProperty
    def first_name( self ):
        return sql.select( [Person.first_name], Person.party_id == self.established_to_party_id )

    @ColumnProperty
    def last_name( self ):
        return sql.select( [Person.last_name], Person.party_id == self.established_to_party_id )

    @ColumnProperty
    def social_security_number( self ):
        return sql.select( [Person.social_security_number], Person.party_id == self.established_to_party_id )

    def __unicode__( self ):
        return u'%s %s %s' % ( unicode( self.established_to ), _('employed by'),unicode( self.established_from ) )

    class Admin( EntityAdmin ):
        name = 'Employer - Employee'
        list_display = ['established_from', 'established_to', 'from_date', 'thru_date']

    class EmployeeAdmin( EntityAdmin ):
        verbose_name = 'Employee'
        list_display = ['established_to', 'from_date', 'thru_date']
        form_display = ['established_to', 'comment', 'from_date', 'thru_date']
        field_attributes = {'established_to':{'name':_( 'name' )}}

    class EmployerAdmin( EntityAdmin ):
        verbose_name = 'Employer'
        list_display = ['established_from', 'from_date', 'thru_date']
        form_display = ['established_from', 'comment', 'from_date', 'thru_date']
        field_attributes = {'established_from':{'name':_( 'name' )}}

class DirectedDirector( PartyRelationship ):
    """Relation from a directed organization to a director"""
    using_options( tablename = 'party_relationship_dir', inheritance = 'multi' )
    established_from = ManyToOne( 'Organization', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    established_to = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    title = Field( Unicode( 256 ) )
    represented_by = OneToMany( 'RepresentedRepresentor', inverse = 'established_to' )

    class Admin( EntityAdmin ):
        verbose_name = 'Directed - Director'
        list_display = ['established_from', 'established_to', 'from_date', 'thru_date']

    class DirectorAdmin( EntityAdmin ):
        verbose_name = 'Director'
        list_display = ['established_to', 'from_date', 'thru_date']
        fields = ['established_to', 'title', 'from_date', 'thru_date', 'represented_by', 'comment']
        field_attributes = {'established_to':{'name':_( 'name' )}}

    class DirectedAdmin( EntityAdmin ):
        verbose_name = 'Directed organization'
        list_display = ['established_from', 'from_date', 'thru_date']
        fields = ['established_from', 'from_date', 'thru_date', 'represented_by', 'comment']
        field_attributes = {'established_from':{'name':_( 'name' )}}

class RepresentedRepresentor( Entity ):
    """Relation from a representing party to the person representing the party"""
    using_options( tablename = 'party_representor' )
    from_date = Field( Date(), default = datetime.date.today, required = True, index = True )
    thru_date = Field( Date(), default = end_of_times, required = True, index = True )
    comment = Field( camelot.types.RichText() )
    established_from = ManyToOne( 'Person', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    established_to = ManyToOne( 'DirectedDirector', required = True, ondelete = 'cascade', onupdate = 'cascade' )

    class Admin( EntityAdmin ):
        verbose_name = 'Represented by'
        list_display = ['established_from', 'from_date', 'thru_date']
        form_display = ['established_from', 'from_date', 'thru_date', 'comment']
        field_attributes = {'established_from':{'name':_( 'name' )}}

class SupplierCustomer( PartyRelationship ):
    """Relation from supplier to customer"""
    using_options( tablename = 'party_relationship_suppl', inheritance = 'multi' )
    established_from = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    established_to = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )

    class Admin( EntityAdmin ):
        verbose_name = 'Supplier - Customer'
        list_display = ['established_from', 'established_to', 'from_date', 'thru_date']

    class CustomerAdmin( EntityAdmin ):
        verbose_name = 'Customer'
        list_display = ['established_to', ]
        fields = ['established_to', 'comment', 'from_date', 'thru_date']
        field_attributes = {'established_to':{'name':_( 'name' )}}

    class SupplierAdmin( EntityAdmin ):
        verbose_name = 'Supplier'
        list_display = ['established_from', ]
        fields = ['established_from', 'comment', 'from_date', 'thru_date']
        field_attributes = {'established_from':{'name':_( 'name' )}}

class SharedShareholder( PartyRelationship ):
    """Relation from a shared organization to a shareholder"""
    using_options( tablename = 'party_relationship_shares', inheritance = 'multi' )
    established_from = ManyToOne( 'Organization', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    established_to = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    shares = Field( Integer() )

    class Admin( EntityAdmin ):
        verbose_name = 'Shared - Shareholder'
        list_display = ['established_from', 'established_to', 'from_date', 'thru_date']

    class ShareholderAdmin( EntityAdmin ):
        verbose_name = 'Shareholder'
        list_display = ['established_to', 'shares', 'from_date', 'thru_date']
        fields = ['established_to', 'shares', 'from_date', 'thru_date', 'comment']
        field_attributes = {'established_to':{'name':'shareholder name'}}

    class SharedAdmin( EntityAdmin ):
        verbose_name = 'Shares'
        verbose_name_plural = 'Shares'
        list_display = ['established_from', 'shares', 'from_date', 'thru_date']
        fields = ['established_from', 'shares', 'from_date', 'thru_date', 'comment']
        field_attributes = {'established_from':{'name':_( 'name' )}}

class AddressAdmin( EntityAdmin ):
    """Admin with only the Address information and not the Party information"""
    list_display = ['address', 'comment']
    form_display = ['address', 'comment', 'from_date', 'thru_date']
    
class PartyContactMechanismAdmin( EntityAdmin ):
    form_size = ( 700, 200 )
    verbose_name = 'Contact mechanism'
    list_search = ['party_name', 'mechanism']
    list_display = ['party_name', 'mechanism', 'comment', 'from_date', ]
    form_display = Form( ['contact_mechanism', 'comment', 'from_date', 'thru_date', ] )
    field_attributes = {'party_name':{'minimal_column_width':25, 'editable':False},
                        'mechanism':{'minimal_column_width':25,'editable':False}}
  
class PartyPartyContactMechanismAdmin( PartyContactMechanismAdmin ):
    list_search = ['party_name', 'mechanism']
    list_display = ['contact_mechanism', 'comment', 'from_date', ]
                
class Party( Entity ):
    """Base class for persons and organizations.  Use this base class to refer to either persons or
    organisations in building authentication systems, contact management or CRM"""
    using_options( tablename = 'party' )
    is_synchronized( 'synchronized', lazy = True )
    addresses = OneToMany( 'PartyAddress', lazy = True )
    contact_mechanisms = OneToMany( 'PartyContactMechanism', lazy = True )
    shares = OneToMany( 'SharedShareholder', inverse = 'established_to' )
    directed_organizations = OneToMany( 'DirectedDirector', inverse = 'established_to' )
    status = OneToMany( type_3_status( 'Party', metadata, entities ) )

    @property
    def name( self ):
        return ''

    @ColumnProperty
    def email( self ):
        
        cm = ContactMechanism
        pcm = PartyContactMechanism
        
        return sql.select( [cm.mechanism],
                          whereclause = and_( pcm.table.c.party_id == self.id,
                                           cm.table.c.mechanism.like( ( u'email', u'%' ) ) ),
                          from_obj = [cm.table.join( pcm.table )] ).limit(1)

    @ColumnProperty
    def phone( self ):
        
        cm = ContactMechanism
        pcm = PartyContactMechanism
                
        return sql.select( [cm.mechanism],
                          whereclause = and_( pcm.table.c.party_id == self.id,
                                           cm.table.c.mechanism.like( ( u'phone', u'%' ) ) ),
                          from_obj = [cm.table.join( pcm.table )] ).limit(1)

    @ColumnProperty
    def full_name( self ):
        aliased_organisation = Organization.table.alias( 'organisation_alias' )
        aliased_person = Person.table.alias( 'person_alias' )
        aliased_party = Party.table.alias( 'party_alias' )
        return sql.functions.coalesce( sql.select( [aliased_person.c.first_name + ' ' + aliased_person.c.last_name],
                                                  whereclause = and_( aliased_party.c.id == self.id ),
                                                  from_obj = [aliased_party.join( aliased_person, aliased_person.c.party_id == aliased_party.c.id )] ).limit( 1 ).as_scalar(),
                                      sql.select( [aliased_organisation.c.name],
                                                 whereclause = and_( aliased_party.c.id == self.id ),
                                                 from_obj = [aliased_party.join( aliased_organisation, aliased_organisation.c.party_id == aliased_party.c.id )] ).limit( 1 ).as_scalar() )

    class Admin( EntityAdmin ):
        verbose_name = 'Party'
        verbose_name_plural = 'Parties'
        list_display = ['name', 'email', 'phone'] # don't use full name, since it might be None for new objects
        list_search = ['full_name']
        fields = ['addresses', 'contact_mechanisms', 'shares', 'directed_organizations']
        field_attributes = dict(addresses = {'admin':AddressAdmin},
                                contact_mechanisms = {'admin':PartyPartyContactMechanismAdmin}, 
                                suppliers = {'admin':SupplierCustomer.SupplierAdmin},
                                customers = {'admin':SupplierCustomer.CustomerAdmin},
                                employers = {'admin':EmployerEmployee.EmployerAdmin},
                                employees = {'admin':EmployerEmployee.EmployeeAdmin},
                                directed_organizations = {'admin':DirectedDirector.DirectedAdmin},
                                directors = {'admin':DirectedDirector.DirectorAdmin},
                                shares = {'admin':SharedShareholder.SharedAdmin},
                                shareholders = {'admin':SharedShareholder.ShareholderAdmin},
                                sex = dict( choices = lambda obj:[( u'M', u'Male' ), ( u'F', u'Female' )], ),
                                name = dict( minimal_column_width = 50 ),
                                email = dict( editable = False, minimal_column_width = 20 ),
                                phone = dict( editable = False, minimal_column_width = 20 )
                                )

class Organization( Party ):
    """An organization represents any internal or external organization.  Organizations can include
    businesses and groups of individuals"""
    using_options( tablename = 'organization', inheritance = 'multi' )
    name = Field( Unicode( 50 ), required = True, index = True )
    logo = Field( camelot.types.Image( upload_to = 'organization-logo' ), deferred = True )
    tax_id = Field( Unicode( 20 ) )
    directors = OneToMany( 'DirectedDirector', inverse = 'established_from' )
    employees = OneToMany( 'EmployerEmployee', inverse = 'established_from' )
    suppliers = OneToMany( 'SupplierCustomer', inverse = 'established_to' )
    customers = OneToMany( 'SupplierCustomer', inverse = 'established_from' )
    shareholders = OneToMany( 'SharedShareholder', inverse = 'established_from' )

    def __unicode__( self ):
        return self.name

    @property
    def number_of_shares_issued( self ):
        return sum( ( shareholder.shares for shareholder in self.shareholders ), 0 )

    class Admin( Party.Admin ):
        verbose_name = _( 'organization' )
        verbose_name_plural = _( 'organizations' )
        section = 'relations'
        list_display = ['name', 'tax_id', 'email', 'phone']
        form_display = TabForm( [( 'Basic', Form( ['name', 'tax_id', 'addresses', 'contact_mechanisms'] ) ),
                                ( 'Employment', Form( ['employees'] ) ),
                                ( 'Customers', Form( ['customers'] ) ),
                                ( 'Suppliers', Form( ['suppliers'] ) ),
                                ( 'Corporate', Form( ['directors', 'shareholders', 'shares'] ) ),
                                ( 'Branding', Form( ['logo'] ) ),
                                ( 'Status', Form( ['status'] ) ),
                                ] )

Organization = documented_entity()( Organization )


        
class AuthenticationMechanism( Entity ):
    using_options( tablename = 'authentication_mechanism' )
    last_login = Field( DateTime() )
    is_active = Field( Boolean, default = True, index = True )

    class Admin( EntityAdmin ):
        verbose_name = 'Authentication mechanism'
        list_display = ['last_login', 'is_active']

class UsernameAuthenticationMechanism( AuthenticationMechanism ):
    using_options( tablename = 'authentication_mechanism_username', inheritance = 'multi' )
    username = Field( Unicode( 40 ), required = True, index = True, unique = True )
    password = Field( Unicode( 200 ), required = False, index = False, default = None )

    @classmethod
    def getOrCreateAuthentication( cls, username ):
        authentication = cls.query.filter_by( username = username ).first()
        if not authentication:
            authentication = cls( username = username )
            from elixir import session
            session.flush( [authentication] )
        return authentication

    def __unicode__( self ):
        return self.username

    class Admin( EntityAdmin ):
        verbose_name = 'Authentication mechanism'
        list_display = ['username', 'last_login', 'is_active']

class Person( Party ):
    """Person represents natural persons
    """
    using_options( tablename = 'person', inheritance = 'multi' )
    first_name = Field( Unicode( 40 ), required = True )
    last_name = Field( Unicode( 40 ), required = True )
    middle_name = Field( Unicode( 40 ) )
    personal_title = Field( Unicode( 10 ) )
    suffix = Field( Unicode( 3 ) )
    sex = Field( Unicode( 1 ), default = u'M' )
    birthdate = Field( Date() )
    martial_status = Field( Unicode( 1 ) )
    social_security_number = Field( Unicode( 12 ) )
    passport_number = Field( Unicode( 20 ) )
    passport_expiry_date = Field( Date() )
    is_staff = Field( Boolean, default = False, index = True )
    is_superuser = Field( Boolean, default = False, index = True )
    picture = Field( camelot.types.Image( upload_to = 'person-pictures' ), deferred = True )
    comment = Field( camelot.types.RichText() )
    employers = OneToMany( 'EmployerEmployee', inverse = 'established_to' )

    @property
    def name( self ):
        # we don't use full name in here, because for new objects, full name will be None, since
        # it needs to be fetched from the db first
        return u'%s %s' % ( self.first_name, self.last_name )

    def __unicode__( self ):
        return self.name

    class Admin( Party.Admin ):
        verbose_name = _( 'person' )
        verbose_name_plural = _( 'persons' )
        list_display = ['first_name', 'last_name', 'email', 'phone']
        form_display = TabForm( [( 'Basic', Form( [HBoxForm( [Form( ['first_name', 'last_name', 'sex'] ),
                                                          Form( ['picture', ] ),
                                                         ] ),
                                                         'contact_mechanisms', 'comment', ], scrollbars = True ) ),
                                ( 'Official', Form( ['birthdate', 'social_security_number', 'passport_number', 'passport_expiry_date', 'addresses', ], scrollbars = True ) ),
                                ( 'Work', Form( ['employers', 'directed_organizations', 'shares'], scrollbars = True ) ),
                                ( 'Status', Form( ['status'] ) ),
                                ] )

Person = documented_entity()( Person )

class GeographicBoundary( Entity ):
    using_options( tablename = 'geographic_boundary' )
    code = Field( Unicode( 10 ) )
    name = Field( Unicode( 40 ), required = True )

    @ColumnProperty
    def full_name( self ):
        return self.code + ' ' + self.name
        
    def __unicode__( self ):
        return u'%s %s' % ( self.code, self.name )

class Country( GeographicBoundary ):
    using_options( tablename = 'geographic_boundary_country', inheritance = 'multi' )

    @classmethod
    def getOrCreate( cls, code, name ):
        country = Country.query.filter_by( code = code ).first()
        if not country:
            from elixir import session
            country = Country( code = code, name = name )
            session.flush( [country] )
        return country

    class Admin( EntityAdmin ):
        form_size = ( 700, 150 )
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'
        list_display = ['name', 'code']

class City( GeographicBoundary ):
    using_options( tablename = 'geographic_boundary_city', inheritance = 'multi' )
    country = ManyToOne( 'Country', required = True, ondelete = 'cascade', onupdate = 'cascade' )

    @classmethod
    def getOrCreate( cls, country, code, name ):
        city = City.query.filter_by( code = code, country = country ).first()
        if not city:
            from elixir import session
            city = City( code = code, name = name, country = country )
            session.flush( [city] )
        return city

    class Admin( EntityAdmin ):
        verbose_name = 'City'
        verbose_name_plural = 'Cities'
        form_size = ( 700, 150 )
        list_display = ['code', 'name', 'country']

class Address( Entity ):
    using_options( tablename = 'address' )
    street1 = Field( Unicode( 128 ), required = True )
    street2 = Field( Unicode( 128 ) )
    city = ManyToOne( 'City', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    is_synchronized( 'synchronized', lazy = True )

    @ColumnProperty
    def name( self ):
        return sql.select( [self.street1 + ', ' + GeographicBoundary.full_name],
                           whereclause = (GeographicBoundary.id==self.city_geographicboundary_id)) 
    
    @classmethod
    def getOrCreate( cls, street1, street2, city ):
        address = cls.query.filter_by( street1 = street1, street2 = street2, city = city ).first()
        if not address:
            from elixir import session
            address = cls( street1 = street1, street2 = street2, city = city )
            session.flush( [address] )
        return address

    def __unicode__( self ):
        return u'%s, %s' % ( self.street1 or '', self.city or '' )

    def showMap( self ):
        from PyQt4 import QtGui, QtCore
        QtGui.QDesktopServices.openUrl ( QtCore.QUrl( 'http://www.google.be/maps?f=q&source=s_q&geocode=%s&q=%s+%s' % ( self.city.country.code, self.street1, self.city.name ) ) )

    class Admin( EntityAdmin ):
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        list_display = ['street1', 'street2', 'city']
        form_size = ( 700, 150 )
        field_attributes = {'street1':{'minimal_column_width':30}}
        form_actions = [FormActionFromModelFunction( 'Show on map', lambda address:address.showMap() )]

Address = documented_entity()( Address )

class PartyAddress( Entity ):
    using_options( tablename = 'party_address' )
    party = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    address = ManyToOne( 'Address', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    from_date = Field( Date(), default = datetime.date.today, required = True, index = True )
    thru_date = Field( Date(), default = end_of_times, required = True, index = True )
    comment = Field( Unicode( 256 ) )

    @ColumnProperty
    def party_name( self ):
        return sql.select( [Party.full_name],
                           whereclause = (Party.id==self.party_id))
        
    @ColumnProperty
    def address_name( self ):
        return sql.select( [Address.name],
                           whereclause = (Address.id==self.address_id))        
                          
    def __unicode__( self ):
        return '%s : %s' % ( unicode( self.party ), unicode( self.address ) )

    def showMap( self ):
        if self.address:
            self.address.showMap()

    class Admin( EntityAdmin ):
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        list_search = ['party_name', 'address_name']
        list_display = ['party_name', 'address_name', 'comment']
        form_display = ['party', 'address', 'comment', 'from_date', 'thru_date']
        form_size = ( 700, 200 )
        form_actions = [FormActionFromModelFunction( 'Show on map', lambda address:address.showMap() )]
        field_attributes = dict(party_name=dict(editable=False, name='Party', minimal_column_width=30),
                                address_name=dict(editable=False, name='Address', minimal_column_width=30))
        
class PartyAddressRoleType( Entity ):
    using_options( tablename = 'party_address_role_type' )
    code = Field( Unicode( 10 ) )
    description = Field( Unicode( 40 ) )

    class Admin( EntityAdmin ):
        verbose_name = 'Address role type'
        list_display = ['code', 'description']

class PartyAuthentication( Entity ):
    using_options( tablename = 'party_authentication' )
    address = ManyToOne( 'AuthenticationMechanism', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    from_date = Field( Date(), default = datetime.date.today, required = True, index = True )
    thru_date = Field( Date(), default = end_of_times, required = True, index = True )
    comment = Field( Unicode( 256 ) )

class ContactMechanism( Entity ):
    using_options( tablename = 'contact_mechanism' )
    mechanism = Field( camelot.types.VirtualAddress( 256 ), required = True )
    party_address = ManyToOne( 'PartyAddress', ondelete = 'set null', onupdate = 'cascade' )

    def __unicode__( self ):
        if self.mechanism:
            return u'%s : %s' % ( self.mechanism[0], self.mechanism[1] )

    class Admin( EntityAdmin ):
        form_size = ( 700, 150 )
        verbose_name = 'Contact mechanism'
        list_display = ['mechanism']
        form_display = Form( ['mechanism', 'party_address'] )
        field_attributes = {'mechanism':{'minimal_column_width':25}}

ContactMechanism = documented_entity()( ContactMechanism )

class PartyContactMechanism( Entity ):
    using_options( tablename = 'party_contact_mechanism' )
    party = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    contact_mechanism = ManyToOne( 'ContactMechanism', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    from_date = Field( Date(), default = datetime.date.today, required = True, index = True )
    thru_date = Field( Date(), default = end_of_times, index = True )
    comment = Field( Unicode( 256 ) )

    @ColumnProperty
    def mechanism( self ):
        return sql.select( [ContactMechanism.mechanism],
                           whereclause = (ContactMechanism.id==self.contact_mechanism_id))
        
    @ColumnProperty
    def party_name( self ):
        return sql.select( [Party.full_name],
                           whereclause = (Party.id==self.party_id))        
        
    def __unicode__( self ):
        return unicode( self.contact_mechanism )

    Admin = PartyContactMechanismAdmin

