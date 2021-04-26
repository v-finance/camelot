#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

"""Set of classes to store persons, organizations, relationships and
contact mechanisms

These structures are modeled like described in 'The Data Model Resource Book'
by Len Silverston, Chapter 2
"""

import datetime

import six

from sqlalchemy.ext import hybrid
from sqlalchemy.types import Date, Unicode
from sqlalchemy.sql.expression import and_
from sqlalchemy import orm, schema, sql, ForeignKey

from camelot.admin.entity_admin import EntityAdmin
from camelot.core.orm import ( Entity, using_options, Field, ManyToMany,  
                               ManyToOne, OneToMany, ColumnProperty )
from camelot.core.utils import ugettext_lazy as _
import camelot.types
from camelot.view.controls import delegates
from camelot.view.forms import Form, TabForm, HBoxForm, WidgetOnlyForm, Stretch

from .authentication import end_of_times

@six.python_2_unicode_compatible
class GeographicBoundary( Entity ):
    """The base class for Country and City"""
    using_options( tablename = 'geographic_boundary' )
    code = schema.Column( Unicode( 10 ) )
    name = schema.Column( Unicode( 40 ), nullable = False )

    row_type = schema.Column( Unicode(40), nullable = False )
    __mapper_args__ = { 'polymorphic_on' : row_type }

    @ColumnProperty
    def full_name( self ):
        return self.code + ' ' + self.name

    def __str__(self):
        return u'%s %s' % ( self.code, self.name )

    class Admin(EntityAdmin):
        verbose_name = _('Geographic Boundary')
        verbose_name_plural = _('Geographic Boundaries')
        list_display = ['row_type', 'name', 'code']
        form_state = 'right'
        field_attributes = {
            'row_type': {
                'name': _('Type'),
                'editable': False,
            }
        }

class Country( GeographicBoundary ):
    """A subclass of GeographicBoundary used to store the name and the
    ISO code of a country"""
    using_options( tablename = 'geographic_boundary_country' )
    geographicboundary_id = Field( camelot.types.PrimaryKey(), 
                                   ForeignKey('geographic_boundary.id'), 
                                   primary_key = True,
                                   autoincrement = False )

    __mapper_args__ = {'polymorphic_identity': 'country'}

    @classmethod
    def get_or_create( cls, code, name ):
        country = Country.query.filter_by( code = code ).first()
        if not country:
            country = Country( code = code, name = name )
            orm.object_session( country ).flush()
        return country

    class Admin(GeographicBoundary.Admin):
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        list_display = ['name', 'code']

@six.python_2_unicode_compatible
class City( GeographicBoundary ):
    """A subclass of GeographicBoundary used to store the name, the postal code
    and the Country of a city"""
    using_options( tablename = 'geographic_boundary_city' )
    country = ManyToOne( Country, required = True, ondelete = 'cascade', onupdate = 'cascade' )
    geographicboundary_id = Field( camelot.types.PrimaryKey(),
                                   ForeignKey('geographic_boundary.id'),
                                   primary_key = True,
                                   autoincrement = False )

    __mapper_args__ = {'polymorphic_identity': 'city'}

    def __str__(self):
        if None not in (self.code, self.name, self.country):
            return u'{0.code} {0.name} [{1.code}]'.format( self, self.country )
        return u''
    
    @classmethod
    def get_or_create( cls, country, code, name ):
        city = City.query.filter_by( code = code, country = country ).first()
        if not city:
            city = City( code = code, name = name, country = country )
            orm.object_session( city ).flush()
        return city

    class Admin(GeographicBoundary.Admin):
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
        list_display = ['code', 'name', 'country']

@six.python_2_unicode_compatible
class Address( Entity ):
    """The Address to be given to a Party (a Person or an Organization)"""
    using_options( tablename = 'address' )
    street1 = schema.Column( Unicode( 128 ), nullable = False )
    street2 = schema.Column( Unicode( 128 ) )
    city = ManyToOne( City,
                      required = True,
                      ondelete = 'cascade',
                      onupdate = 'cascade',
                      lazy = 'subquery' )

    def name( self ):
        return sql.select( [self.street1 + ', ' + GeographicBoundary.full_name],
                           whereclause = (GeographicBoundary.id == self.city_geographicboundary_id))

    name = ColumnProperty( name, deferred = True )

    @classmethod
    def get_or_create( cls, street1, street2, city ):
        address = cls.query.filter_by( street1 = street1, street2 = street2, city = city ).first()
        if not address:
            address = cls( street1 = street1, street2 = street2, city = city )
            orm.object_session( address ).flush()
        return address

    def __str__(self):
        return u'%s, %s' % ( self.street1 or '', self.city or '' )

    class Admin( EntityAdmin ):
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        list_display = ['street1', 'street2', 'city']
        form_size = ( 700, 150 )
        field_attributes = {'street1':{'minimal_column_width':30}}
        
        def get_depending_objects( self, address ):
            for party_address in address.party_addresses:
                yield party_address
                if party_address.party != None:
                    yield party_address.party

class PartyContactMechanismAdmin( EntityAdmin ):
    form_size = ( 700, 200 )
    verbose_name = _('Contact mechanism')
    verbose_name_plural = _('Contact mechanisms')
    list_search = ['party_name', 'mechanism']
    list_display = ['party_name', 'mechanism', 'comment', 'from_date', ]
    form_display = Form( ['mechanism', 'comment', 'from_date', 'thru_date', ] )
    field_attributes = {'party_name':{'minimal_column_width':25, 'editable':False},
                        'comment': {'name': _('Comment')},
                        'mechanism':{'minimal_column_width':25,
                                     'editable':True,
                                     'nullable':False,
                                     'name':_('Mechanism'),
                                     'delegate':delegates.VirtualAddressDelegate}}

    def get_depending_objects(self, contact_mechanism ):
        party = contact_mechanism.party
        if party and (party not in Party.query.session.new):
            yield party
            
    def get_compounding_objects( self, contact_mechanism ):
        if contact_mechanism.contact_mechanism:
            yield contact_mechanism.contact_mechanism

class PartyPartyContactMechanismAdmin( PartyContactMechanismAdmin ):
    list_search = ['party_name', 'mechanism']
    list_display = ['mechanism', 'comment', 'from_date', ]

class WithAddresses(object):

    @hybrid.hybrid_property
    def street1( self ):
        return self._get_address_field( u'street1' )
    
    @street1.setter
    def street1( self, value ):
        return self._set_address_field( u'street1', value )

    @street1.expression
    def street1(cls):
        return sql.select([Address.street1],
                          whereclause=cls.first_address_filter(),
                          limit=1).as_scalar()

    @hybrid.hybrid_property
    def street2( self ):
        return self._get_address_field( u'street2' )

    @street2.expression
    def street2_expression(cls):
        return sql.select([Address.street2],
                          whereclause=cls.first_address_filter(),
                          limit=1).as_scalar()

    @street2.setter
    def street2( self, value ):
        return self._set_address_field( u'street2', value )

    @hybrid.hybrid_property
    def city( self ):
        return self._get_address_field( u'city' )
    
    @city.setter
    def city( self, value ):
        return self._set_address_field( u'city', value )

    @city.expression
    def city(cls):

        GB = orm.aliased(GeographicBoundary)

        return sql.select([GB.code + ' ' + GB.name],
                          whereclause=sql.and_(
                              GB.id==Address.city_geographicboundary_id,
                              cls.first_address_filter()
                              ),
                          limit=1).as_scalar()

    def get_first_address(self):
        raise NotImplementedError()

    def set_first_address(self):
        raise NotImplementedError()

    @classmethod
    def first_address_filter(cls):
        raise NotImplementedError

    def _get_address_field( self, name ):
        first_address = self.get_first_address()
        if first_address is not None:
            return getattr( first_address, name )

    def _set_address_field( self, name, value ):
        address = self.set_first_address()
        setattr( address, name, value )
        if address.street1==None and address.street2==None and address.city==None:
            session = orm.object_session( address )
            if address in session.new:
                session.expunge( address )
                self.addresses.remove( address )
            else:
                session.delete( address )

class Party(Entity, WithAddresses):
    """Base class for persons and organizations.  Use this base class to refer to either persons or
    organisations in building authentication systems, contact management or CRM"""
    using_options( tablename = 'party' )
    
    row_type = schema.Column( Unicode(40), nullable = False )
    __mapper_args__ = { 'polymorphic_on' : row_type }

    @classmethod
    def first_address_filter(cls):
        return sql.and_(PartyAddress.party_id==cls.id,
                        PartyAddress.address_id==Address.id)

    @property
    def name( self ):
        return ''

    def get_first_address(self):
        for party_address in self.addresses:
            return party_address

    def set_first_address(self):
        if not self.addresses:
            address = PartyAddress()
            self.addresses.append( address )
        return self.addresses[0]
        
    def _get_contact_mechanism( self, described_by ):
        """Get a specific type of contact mechanism
        """
        for party_contact_mechanism in self.contact_mechanisms:
            contact_mechanism = party_contact_mechanism.contact_mechanism
            if contact_mechanism != None:
                mechanism = contact_mechanism.mechanism
                if mechanism != None:
                    if mechanism[0] == described_by:
                        return mechanism
                    
    def _set_contact_mechanism( self, described_by, value ):
        """Set a specific type of contact mechanism
        """
        assert value[0] in camelot.types.VirtualAddress.virtual_address_types
        for party_contact_mechanism in self.contact_mechanisms:
            contact_mechanism = party_contact_mechanism.contact_mechanism
            if contact_mechanism != None:
                mechanism = contact_mechanism.mechanism
                if mechanism != None:
                    if mechanism[0] == described_by:
                        if value and value[1]:
                            contact_mechanism.mechanism = value
                        else:
                            self.contact_mechanisms.remove( party_contact_mechanism )
                            session = orm.object_session( party_contact_mechanism )
                            if (session is not None) and party_contact_mechanism.id:
                                session.delete( party_contact_mechanism )
                        return
        if value and value[1]:
            contact_mechanism = ContactMechanism( mechanism = value )
            party_contact_mechanism = PartyContactMechanism( contact_mechanism = contact_mechanism )
            self.contact_mechanisms.append( party_contact_mechanism )
            
    @hybrid.hybrid_property
    def email( self ):
        return self._get_contact_mechanism( u'email' )
    
    @email.setter
    def email( self, value ):
        return self._set_contact_mechanism( u'email', value )
    
    @email.expression
    def email( self ):
        return orm.aliased( ContactMechanism ).mechanism

    @hybrid.hybrid_property
    def phone( self ):
        return self._get_contact_mechanism( u'phone' )
    
    @phone.setter
    def phone( self, value ):
        return self._set_contact_mechanism( u'phone', value )
    
    @phone.expression
    def phone( self ):
        return orm.aliased( ContactMechanism ).mechanism

    @hybrid.hybrid_property
    def fax( self ):
        return self._get_contact_mechanism( u'fax' )

    @fax.setter
    def fax( self, value ):
        return self._set_contact_mechanism( u'fax', value )

    @fax.expression
    def fax( self ):
        return orm.aliased( ContactMechanism ).mechanism

    @hybrid.hybrid_property
    def mobile( self ):
        return self._get_contact_mechanism( u'mobile' )

    @mobile.setter
    def mobile( self, value ):
        return self._set_contact_mechanism( u'mobile', value )

    @mobile.expression
    def mobile( self ):
        return orm.aliased( ContactMechanism ).mechanism


@six.python_2_unicode_compatible
class Organization( Party ):
    """An organization represents any internal or external organization.  Organizations can include
    businesses and groups of individuals"""
    using_options( tablename = 'organization' )
    party_id = Field( camelot.types.PrimaryKey(),
                      ForeignKey('party.id'),
                      primary_key = True )
    __mapper_args__ = {'polymorphic_identity': u'organization'}
    name = schema.Column( Unicode( 50 ), nullable = False, index = True )
    logo = schema.Column( camelot.types.File( upload_to = 'organization-logo' ))
    tax_id = schema.Column( Unicode( 20 ) )

    def __str__(self):
        return self.name or ''

    @property
    def note(self):
        session = orm.object_session(self)
        if session is not None:
            cls = self.__class__
            if session.query(cls).filter( sql.and_( cls.name == self.name,
                                                    cls.id != self.id ) ).count():
                return _('An organization with the same name already exists')

# begin short person definition
@six.python_2_unicode_compatible
class Person( Party ):
    """Person represents natural persons
    """
    using_options( tablename = 'person' )
    party_id = Field( camelot.types.PrimaryKey(),
                      ForeignKey('party.id'),
                      primary_key = True )
    __mapper_args__ = {'polymorphic_identity': u'person'}
    first_name = schema.Column( Unicode( 40 ), nullable = False )
    last_name = schema.Column( Unicode( 40 ), nullable = False )
# end short person definition
    middle_name = schema.Column( Unicode( 40 ) )
    personal_title = schema.Column( Unicode( 10 ) )
    suffix = schema.Column( Unicode( 3 ) )
    sex = schema.Column( Unicode( 1 ), default = u'M' )
    birthdate = schema.Column( Date() )
    martial_status = schema.Column( Unicode( 1 ) )
    social_security_number = schema.Column( Unicode( 12 ) )
    passport_number = schema.Column( Unicode( 20 ) )
    passport_expiry_date = schema.Column( Date() )
    picture = schema.Column( camelot.types.File( upload_to = 'person-pictures' ))
    comment = schema.Column( camelot.types.RichText() )

    @property
    def note(self):
        for person in self.__class__.query.filter_by(first_name=self.first_name, last_name=self.last_name):
            if person != self:
                return _('A person with the same name already exists')

    @property
    def name( self ):
        # we don't use full name in here, because for new objects, full name will be None, since
        # it needs to be fetched from the db first
        return ' '.join([name for name in [self.first_name, self.last_name] if name])

    def __str__(self):
        return self.name or ''

#class PartyRelationship( Entity ):
    #using_options( tablename = 'party_relationship' )
    #from_date = Field( Date(), default = datetime.date.today, required = True, index = True )
    #thru_date = Field( Date(), default = end_of_times, required = True, index = True )
    #comment = Field( camelot.types.RichText() )
    
    #row_type = schema.Column( Unicode(40), nullable = False )
    #__mapper_args__ = { 'polymorphic_on' : row_type }

    #class Admin( EntityAdmin ):
        #verbose_name = _('Relationship')
        #verbose_name_plural = _('Relationships')
        #list_display = ['from_date', 'thru_date']

#class EmployerEmployee( PartyRelationship ):
    #"""Relation from employer to employee"""
    #using_options( tablename = 'party_relationship_empl' )
    #established_from = ManyToOne( Organization, required = True, ondelete = 'cascade', onupdate = 'cascade',
                                  #backref=orm.backref('employees', cascade='all, delete, delete-orphan' ) )    # the employer
    #established_to = ManyToOne( Person, required = True, ondelete = 'cascade', onupdate = 'cascade'
    #                            backref=orm.backref('employers', cascade='all, delete, delete-orphan' ))            # the employee
    #partyrelationship_id = Field( Integer,
                                  #ForeignKey('party_relationship.id'), 
                                  #primary_key = True )

    #__mapper_args__ = {'polymorphic_identity': 'employeremployee'}

    #@ColumnProperty
    #def first_name( self ):
        #return sql.select( [Person.first_name], Person.party_id == self.established_to_party_id )

    #@ColumnProperty
    #def last_name( self ):
        #return sql.select( [Person.last_name], Person.party_id == self.established_to_party_id )

    #@ColumnProperty
    #def social_security_number( self ):
        #return sql.select( [Person.social_security_number], Person.party_id == self.established_to_party_id )

    #def __unicode__( self ):
        #return u'%s %s %s' % ( unicode( self.established_to ), _('Employed by'),unicode( self.established_from ) )

    #class Admin( PartyRelationship.Admin ):
        #verbose_name = _('Employment relation')
        #verbose_name_plural = _('Employment relations')
        #list_filter = ['established_from.name']
        #list_search = ['established_from.name', 'established_to.first_name', 'established_to.last_name']

    #class EmployeeAdmin( EntityAdmin ):
        #verbose_name = _('Employee')
        #list_display = ['established_to', 'from_date', 'thru_date']
        #form_display = ['established_to', 'comment', 'from_date', 'thru_date']
        #field_attributes = {'established_to':{'name':_( 'Name' )}}

    #class EmployerAdmin( EntityAdmin ):
        #verbose_name = _('Employer')
        #list_display = ['established_from', 'from_date', 'thru_date']
        #form_display = ['established_from', 'comment', 'from_date', 'thru_date']
        #field_attributes = {'established_from':{'name':_( 'Name' )}}

#class DirectedDirector( PartyRelationship ):
    #"""Relation from a directed organization to a director"""
    #using_options( tablename = 'party_relationship_dir' )
    #established_from = ManyToOne( Organization, required = True, ondelete = 'cascade', onupdate = 'cascade',
                                  #backref=orm.backref('directors', cascade='all, delete, delete-orphan' ))
    #established_to = ManyToOne( Party, required = True, ondelete = 'cascade', onupdate = 'cascade',
                                #backref=orm.backref('directed_organizations', cascade='all, delete, delete-orphan' ))
    #title = Field( Unicode( 256 ) )
    #represented_by = OneToMany( 'RepresentedRepresentor', inverse = 'established_to' )

    #partyrelationship_id = Field( Integer,
                                  #ForeignKey('party_relationship.id'), 
                                  #primary_key = True )

    #__mapper_args__ = {'polymorphic_identity': 'directeddirector'}

    #class Admin( PartyRelationship.Admin ):
        #verbose_name = _('Direction structure')
        #verbose_name_plural = _('Direction structures')
        #list_display = ['established_from', 'established_to', 'title', 'represented_by']
        #list_search = ['established_from.full_name', 'established_to.full_name']
        #field_attributes = {'established_from':{'name':_('Organization')},
                            #'established_to':{'name':_('Director')}}

    #class DirectorAdmin( Admin ):
        #verbose_name = _('Director')
        #list_display = ['established_to', 'title', 'from_date', 'thru_date']
        #form_display = ['established_to', 'title', 'from_date', 'thru_date', 'represented_by', 'comment']

    #class DirectedAdmin( Admin ):
        #verbose_name = _('Directed organization')
        #list_display = ['established_from', 'title', 'from_date', 'thru_date']
        #form_display = ['established_from', 'title', 'from_date', 'thru_date', 'represented_by', 'comment']

#class RepresentedRepresentor( Entity ):
    #"""Relation from a representing party to the person representing the party"""
    #using_options( tablename = 'party_representor' )
    #from_date = Field( Date(), default = datetime.date.today, required = True, index = True )
    #thru_date = Field( Date(), default = end_of_times, required = True, index = True )
    #comment = Field( camelot.types.RichText() )
    #established_from = ManyToOne( Person, required = True, ondelete = 'cascade', onupdate = 'cascade' )
    #established_to = ManyToOne( DirectedDirector, required = True, ondelete = 'cascade', onupdate = 'cascade' )

    #class Admin( EntityAdmin ):
        #verbose_name = _('Represented by')
        #list_display = ['established_from', 'from_date', 'thru_date']
        #form_display = ['established_from', 'from_date', 'thru_date', 'comment']
        #field_attributes = {'established_from':{'name':_( 'Name' )}}

#class SupplierCustomer( PartyRelationship ):
    #"""Relation from supplier to customer"""
    #using_options( tablename = 'party_relationship_suppl' )
    #established_from = ManyToOne( Party, required = True, ondelete = 'cascade', onupdate = 'cascade',
                                  #backref=orm.backref('customers', cascade='all, delete, delete-orphan' ))
    #established_to = ManyToOne( Party, required = True, ondelete = 'cascade', onupdate = 'cascade',
                                #backref=orm.backref('suppliers', cascade='all, delete, delete-orphan' ))
    #partyrelationship_id = Field( Integer,
                                  #ForeignKey('party_relationship.id'), 
                                  #primary_key = True )

    #__mapper_args__ = {'polymorphic_identity': 'suppliercustomer'}

    #class Admin( PartyRelationship.Admin ):
        #verbose_name = _('Supplier - Customer')
        #list_display = ['established_from', 'established_to', 'from_date', 'thru_date']

    #class CustomerAdmin( EntityAdmin ):
        #verbose_name = _('Customer')
        #list_display = ['established_to', ]
        #form_display = ['established_to', 'comment', 'from_date', 'thru_date']
        #field_attributes = {'established_to':{'name':_( 'Name' )}}

    #class SupplierAdmin( EntityAdmin ):
        #verbose_name = _('Supplier')
        #list_display = ['established_from', ]
        #form_display = ['established_from', 'comment', 'from_date', 'thru_date']
        #field_attributes = {'established_from':{'name':_( 'Name' )}}

#class SharedShareholder( PartyRelationship ):
    #"""Relation from a shared organization to a shareholder"""
    #using_options( tablename = 'party_relationship_shares' )
    #established_from = ManyToOne( Organization, required = True, ondelete = 'cascade', onupdate = 'cascade',
                                  #backref=orm.backref('shareholders', cascade='all, delete, delete-orphan' ))
    #established_to = ManyToOne( Party, required = True, ondelete = 'cascade', onupdate = 'cascade',
                                #backref=orm.backref('shares', cascade='all, delete, delete-orphan' ) )
    #shares = Field( Integer() )
    #partyrelationship_id = Field( Integer,
                                  #ForeignKey('party_relationship.id'), 
                                  #primary_key = True )

    #__mapper_args__ = {'polymorphic_identity': 'sharedshareholder'}

    #class Admin( PartyRelationship.Admin ):
        #verbose_name = _('Shareholder structure')
        #verbose_name_plural = _('Shareholder structures')
        #list_display = ['established_from', 'established_to', 'shares',]
        #list_search = ['established_from.full_name', 'established_to.full_name']
        #field_attributes = {'established_from':{'name':_('Organization')},
                            #'established_to':{'name':_('Shareholder')}}

    #class ShareholderAdmin( Admin ):
        #verbose_name = _('Shareholder')
        #list_display = ['established_to', 'shares', 'from_date', 'thru_date']
        #form_display = ['established_to', 'shares', 'from_date', 'thru_date', 'comment']
        #form_size = (500, 300)

    #class SharedAdmin( Admin ):
        #verbose_name = _('Shares')
        #verbose_name_plural = _('Shares')
        #list_display = ['established_from', 'shares', 'from_date', 'thru_date']
        #form_display = ['established_from', 'shares', 'from_date', 'thru_date', 'comment']
        #form_size = (500, 300)

class Addressable(object):
    
    def _get_address_field( self, name ):
        if self.address:
            return getattr( self.address, name )
        
    def _set_address_field( self, name, value ):
        if not self.address:
            self.address = Address()
        setattr( self.address, name, value )
        
    @hybrid.hybrid_property
    def street1( self ):
        return self._get_address_field( u'street1' )
    
    @street1.setter
    def street1( self, value ):
        return self._set_address_field( u'street1', value )
    
    @street1.expression
    def street1( self ):
        return Address.street1

    @hybrid.hybrid_property
    def street2( self ):
        return self._get_address_field( u'street2' )

    @street2.setter
    def street2( self, value ):
        return self._set_address_field( u'street2', value )

    @street2.expression
    def street2( self ):
        return Address.street2

    @hybrid.hybrid_property
    def city( self ):
        return self._get_address_field( u'city' )
    
    @city.setter
    def city( self, value ):
        return self._set_address_field( u'city', value )

    @city.expression
    def city_expression( self ):
        return Address.city_geographicboundary_id

    class Admin(object):
        field_attributes = dict(
            street1 = dict( editable = True,
                            name = _('Street'),
                            minimal_column_width = 50 ),
            street2 = dict( editable = True,
                            name = _('Street Extra'),
                            minimal_column_width = 50 ),
            city = dict( editable = True, 
                         delegate = delegates.Many2OneDelegate,
                         target = City ), 
            email = dict( editable = True, 
                          minimal_column_width = 20,
                          name = _('Email'),
                          address_type = 'email',
                          from_string = lambda s:('email', s),
                          delegate = delegates.VirtualAddressDelegate),
            phone = dict( editable = True, 
                          minimal_column_width = 20,
                          address_type = 'phone',
                          name = _('Phone'),
                          from_string = lambda s:('phone', s),
                          delegate = delegates.VirtualAddressDelegate ),
            mobile = dict( editable = True,
                           minimal_column_width = 20,
                           address_type = 'mobile',
                           name = _('Mobile'),
                           from_string = lambda s:('mobile', s),
                           delegate = delegates.VirtualAddressDelegate ),
            fax = dict( editable = True,
                        minimal_column_width = 20,
                        address_type = 'fax',
                        name = _('Fax'),
                        from_string = lambda s:('fax', s),
                        delegate = delegates.VirtualAddressDelegate ), )


@six.python_2_unicode_compatible
class PartyAddress( Entity, Addressable ):
    using_options( tablename = 'party_address' )
    party_id = schema.Column(
        camelot.types.PrimaryKey(),
        ForeignKey('party.id', ondelete='cascade', onupdate='cascade'),
        nullable=False,
    )
    party = orm.relationship(
        Party, backref = orm.backref('addresses', lazy=True,
                                     cascade='all, delete, delete-orphan'),
        lazy='subquery',
    )
    address = ManyToOne( Address,
                         required = True,
                         backref = 'party_addresses',
                         ondelete = 'cascade',
                         onupdate = 'cascade',
                         lazy = 'subquery' )
    from_date = schema.Column( Date(), default = datetime.date.today, nullable=False, index = True )
    thru_date = schema.Column( Date(), default = end_of_times, nullable=False, index = True )
    comment = schema.Column( Unicode( 256 ) )

    def __str__(self):
        return '%s : %s' % ( six.text_type( self.party ), six.text_type( self.address ) )

    class Admin( EntityAdmin ):
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        list_search = ['party_name', 'street1', 'street2',]
        list_display = ['party_name', 'street1', 'street2', 'city', 'comment']
        form_display = [ 'party', 'street1', 'street2', 'city', 'comment', 
                         'from_date', 'thru_date']
        form_size = ( 700, 200 )
        field_attributes = dict(party_name=dict(editable=False, name='Party', minimal_column_width=30))
        
        def get_compounding_objects( self, party_address ):
            if party_address.address!=None:
                yield party_address.address

class AddressAdmin( PartyAddress.Admin ):
    """Admin with only the Address information and not the Party information"""
    verbose_name = _('Address')
    list_display = ['street1', 'city', 'comment']
    form_display = ['street1', 'street2', 'city', 'comment', 'from_date', 'thru_date']
    field_attributes = dict(street1 = dict(name=_('Street'),
                                           editable=True,
                                           nullable=False),
                            street2 = dict(name=_('Street Extra'),
                                           editable=True),
                            city = dict(name=_('City'),
                                        editable=True,
                                        nullable=False,
                                        delegate=delegates.Many2OneDelegate,
                                        target=City),
                            )
        
    def get_depending_objects( self, party_address ):
        if party_address.party:
            yield party_address.party

class PartyAddressRoleType( Entity ):
    using_options( tablename = 'party_address_role_type' )
    code = schema.Column( Unicode( 10 ) )
    description = schema.Column( Unicode( 40 ) )

    class Admin( EntityAdmin ):
        verbose_name = _('Address role type')
        list_display = ['code', 'description']

@six.python_2_unicode_compatible
class ContactMechanism( Entity ):
    using_options( tablename = 'contact_mechanism' )
    mechanism = schema.Column( camelot.types.VirtualAddress( 256 ), nullable = False )
    party_address = ManyToOne( PartyAddress, ondelete = 'set null', onupdate = 'cascade' )
    party_contact_mechanisms = OneToMany( 'PartyContactMechanism' )

    def __str__(self):
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
                yield party_contact_mechanism
                party = party_contact_mechanism.party
                if party:
                    yield party

@six.python_2_unicode_compatible
class PartyContactMechanism( Entity ):
    using_options( tablename = 'party_contact_mechanism' )

    party = ManyToOne( Party, required = True, ondelete = 'cascade', onupdate = 'cascade',
                       backref = orm.backref('contact_mechanisms', lazy = 'select',
                                             cascade='all, delete, delete-orphan' )
                       )
    contact_mechanism = ManyToOne( ContactMechanism, lazy='joined', required = True, ondelete = 'cascade', onupdate = 'cascade' )
    from_date = schema.Column( Date(), default = datetime.date.today, nullable = False, index = True )
    thru_date = schema.Column( Date(), default = end_of_times, index = True )
    comment = schema.Column( Unicode( 256 ) )

    @hybrid.hybrid_property
    def mechanism( self ):
        if self.contact_mechanism != None:
            return self.contact_mechanism.mechanism

    @mechanism.setter
    def mechanism( self, value ):
        if value != None:
            if self.contact_mechanism:
                self.contact_mechanism.mechanism = value
            else:
                self.contact_mechanism = ContactMechanism( mechanism = value )

    @mechanism.expression
    def mechanism( self ):
        return sql.select(
            [ContactMechanism.mechanism],
            whereclause=ContactMechanism.id==self.contact_mechanism_id).as_scalar()

    def party_name( self ):
        return sql.select( [Party.full_name],
                           whereclause = (Party.id==self.party_id))

    party_name = ColumnProperty( party_name, deferred = True )

    def __str__(self):
        return six.text_type( self.contact_mechanism )

    Admin = PartyContactMechanismAdmin

# begin category definition
@six.python_2_unicode_compatible
class PartyCategory( Entity ):
    using_options( tablename = 'party_category' )
    name = schema.Column( Unicode(40), index=True, nullable = False )
    color = schema.Column(Unicode(8))
# end category definition
    parties = ManyToMany( 'Party', lazy = True, backref='categories',
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

    def __str__(self):
        return self.name or ''
    
    class Admin( EntityAdmin ):
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        list_display = ['name', 'color']

class PartyAdmin( EntityAdmin ):
    verbose_name = _('Party')
    verbose_name_plural = _('Parties')
    list_display = ['name', 'email', 'phone'] # don't use full name, since it might be None for new objects
    list_search = ['full_name']
    form_display = ['addresses', 'contact_mechanisms']
    form_size = (700, 700)
    field_attributes = dict(addresses = {'admin':AddressAdmin},
                            contact_mechanisms = {'admin':PartyPartyContactMechanismAdmin},
                            sex = dict( choices = [( u'M', _('male') ), ( u'F', _('female') )], name=_('Gender')),
                            name = dict( minimal_column_width = 50, name=_('Name')),
                            note = dict( delegate = delegates.NoteDelegate ),
                            first_name = {'name': _('First name')},
                            last_name = {'name': _('Last name')},
                            social_security_number = {'name': _('Social security number')},
                            tax_id = {'name': _('Tax registration')},
                            )
    field_attributes.update( Addressable.Admin.field_attributes )

    def get_compounding_objects( self, party ):
        for party_contact_mechanism in party.contact_mechanisms:
            yield party_contact_mechanism
        for party_address in party.addresses:
            yield party_address

    def get_query( self ):
        query = super( PartyAdmin, self ).get_query()
        query = query.options( orm.selectinload('contact_mechanisms') )
        query = query.options( orm.selectinload('addresses').joinedload('address') )
        return query

    #def flush(self, party):
        #from sqlalchemy.orm.session import Session
        #session = Session.object_session( party )
        #if session:
            ## 
            ## flush all contact mechanism related objects
            ##
            #objects = [party]
            #deleted = ( party in session.deleted )
            #for party_contact_mechanism in party.contact_mechanisms:
                #if deleted:
                    #session.delete( party_contact_mechanism )
                #objects.extend([ party_contact_mechanism, party_contact_mechanism.contact_mechanism ])
            #session.flush( objects )

Party.Admin = PartyAdmin

class OrganizationAdmin( Party.Admin ):
    verbose_name = _( 'Organization' )
    verbose_name_plural = _( 'Organizations' )
    list_search = ['name', 'tax_id']
    list_display = ['name', 'tax_id', 'email', 'phone', 'fax']
    form_display = TabForm( [( _('Basic'), Form( [ WidgetOnlyForm('note'), 'name', 'email', 
                                                   'phone', 
                                                   'fax', 'tax_id', 
                                                   'street1',
                                                   'street2',
                                                   'city',
                                                   'addresses', 'contact_mechanisms'] ) ),
                            ( _('Branding'), Form( ['logo'] ) ),
                            ] )
    field_attributes = dict( Party.Admin.field_attributes )

Organization.Admin = OrganizationAdmin

class PersonAdmin( Party.Admin ):
    verbose_name = _( 'Person' )
    verbose_name_plural = _( 'Persons' )
    list_search = ['first_name', 'last_name']
    list_display = ['first_name', 'last_name', 'email', 'phone']
    form_display = TabForm( [( _('Basic'), Form( [HBoxForm( [ Form( [WidgetOnlyForm('note'), 
                                                              'first_name', 
                                                              'last_name', 
                                                              'sex',
                                                              'email',
                                                              'phone',
                                                              'fax',
                                                              'street1',
                                                              'street2',
                                                              'city',] ),
                                                            [WidgetOnlyForm('picture'),
                                                             Stretch()],
                                                     ] ),
                                                     'comment', ], scrollbars = False ) ),
                            ( _('Official'), Form( ['birthdate', 'social_security_number', 'passport_number',
                                                    'passport_expiry_date', 'addresses', 'contact_mechanisms',], scrollbars = False ) ),
                            ] )
    
Person.Admin = PersonAdmin

aliased_organisation = sql.alias( Organization.table )
aliased_person = sql.alias( Person.table )

Party.full_name = orm.column_property(
    sql.functions.coalesce( sql.select( [sql.functions.coalesce(aliased_person.c.first_name,'') + ' ' + sql.functions.coalesce(aliased_person.c.last_name, '')],
                                           whereclause = and_( aliased_person.c.party_id == Party.id ),
                                           ).limit( 1 ).as_scalar(),
                               sql.select( [aliased_organisation.c.name],
                                           whereclause = and_( aliased_organisation.c.party_id == Party.id ), 
                                           ).limit( 1 ).as_scalar() ),
    deferred=True
)

PartyAddress.party_name = orm.column_property(
    sql.select( [sql.func.coalesce(Party.full_name, '')],
                whereclause = (Party.id==PartyAddress.party_id)),
    deferred = True 
)
