#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Set of classes to store persons, organizations, relationships and
contact mechanisms

These structures are modeled like described in 'The Data Model Resource Book'
by Len Silverston, Chapter 2
"""

import collections

from camelot.core.sql import metadata
from elixir import entities
from camelot.view.controls import delegates

from elixir import Entity, using_options, Field, ManyToMany
from sqlalchemy.types import Date, Unicode, Integer, Boolean
from elixir.relationships import ManyToOne, OneToMany
from elixir.properties import ColumnProperty
from sqlalchemy.sql.expression import and_

from sqlalchemy import sql

import camelot.types

__metadata__ = metadata

from camelot.core.document import documented_entity
from camelot.core.utils import ugettext_lazy as _

from camelot.admin.entity_admin import EntityAdmin
from camelot.view.forms import Form, TabForm, HBoxForm, WidgetOnlyForm
import datetime
import threading

_current_authentication_ = threading.local()

from authentication import end_of_times

from camelot.model.type_and_status import type_3_status

class GeographicBoundary( Entity ):
    """The base class for Country and City"""
    using_options( tablename = 'geographic_boundary' )
    code = Field( Unicode( 10 ) )
    name = Field( Unicode( 40 ), required = True )

    @ColumnProperty
    def full_name( self ):
        return self.code + ' ' + self.name

    def __unicode__( self ):
        return u'%s %s' % ( self.code, self.name )

class Country( GeographicBoundary ):
    """A subclass of GeographicBoundary used to store the name and the
    ISO code of a country"""
    using_options( tablename = 'geographic_boundary_country', inheritance = 'multi' )

    @classmethod
    def get_or_create( cls, code, name ):
        country = Country.query.filter_by( code = code ).first()
        if not country:
            from elixir import session
            country = Country( code = code, name = name )
            session.flush( [country] )
        return country

    class Admin( EntityAdmin ):
        form_size = ( 700, 150 )
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        list_display = ['name', 'code']

Country = documented_entity()(Country)

class City( GeographicBoundary ):
    """A subclass of GeographicBoundary used to store the name, the postal code
    and the Country of a city"""
    using_options( tablename = 'geographic_boundary_city', inheritance = 'multi' )
    country = ManyToOne( 'Country', required = True, ondelete = 'cascade', onupdate = 'cascade' )

    @classmethod
    def get_or_create( cls, country, code, name ):
        city = City.query.filter_by( code = code, country = country ).first()
        if not city:
            from elixir import session
            city = City( code = code, name = name, country = country )
            session.flush( [city] )
        return city

    class Admin( EntityAdmin ):
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
        form_size = ( 700, 150 )
        list_display = ['code', 'name', 'country']

City = documented_entity()(City)

class PartyRelationship( Entity ):
    using_options( tablename = 'party_relationship' )
    from_date = Field( Date(), default = datetime.date.today, required = True, index = True )
    thru_date = Field( Date(), default = end_of_times, required = True, index = True )
    comment = Field( camelot.types.RichText() )

    class Admin( EntityAdmin ):
        verbose_name = _('Relationship')
        verbose_name_plural = _('Relationships')
        list_display = ['from_date', 'thru_date']

class EmployerEmployee( PartyRelationship ):
    """Relation from employer to employee"""
    using_options( tablename = 'party_relationship_empl', inheritance = 'multi' )
    established_from = ManyToOne( 'Organization', required = True, ondelete = 'cascade', onupdate = 'cascade' )    # the employer
    established_to = ManyToOne( 'Person', required = True, ondelete = 'cascade', onupdate = 'cascade' )            # the employee

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
        return u'%s %s %s' % ( unicode( self.established_to ), _('Employed by'),unicode( self.established_from ) )

    class Admin( PartyRelationship.Admin ):
        verbose_name = _('Employment relation')
        verbose_name_plural = _('Employment relations')
        list_filter = ['established_from.name']
        list_search = ['established_from.name', 'established_to.first_name', 'established_to.last_name']

    class EmployeeAdmin( EntityAdmin ):
        verbose_name = _('Employee')
        list_display = ['established_to', 'from_date', 'thru_date']
        form_display = ['established_to', 'comment', 'from_date', 'thru_date']
        field_attributes = {'established_to':{'name':_( 'Name' )}}

    class EmployerAdmin( EntityAdmin ):
        verbose_name = _('Employer')
        list_display = ['established_from', 'from_date', 'thru_date']
        form_display = ['established_from', 'comment', 'from_date', 'thru_date']
        field_attributes = {'established_from':{'name':_( 'Name' )}}

class DirectedDirector( PartyRelationship ):
    """Relation from a directed organization to a director"""
    using_options( tablename = 'party_relationship_dir', inheritance = 'multi' )
    established_from = ManyToOne( 'Organization', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    established_to = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    title = Field( Unicode( 256 ) )
    represented_by = OneToMany( 'RepresentedRepresentor', inverse = 'established_to' )

    class Admin( PartyRelationship.Admin ):
        verbose_name = _('Direction structure')
        verbose_name_plural = _('Direction structures')
        list_display = ['established_from', 'established_to', 'title', 'represented_by']
        list_search = ['established_from.full_name', 'established_to.full_name']
        field_attributes = {'established_from':{'name':_('Organization')},
                            'established_to':{'name':_('Director')}}

    class DirectorAdmin( Admin ):
        verbose_name = _('Director')
        list_display = ['established_to', 'title', 'from_date', 'thru_date']
        form_display = ['established_to', 'title', 'from_date', 'thru_date', 'represented_by', 'comment']

    class DirectedAdmin( Admin ):
        verbose_name = _('Directed organization')
        list_display = ['established_from', 'title', 'from_date', 'thru_date']
        form_display = ['established_from', 'title', 'from_date', 'thru_date', 'represented_by', 'comment']

class RepresentedRepresentor( Entity ):
    """Relation from a representing party to the person representing the party"""
    using_options( tablename = 'party_representor' )
    from_date = Field( Date(), default = datetime.date.today, required = True, index = True )
    thru_date = Field( Date(), default = end_of_times, required = True, index = True )
    comment = Field( camelot.types.RichText() )
    established_from = ManyToOne( 'Person', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    established_to = ManyToOne( 'DirectedDirector', required = True, ondelete = 'cascade', onupdate = 'cascade' )

    class Admin( EntityAdmin ):
        verbose_name = _('Represented by')
        list_display = ['established_from', 'from_date', 'thru_date']
        form_display = ['established_from', 'from_date', 'thru_date', 'comment']
        field_attributes = {'established_from':{'name':_( 'Name' )}}

class SupplierCustomer( PartyRelationship ):
    """Relation from supplier to customer"""
    using_options( tablename = 'party_relationship_suppl', inheritance = 'multi' )
    established_from = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    established_to = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )

    class Admin( PartyRelationship.Admin ):
        verbose_name = _('Supplier - Customer')
        list_display = ['established_from', 'established_to', 'from_date', 'thru_date']

    class CustomerAdmin( EntityAdmin ):
        verbose_name = _('Customer')
        list_display = ['established_to', ]
        form_display = ['established_to', 'comment', 'from_date', 'thru_date']
        field_attributes = {'established_to':{'name':_( 'Name' )}}

    class SupplierAdmin( EntityAdmin ):
        verbose_name = _('Supplier')
        list_display = ['established_from', ]
        form_display = ['established_from', 'comment', 'from_date', 'thru_date']
        field_attributes = {'established_from':{'name':_( 'Name' )}}

class SharedShareholder( PartyRelationship ):
    """Relation from a shared organization to a shareholder"""
    using_options( tablename = 'party_relationship_shares', inheritance = 'multi' )
    established_from = ManyToOne( 'Organization', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    established_to = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    shares = Field( Integer() )

    class Admin( PartyRelationship.Admin ):
        verbose_name = _('Shareholder structure')
        verbose_name_plural = _('Shareholder structures')
        list_display = ['established_from', 'established_to', 'shares',]
        list_search = ['established_from.full_name', 'established_to.full_name']
        field_attributes = {'established_from':{'name':_('Organization')},
                            'established_to':{'name':_('Shareholder')}}

    class ShareholderAdmin( Admin ):
        verbose_name = _('Shareholder')
        list_display = ['established_to', 'shares', 'from_date', 'thru_date']
        form_display = ['established_to', 'shares', 'from_date', 'thru_date', 'comment']
        form_size = (500, 300)

    class SharedAdmin( Admin ):
        verbose_name = _('Shares')
        verbose_name_plural = _('Shares')
        list_display = ['established_from', 'shares', 'from_date', 'thru_date']
        form_display = ['established_from', 'shares', 'from_date', 'thru_date', 'comment']
        form_size = (500, 300)

class AddressAdmin( EntityAdmin ):
    """Admin with only the Address information and not the Party information"""
    verbose_name = _('Address')
    list_display = ['address_street1', 'address_city', 'comment']
    form_display = ['address_street1', 'address_street2', 'address_city', 'comment', 'from_date', 'thru_date']
    field_attributes = dict(address_street1 = dict(name=_('Street'),
                                                   editable=True,
                                                   nullable=False),
                            address_street2 = dict(name=_('Street Extra'),
                                                   editable=True),
                            address_city = dict(name=_('City'),
                                                editable=True,
                                                nullable=False,
                                                delegate=delegates.Many2OneDelegate,
                                                target=City),
                            )

    def flush(self, party_address):
        if party_address.address:
            super( AddressAdmin, self ).flush( party_address.address )
        super( AddressAdmin, self ).flush( party_address )

    def refresh(self, party_address):
        if party_address.address:
            super( AddressAdmin, self ).refresh( party_address.address )
        super( AddressAdmin, self ).refresh( party_address )

class PartyContactMechanismAdmin( EntityAdmin ):
    form_size = ( 700, 200 )
    verbose_name = _('Contact mechanism')
    verbose_name_plural = _('Contact mechanisms')
    list_search = ['party_name', 'mechanism']
    list_display = ['party_name', 'contact_mechanism_mechanism', 'comment', 'from_date', ]
    form_display = Form( ['contact_mechanism_mechanism', 'comment', 'from_date', 'thru_date', ] )
    field_attributes = {'party_name':{'minimal_column_width':25, 'editable':False},
                        'mechanism':{'minimal_column_width':25,'editable':False},
                        'contact_mechanism_mechanism':{'minimal_column_width':25,
                                                       'editable':True,
                                                       'nullable':False,
                                                       'name':_('Mechanism'),
                                                       'delegate':delegates.VirtualAddressDelegate}}

    def flush(self, party_contact_mechanism):
        if party_contact_mechanism.contact_mechanism:
            super(PartyContactMechanismAdmin, self).flush( party_contact_mechanism.contact_mechanism )
        super(PartyContactMechanismAdmin, self).flush( party_contact_mechanism )

    def refresh(self, party_contact_mechanism):
        if party_contact_mechanism.contact_mechanism:
            super(PartyContactMechanismAdmin, self).refresh( party_contact_mechanism.contact_mechanism )
        super(PartyContactMechanismAdmin, self).refresh( party_contact_mechanism )
        party_contact_mechanism._contact_mechanism_mechanism = party_contact_mechanism.mechanism

    def get_depending_objects(self, contact_mechanism ):
        party = contact_mechanism.party
        if party and (party not in Party.query.session.new):
            party.expire(['email', 'phone'])
            yield party

class PartyPartyContactMechanismAdmin( PartyContactMechanismAdmin ):
    list_search = ['party_name', 'mechanism']
    list_display = ['contact_mechanism_mechanism', 'comment', 'from_date', ]

class Party( Entity ):
    """Base class for persons and organizations.  Use this base class to refer to either persons or
    organisations in building authentication systems, contact management or CRM"""
    using_options( tablename = 'party' )

    def __new__(cls, *args, **kwargs):
        party = super(Party, cls).__new__(cls, *args, **kwargs)
        # store the contact mechanisms as a temp variable before
        # the party has been flushed to the db
        setattr(party, '_contact_mechanisms', collections.defaultdict(lambda:None))
        return party

    addresses = OneToMany( 'PartyAddress', lazy = True, cascade="all, delete, delete-orphan" )
    contact_mechanisms = OneToMany( 'PartyContactMechanism', 
                                    lazy = True, 
                                    cascade='all, delete, delete-orphan' )
    shares = OneToMany( 'SharedShareholder', inverse = 'established_to', cascade='all, delete, delete-orphan' )
    directed_organizations = OneToMany( 'DirectedDirector', inverse = 'established_to', cascade='all, delete, delete-orphan' )
    status = OneToMany( type_3_status( 'Party', metadata, entities ), cascade='all, delete, delete-orphan' )
    categories = ManyToMany( 'PartyCategory', 
                            tablename='party_category_party', 
                            remote_colname='party_category_id',
                            local_colname='party_id')

    @property
    def name( self ):
        return ''

    def email( self ):

        cm = ContactMechanism
        pcm = PartyContactMechanism

        return sql.select( [cm.mechanism],
                          whereclause = and_( pcm.table.c.party_id == self.id,
                                              cm.table.c.mechanism.like( ( u'email', u'%' ) ) ),
                          from_obj = [cm.table.join( pcm.table )] ).limit(1)
    
    email = ColumnProperty( email, deferred = True )

    def phone( self ):

        cm = ContactMechanism
        pcm = PartyContactMechanism

        return sql.select( [cm.mechanism],
                          whereclause = and_( pcm.table.c.party_id == self.id,
                                              cm.table.c.mechanism.like( ( u'phone', u'%' ) ) ),
                          from_obj = [cm.table.join( pcm.table )] ).limit(1)
    
    phone = ColumnProperty( phone, deferred = True )

    def fax( self ):

        cm = ContactMechanism
        pcm = PartyContactMechanism

        return sql.select( [cm.mechanism],
                          whereclause = and_( pcm.table.c.party_id == self.id,
                                              cm.table.c.mechanism.like( ( u'fax', u'%' ) ) ),
                          from_obj = [cm.table.join( pcm.table )] ).limit(1)
    
    fax = ColumnProperty( fax, deferred = True )
    
    #
    # Create virtual properties for email and phone that can
    # get and set a contact mechanism for the party
    #
    def _get_contact_mechanisms_email(self):
        return self.email or self._contact_mechanisms['email']

    def _set_contact_mechanism_email(self, value):
        # todo : if no value, the existing value should be removed
        if not value or not value[1]:
            return
        self._contact_mechanisms['email'] = value

    def _get_contact_mechanisms_phone(self):
        return self.phone or self._contact_mechanisms['phone']

    def _set_contact_mechanism_phone(self, value):
        # todo : if no value, the existing value should be removed
        if not value or not value[1]:
            return
        self._contact_mechanisms['phone'] = value
        
    def _get_contact_mechanisms_fax(self):
        return self.fax or self._contact_mechanisms['fax']

    def _set_contact_mechanism_fax(self, value):
        # todo : if no value, the existing value should be removed
        if not value or not value[1]:
            return
        self._contact_mechanisms['fax'] = value
        
    contact_mechanisms_email = property(_get_contact_mechanisms_email,
                                        _set_contact_mechanism_email)

    contact_mechanisms_phone = property(_get_contact_mechanisms_phone,
                                        _set_contact_mechanism_phone)
    
    contact_mechanisms_fax = property(_get_contact_mechanisms_fax,
                                      _set_contact_mechanism_fax)

    def full_name( self ):

        aliased_organisation = sql.alias( Organization.table )
        aliased_person = sql.alias( Person.table )
        
        return sql.functions.coalesce( sql.select( [sql.functions.coalesce(aliased_person.c.first_name,'') + ' ' + sql.functions.coalesce(aliased_person.c.last_name, '')],
                                                   whereclause = and_( aliased_person.c.party_id == self.id ),
                                                   ).limit( 1 ).as_scalar(),
                                       sql.select( [aliased_organisation.c.name],
                                                   whereclause = and_( aliased_organisation.c.party_id == self.id ), 
                                                   ).limit( 1 ).as_scalar() )
    
    full_name = ColumnProperty( full_name, deferred=True )

    class Admin( EntityAdmin ):
        verbose_name = _('Party')
        verbose_name_plural = _('Parties')
        list_display = ['name', 'contact_mechanisms_email', 'contact_mechanisms_phone'] # don't use full name, since it might be None for new objects
        list_search = ['full_name']
        list_filter = ['categories.name']
        form_display = ['addresses', 'contact_mechanisms', 'shares', 'directed_organizations']
        form_size = (700, 700)
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
                                sex = dict( choices = [( u'M', _('male') ), ( u'F', _('female') )] ),
                                name = dict( minimal_column_width = 50 ),
                                email = dict( editable = False, minimal_column_width = 20 ),
                                phone = dict( editable = False, minimal_column_width = 20 ),
                                contact_mechanisms_email = dict( editable = True,
                                                                 name = _('Email'),
                                                                 address_type = 'email',
                                                                 minimal_column_width = 20,
                                                                 from_string = lambda s:('email', s),
                                                                 delegate = delegates.VirtualAddressDelegate ),
                                contact_mechanisms_phone = dict( editable = True,
                                                                 name = _('Phone'),
                                                                 address_type = 'phone',
                                                                 minimal_column_width = 20,
                                                                 from_string = lambda s:('phone', s),
                                                                 delegate = delegates.VirtualAddressDelegate ),
                                contact_mechanisms_fax = dict( editable = True,
                                                               name = _('Fax'),
                                                               address_type = 'fax',
                                                               minimal_column_width = 20,
                                                               from_string = lambda s:('fax', s),
                                                               delegate = delegates.VirtualAddressDelegate ),
                                )

        def flush(self, party):
            from sqlalchemy.orm.session import Session
            session = Session.object_session( party )
            if session:
                #
                # make sure the temporary contact mechanisms are added
                # relational
                #
                for cm in party._contact_mechanisms.values():
                    if not cm:
                        break
                    found = False
                    for party_contact_mechanism in party.contact_mechanisms:
                        mechanism = party_contact_mechanism.contact_mechanism_mechanism
                        if mechanism and mechanism[0] == cm[0]:
                            party_contact_mechanism.contact_mechanism_mechanism = cm
                            found = True
                            break
                    if not found:
                        contact_mechanism = ContactMechanism( mechanism = cm )
                        party.contact_mechanisms.append( PartyContactMechanism(contact_mechanism=contact_mechanism) )
                #
                # then clear the temporary store to make sure they are not created
                # a second time
                #
                
                #for party_contact_mechanism in party.contact_mechanisms:
                #    objects.extend([ party_contact_mechanism, party_contact_mechanism.contact_mechanism ])
                session.flush()
                party._contact_mechanisms.clear()
                party.expire( ['phone', 'email', 'fax'] )
                
class Organization( Party ):
    """An organization represents any internal or external organization.  Organizations can include
    businesses and groups of individuals"""
    using_options( tablename = 'organization', inheritance = 'multi' )
    name = Field( Unicode( 50 ), required = True, index = True )
    logo = Field( camelot.types.Image( upload_to = 'organization-logo' ), deferred = True )
    tax_id = Field( Unicode( 20 ) )
    directors = OneToMany( 'DirectedDirector', inverse = 'established_from', cascade='all, delete, delete-orphan' )
    employees = OneToMany( 'EmployerEmployee', inverse = 'established_from', cascade='all, delete, delete-orphan' )
    suppliers = OneToMany( 'SupplierCustomer', inverse = 'established_to', cascade='all, delete, delete-orphan' )
    customers = OneToMany( 'SupplierCustomer', inverse = 'established_from', cascade='all, delete, delete-orphan' )
    shareholders = OneToMany( 'SharedShareholder', inverse = 'established_from', cascade='all, delete, delete-orphan' )

    def __unicode__( self ):
        return self.name or ''

    @property
    def number_of_shares_issued( self ):
        return sum( ( shareholder.shares for shareholder in self.shareholders ), 0 )

    class Admin( Party.Admin ):
        verbose_name = _( 'Organization' )
        verbose_name_plural = _( 'Organizations' )
        list_display = ['name', 'tax_id', 'contact_mechanisms_email', 'contact_mechanisms_phone']
        form_display = TabForm( [( _('Basic'), Form( [ 'name', 'contact_mechanisms_email', 
                                                       'contact_mechanisms_phone', 
                                                       'contact_mechanisms_fax', 'tax_id', 
                                                       'addresses', 'contact_mechanisms'] ) ),
                                ( _('Employment'), Form( ['employees'] ) ),
                                ( _('Customers'), Form( ['customers'] ) ),
                                ( _('Suppliers'), Form( ['suppliers'] ) ),
                                ( _('Corporate'), Form( ['directors', 'shareholders', 'shares'] ) ),
                                ( _('Branding'), Form( ['logo'] ) ),
                                ( _('Category and Status'), Form( ['categories', 'status'] ) ),
                                ] )
        field_attributes = dict( Party.Admin.field_attributes )

Organization = documented_entity()( Organization )

# begin short person definition
class Person( Party ):
    """Person represents natural persons
    """
    using_options( tablename = 'person', inheritance = 'multi' )
    first_name = Field( Unicode( 40 ), required = True )
    last_name = Field( Unicode( 40 ), required = True )
# end short person definition
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
    employers = OneToMany( 'EmployerEmployee', inverse = 'established_to', cascade='all, delete, delete-orphan' )

    @property
    def note(self):
        for person in self.__class__.query.filter_by(first_name=self.first_name, last_name=self.last_name):
            if person != self:
                return _('A person with the same name already exists')

    @property
    def name( self ):
        # we don't use full name in here, because for new objects, full name will be None, since
        # it needs to be fetched from the db first
        return u'%s %s' % ( self.first_name, self.last_name )

    def __unicode__( self ):
        return self.name or ''

    class Admin( Party.Admin ):
        verbose_name = _( 'Person' )
        verbose_name_plural = _( 'Persons' )
        list_display = ['first_name', 'last_name', 'contact_mechanisms_email', 'contact_mechanisms_phone']
        form_display = TabForm( [( _('Basic'), Form( [HBoxForm( [ Form( [WidgetOnlyForm('note'), 
                                                                  'first_name', 
                                                                  'last_name', 
                                                                  'sex',
                                                                  'contact_mechanisms_email',
                                                                  'contact_mechanisms_phone',
                                                                  'contact_mechanisms_fax'] ),
                                                                [WidgetOnlyForm('picture'), ],
                                                         ] ),
                                                         'comment', ], scrollbars = False ) ),
                                ( _('Official'), Form( ['birthdate', 'social_security_number', 'passport_number',
                                                        'passport_expiry_date', 'addresses', 'contact_mechanisms',], scrollbars = False ) ),
                                ( _('Work'), Form( ['employers', 'directed_organizations', 'shares'], scrollbars = False ) ),
                                ( _('Category'), Form( ['categories',] ) ),
                                ] )
        field_attributes = dict( Party.Admin.field_attributes )
        field_attributes['note'] = {'delegate':delegates.NoteDelegate}

Person = documented_entity()( Person )

class Address( Entity ):
    """The Address to be given to a Party (a Person or an Organization)"""
    using_options( tablename = 'address' )
    street1 = Field( Unicode( 128 ), required = True )
    street2 = Field( Unicode( 128 ) )
    city = ManyToOne( 'City', required = True, ondelete = 'cascade', onupdate = 'cascade' )

    @ColumnProperty
    def name( self ):
        return sql.select( [self.street1 + ', ' + GeographicBoundary.full_name],
                           whereclause = (GeographicBoundary.id==self.city_geographicboundary_id))

    @classmethod
    def get_or_create( cls, street1, street2, city ):
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
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        list_display = ['street1', 'street2', 'city']
        form_size = ( 700, 150 )
        field_attributes = {'street1':{'minimal_column_width':30}}
        form_actions = [( 'Show on map', lambda address:address.showMap() )]

Address = documented_entity()( Address )

class PartyAddress( Entity ):
    using_options( tablename = 'party_address' )

    def __new__(cls, *args, **kwargs):
        party_address = super(PartyAddress, cls).__new__(cls, *args, **kwargs)
        setattr(party_address, '_address_street1', None)
        setattr(party_address, '_address_street2', None)
        setattr(party_address, '_address_city', None)
        return party_address

    party = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    address = ManyToOne( 'Address', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    from_date = Field( Date(), default = datetime.date.today, required = True, index = True )
    thru_date = Field( Date(), default = end_of_times, required = True, index = True )
    comment = Field( Unicode( 256 ) )

    #
    # Create 3 'virtual attributes'
    # * address_street1
    # * address_street2
    # * address_city
    # These attributes refer to the corresponding attributes on the
    # address relation, if the address relation exists, otherwise, they
    # refer to a corresponding hidden attribute
    #
    def __getattr__(self, attr):
        if attr.startswith('address_'):
            if self.address:
                return getattr(self.address, attr[len('address_'):])
            else:
                return getattr(self, '_address_' + attr[len('address_'):] )
        else:
            return super(PartyAddress, self).__getattr__(attr)

    def __setattr__(self, attr, value):
        if attr.startswith('address_'):
            setattr(self, '_address_' + attr[len('address_'):], value )
            if self.address:
                return setattr(self.address, attr[len('address_'):], value )
            elif self._address_street1 != None and self._address_city != None:
                self.address = Address( street1 = self._address_street1,
                                        city = self._address_city )
        else:
            super(PartyAddress, self).__setattr__(attr, value)

    @ColumnProperty
    def party_name( self ):
        return sql.select( [sql.func.coalesce(Party.full_name, '')],
                           whereclause = (Party.id==self.party_id))

    @ColumnProperty
    def address_name( self ):
        return sql.select( [sql.func.coalesce(Address.name, '')],
                           whereclause = (Address.id==self.address_id))

    def __unicode__( self ):
        return '%s : %s' % ( unicode( self.party ), unicode( self.address ) )

    def showMap( self ):
        if self.address:
            self.address.showMap()

    class Admin( EntityAdmin ):
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        list_search = ['party_name', 'address_name']
        list_display = ['party_name', 'address_name', 'comment']
        form_display = ['party', 'address', 'comment', 'from_date', 'thru_date']
        form_size = ( 700, 200 )
        form_actions = [( 'Show on map', lambda address:address.showMap() )]
        field_attributes = dict(address=dict(embedded=True),
                                party_name=dict(editable=False, name='Party', minimal_column_width=30),
                                address_name=dict(editable=False, name='Address', minimal_column_width=30))

class PartyAddressRoleType( Entity ):
    using_options( tablename = 'party_address_role_type' )
    code = Field( Unicode( 10 ) )
    description = Field( Unicode( 40 ) )

    class Admin( EntityAdmin ):
        verbose_name = _('Address role type')
        list_display = ['code', 'description']

class ContactMechanism( Entity ):
    using_options( tablename = 'contact_mechanism' )
    mechanism = Field( camelot.types.VirtualAddress( 256 ), required = True )
    party_address = ManyToOne( 'PartyAddress', ondelete = 'set null', onupdate = 'cascade' )
    party_contact_mechanisms = OneToMany( 'PartyContactMechanism' )

    def __unicode__( self ):
        if self.mechanism:
            return u'%s : %s' % ( self.mechanism[0], self.mechanism[1] )

    class Admin( EntityAdmin ):
        form_size = ( 700, 150 )
        verbose_name = _('Contact mechanism')
        list_display = ['mechanism']
        form_display = Form( ['mechanism', 'party_address'] )
        field_attributes = {'mechanism':{'minimal_column_width':25}}

        def get_depending_objects(self, contact_mechanism ):
            for party_contact_mechanism in contact_mechanism.party_contact_mechanisms:
                if party_contact_mechanism not in PartyContactMechanism.query.session.new:
                    party_contact_mechanism.expire( ['mechanism'] )
                    yield party_contact_mechanism
                    party = party_contact_mechanism.party
                    if party and party not in Party.query.session.new:
                        party.expire(['email', 'phone'])
                        yield party

ContactMechanism = documented_entity()( ContactMechanism )

class PartyContactMechanism( Entity ):
    using_options( tablename = 'party_contact_mechanism' )

    def __new__(cls, *args, **kwargs):
        party_contact_mechanism = super(PartyContactMechanism, cls).__new__(cls, *args, **kwargs)
        setattr(party_contact_mechanism, '_contact_mechanism_mechanism', None)
        return party_contact_mechanism

    party = ManyToOne( 'Party', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    contact_mechanism = ManyToOne( 'ContactMechanism', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    from_date = Field( Date(), default = datetime.date.today, required = True, index = True )
    thru_date = Field( Date(), default = end_of_times, index = True )
    comment = Field( Unicode( 256 ) )

    def _get_contact_mechanism_mechanism(self):
        if self._contact_mechanism_mechanism != None:
            return self._contact_mechanism_mechanism
        return self.mechanism

    def _set_contact_mechanism_mechanism(self, mechanism):
        self._contact_mechanism_mechanism = mechanism
        if mechanism != None:
            if self.contact_mechanism:
                self.contact_mechanism.mechanism = mechanism
            else:
                self.contact_mechanism = ContactMechanism( mechanism=mechanism )

    #
    # A property to get and set the mechanism attribute of the
    # related contact mechanism object
    #
    contact_mechanism_mechanism = property( _get_contact_mechanism_mechanism,
                                            _set_contact_mechanism_mechanism )

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

# begin category definition
class PartyCategory( Entity ):
    using_options( tablename = 'party_category' )
    name = Field( Unicode(40), index=True, required=True )
    color = Field( camelot.types.Color() )
    parent = ManyToOne( 'PartyCategory' )
# end category definition
    parties = ManyToMany( 'Party', lazy = True,
                          tablename='party_category_party', 
                          remote_colname='party_id',
                          local_colname='party_category_id')
                            
    def get_contact_mechanisms(self, virtual_address_type):
        """Function to be used to do messaging
        
        :param virtual_address_type: a virtual address type, such as 'phone' or 'email'
        :return: a generator that yields strings of contact mechanisms, egg 'info@example.com'
        """
        for party in self.parties:
            for party_contact_mechanism in party.contact_mechanisms:
                contact_mechanism = party_contact_mechanism.contact_mechanism
                if contact_mechanism:
                    virtual_address = contact_mechanism.mechanism
                    if virtual_address and virtual_address[0] == virtual_address_type:
                        yield virtual_address[1]
                
    def __unicode__(self):
        return self.name or ''
    
    class Admin( EntityAdmin ):
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        list_display = ['name', 'color']
