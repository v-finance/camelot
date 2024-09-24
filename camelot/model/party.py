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

import copy
import enum

import sqlalchemy.types

from sqlalchemy.ext import hybrid
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.base import NEVER_SET
from sqlalchemy.types import Unicode
from sqlalchemy import (
    event, orm, schema, sql,
)

from camelot.admin.entity_admin import EntityAdmin
from camelot.admin.action import list_filter
from camelot.core.orm import Entity
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.data.types import zip_code_types
from camelot.sql import is_postgres, is_sqlite
from camelot.sql.types import IdentifyingUnicode, QuasiIdentifyingUnicode
from camelot.types.typing import Note

from camelot.view.controls import delegates
from camelot.view.forms import Form, GroupBoxForm, WidgetOnlyForm
from camelot.view.validator import RegexValidator, ZipcodeValidatorState


class GeographicBoundary( Entity ):
    """The base class for Country and City"""
    __tablename__ = 'geographic_boundary'

    _code = schema.Column('code', QuasiIdentifyingUnicode(length=10), index=True)
    name = schema.Column( QuasiIdentifyingUnicode(length=40), nullable = False )

    row_type = schema.Column( Unicode(40), nullable = False, index=True)

    @hybrid.hybrid_property
    def code(self):
        return self._code

    @code.expression
    def code(cls):
        return cls._code

    @code.setter
    def code(self, code):
        self._code = code

    @hybrid.hybrid_method
    def translation(self, language='nl_BE'):
        # VFIN-2512 : enable eager loading all alternative names, where
        # each property filters the needed alternative name.
        #
        # When language is None, the optimalisation could be made of not
        # looping over alternative names ?
        #
        for alternative_name in self.alternative_names:
            if (alternative_name.language == language) and (alternative_name.row_type=='translation'):
                return alternative_name.name
        return self.name

    @translation.expression
    def translation(cls, language='nl_BE'):
        return sql.select([GeographicBoundaryTranslation.name])\
               .where(GeographicBoundaryTranslation.alternative_name_for_id == cls.id)\
               .where(GeographicBoundaryTranslation.language == language).label('translation')

    @hybrid.hybrid_property
    def name_NL(cls):
        return cls.translation(language='nl_BE')

    @hybrid.hybrid_property
    def name_FR(cls):
        return cls.translation(language='fr_BE')

    __mapper_args__ = {
        'polymorphic_identity': None,
        'polymorphic_on' : row_type
    }

    __table_args__ = (
        schema.Index(
            'ix_geographic_boundary_name', name,
            postgresql_ops={"name": "gin_trgm_ops"},
            postgresql_using='gin'
        ),
        schema.CheckConstraint("code !~ '[-\\s\\./#,]'", name='code', _create_rule=is_postgres),
        schema.CheckConstraint("code GLOB '*[^-. /#,]*'", name='code', _create_rule=is_sqlite),
    )

    __entity_args__ = {
        'editable': False
    }

    full_name = orm.column_property(_code + ' ' + name)

    def __str__(self):
        return u'%s %s' % ( self.code, self.name )
    
    class Admin(EntityAdmin):
        
        verbose_name = _('Geographic Boundary')
        verbose_name_plural = _('Geographic Boundaries')
        
        # Exclude basic column search, as this is replaced by a
        # customized similarity search with alternative names in search query decoration.
        basic_search = False
        
        list_display = ['row_type', 'name', 'code']
        form_display = Form(
            [GroupBoxForm(_('General'), ['name', None, 'code'], columns=2),
             GroupBoxForm(_('NL'), ['name_NL', None], columns=2),
             GroupBoxForm(_('FR'), ['name_FR', None], columns=2),
             GroupBoxForm(_('Coordinates'), ['latitude', None, 'longitude'], columns=2),
             'alternative_names'],
            columns=2)
        
        form_state = 'right'
        field_attributes = {
            'row_type': {
                'name': _('Type'),
                'filter_strategy': list_filter.NoFilter,
                'editable': False,
            },
            'id': {'filter_strategy': list_filter.NoFilter},
            'geographicboundary_id': {'name': _('Id')},
            'name_NL': {'name': _('Name')},
            'name_FR': {'name': _('Name')},
            'alternative_names': {'editable': False},
        }
    
class GeographicBoundaryAlternativeName(Entity):
    
    __tablename__ = 'geographic_boundary_alternative_name'
    
    name = schema.Column(Unicode(100), nullable=False)
    row_type = schema.Column(sqlalchemy.types.Unicode(40), nullable=False, index=True)
    language = schema.Column(sqlalchemy.types.Unicode(6), nullable=True)
    
    alternative_name_for_id = schema.Column(sqlalchemy.types.Integer(),
                                            schema.ForeignKey(GeographicBoundary.id, ondelete='cascade', onupdate='cascade'),
                                            nullable = False,
                                            index = True)
    alternative_name_for = orm.relationship(GeographicBoundary, backref=orm.backref('alternative_names', cascade='all, delete, delete-orphan', overlaps="translations"))
    
    __mapper_args__ = {
        'polymorphic_on' : row_type,
        'polymorphic_identity': 'name',
    }
    
    __table_args__ = (
        schema.Index(
            'ix_geographic_boundary_alternative_name', name,
            postgresql_ops={"name": "gin_trgm_ops"},
            postgresql_using='gin'
        ),
        schema.Index(
            'ix_geographic_boundary_alternative_name_main_municipality', 'alternative_name_for_id', language.is_(None).self_group(), unique=True,
            postgresql_where=sql.and_(row_type == 'main_municipality', language.is_(None)),
            sqlite_where=sql.and_(row_type == 'main_municipality', language.is_(None))),
        schema.Index(
            'ix_geographic_boundary_alternative_name_language_unique', alternative_name_for_id, language, row_type, unique=True,
            postgresql_where=(row_type != 'name'),
            sqlite_where=(row_type != 'name'),
        ),
        schema.CheckConstraint(sql.or_(sql.and_(row_type == 'translation', language.isnot(None)), row_type != 'translation'), name='translation_language'),
    )

    class Admin(EntityAdmin):

        verbose_name = _('Alternative name')
        verbose_name_plural = _('Alternative names')

        list_display = ['name', 'row_type', 'language']
        form_display = list_display

        field_attributes = {
            'row_type': {
                'name': _('Type'),
                'choices': [('translation', _('Translation')),
                            ('main_municipality', _('Main municipality'))]
            },
            'language': {
                'nullable': lambda o: o.row_type != 'translation',
                'editable': lambda o: o.row_type == 'translation',
            }
        }

class GeographicBoundaryTranslation(GeographicBoundaryAlternativeName):
    
    __mapper_args__ = {'polymorphic_identity': 'translation'}
    
GeographicBoundary.translations = orm.relationship(GeographicBoundaryTranslation, lazy='dynamic')

class GeographicBoundaryMainMunicipality(GeographicBoundaryAlternativeName):
    
    __mapper_args__ = {'polymorphic_identity': 'main_municipality'}


class Country( GeographicBoundary ):
    """A subclass of GeographicBoundary used to store the name and the
    ISO code of a country"""
    __tablename__ = 'geographic_boundary_country'
    geographicboundary_id = schema.Column(sqlalchemy.types.Integer(), schema.ForeignKey(GeographicBoundary.id), primary_key=True)

    __mapper_args__ = {'polymorphic_identity': 'country'}

    @classmethod
    def get_or_create(cls, session, code, name):
        country = session.query(cls).filter_by(code=code).first()
        if not country:
            country = Country( code = code, name = name )
            orm.object_session( country ).flush()
        return country

    class Admin(GeographicBoundary.Admin):
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        list_display = ['id', 'name', 'code']

class WithCountry(object):
    """
    Declarative mixin class that shares schema constructs and functionality across GeographicBoundary classes
    that are part of a country.
    """

    @declared_attr
    def country_id(cls):
        return schema.Column(sqlalchemy.types.Integer(),
                            schema.ForeignKey(Country.geographicboundary_id, ondelete='cascade', onupdate='cascade'),
                            nullable=False, index=True)

    @declared_attr
    def country(cls):
        return orm.relationship(Country, foreign_keys=[cls.country_id])

class AdministrativeDivision(GeographicBoundary, WithCountry):

    __tablename__ = 'geographic_boundary_administrative_division'

    geographicboundary_id = schema.Column(sqlalchemy.types.Integer(),
                                          schema.ForeignKey(GeographicBoundary.id,
                                                            name='fk_geographic_boundary_administrative_division_boundary_id'),
                                          primary_key=True, nullable=False)

    __mapper_args__ = {'polymorphic_identity': 'administrative_division'}

    def __str__(self):
        return '{} {} {}'.format(self.code, self.name, self.country)

    class Admin(GeographicBoundary.Admin):

        verbose_name = _('Administrative division')
        verbose_name_plural = _('Administrative divisions (NUTS 3)')

        list_display = ['code', 'name', 'country']

        field_attributes = {h:copy.copy(v) for h,v in GeographicBoundary.Admin.field_attributes.items()}
        attributes_dict = {
            'code': {'name': _('NUTS code')},
            'country_id': {'filter_strategy': list_filter.NoFilter},
        }
        for field_name, attributes in attributes_dict.items():
            field_attributes.setdefault(field_name, {}).update(attributes)

class City(GeographicBoundary, WithCountry):
    """A subclass of GeographicBoundary used to store the name, the postal code
    and the Country of a city"""

    __tablename__ = 'geographic_boundary_city'

    geographicboundary_id = schema.Column(sqlalchemy.types.Integer(),schema.ForeignKey(GeographicBoundary.id),
                                          primary_key=True, nullable=False)
    administrative_division_id = schema.Column(sqlalchemy.types.Integer(),
                                               schema.ForeignKey(AdministrativeDivision.geographicboundary_id, ondelete='restrict', onupdate='cascade'),
                                               nullable=True, index=True)
    administrative_division = orm.relationship(AdministrativeDivision, foreign_keys=[administrative_division_id])
    main_municipality_alternative_names = orm.relationship(GeographicBoundaryMainMunicipality, lazy='dynamic')

    __mapper_args__ = {'polymorphic_identity': 'city'}

    @property
    def zip_code_type(self):
        if self.country is not None:
            try:
                return zip_code_types[self.country.code].name
            except KeyError:
                return

    @GeographicBoundary.code.setter
    def code(self, code):
        # Set the city's zip code to its compact and sanitized representation.
        self._code = ZipcodeValidatorState.for_type(self.zip_code_type, code).value

    @property
    def formatted_zip_code(self):
        return ZipcodeValidatorState.for_city(self).formatted_value

    @hybrid.hybrid_method
    def main_municipality_name(self, language=None):
        matched_mm = default_mm = None
        for main_municipality in self.alternative_names:
            # VFIN-2512 : enable eager loading all alternative names, where
            # each property filters the needed alternative name.
            if main_municipality.row_type != 'main_municipality':
                continue
            if main_municipality.language == language:
                matched_mm = main_municipality.name
            elif main_municipality.language is None:
                default_mm = main_municipality.name
        return matched_mm or default_mm

    @main_municipality_name.expression
    def main_municipality_name(cls, language=None):
        return sql.select([GeographicBoundaryMainMunicipality.name])\
               .where(GeographicBoundaryMainMunicipality.alternative_name_for_id == cls.id)\
               .order_by(GeographicBoundaryMainMunicipality.language==language,
                         GeographicBoundaryMainMunicipality.language==None)\
               .label('main_municipality_name')

    @hybrid.hybrid_method
    def administrative_translation(cls, language):
        translated_name = cls.translation(language)
        if translated_name is not None:
            main_municipality = cls.main_municipality_name(language)
            main_municipality_suffix = ''
            if main_municipality is not None:
                main_municipality_suffix = ' ({})'.format(main_municipality)
            return translated_name + main_municipality_suffix        

    @hybrid.hybrid_property
    def main_municipality(cls):
        return cls.main_municipality_name(None)

    @hybrid.hybrid_property
    def administrative_name(cls):
        return cls.administrative_translation(language=None)

    @hybrid.hybrid_property
    def administrative_name_NL(cls):
        return cls.administrative_translation(language='nl_BE')

    @hybrid.hybrid_property
    def administrative_name_FR(cls):
        return cls.administrative_translation(language='fr_BE')
    
    def __str__(self):
        if None not in (self.name, self.country):
            if self.formatted_zip_code is not None:
                return u'{0} {1} [{2.code}]'.format(self.formatted_zip_code, self.name, self.country)
            return u'{0.name} [{1.code}]'.format(self, self.country)
        return u''

    @classmethod
    def get_or_create(cls, session, country, code, name ):
        city = session.query(City).filter_by( code = code, country = country ).first()
        if not city:
            city = City( code = code, name = name, country = country )
            session.flush()
        return city

    # TODO: refactor this to MessageEnum after move to vFinance repo.
    class Message(enum.Enum):

        invalid_administrative_division = "{} is geen geldige administratieve indeling voor {}"
        invalid_zip_code =                "{} is not a valid zip code for {}: {}"

    def get_messages(self):
        if self.country is not None:

            zipcode_validator_state = ZipcodeValidatorState.for_city(self)
            if not zipcode_validator_state.valid:
                yield _(self.Message.invalid_zip_code.value, self.code, self.country, ugettext(zipcode_validator_state.error_msg))

            if self.administrative_division is not None:
                if self.country != self.administrative_division.country:
                    yield _(self.Message.invalid_administrative_division.value, self.administrative_division, self.country)

    @property
    def note(self) -> Note:
        for msg in self.get_messages():
            return msg

    class Admin(GeographicBoundary.Admin):

        verbose_name = _('City')
        verbose_name_plural = _('Cities')

        list_display = ['id', 'code', 'name', 'administrative_name', 'administrative_division', 'country']
        form_display = Form(
            [GroupBoxForm(_('General'), ['name', None, 'code', None, 'country'], columns=2),
             GroupBoxForm(_('Administrative division'), ['administrative_division', None], columns=2),
             GroupBoxForm(_('Administrative unit'), ['main_municipality', None, 'administrative_name'], columns=2),
             GroupBoxForm(_('NL'), ['name_NL', None, 'administrative_name_NL'], columns=2),
             GroupBoxForm(_('FR'), ['name_FR', None, 'administrative_name_FR'], columns=2),
             GroupBoxForm(_('Coordinates'), ['latitude', None, 'longitude'], columns=2),
             'alternative_names',
             WidgetOnlyForm('note')],
            columns=2)

        field_attributes = {h:copy.copy(v) for h,v in GeographicBoundary.Admin.field_attributes.items()}
        attributes_dict = {
            'code': {
                'name': _('Postal code'),
                'validator_type': RegexValidator.__name__,
                'validator_state': ZipcodeValidatorState.for_city,
                'tooltip': ZipcodeValidatorState.hint_for_city,
            },
            'administrative_name_NL': {'name': _('Administrative name')},
            'administrative_name_FR': {'name': _('Administrative name')},
            'administrative_division': {'name': _('Administrative division (NUTS)')},
            'administrative_division_id': {'filter_strategy': list_filter.NoFilter},
            'country_id': {'filter_strategy': list_filter.NoFilter},
        }
        for field_name, attributes in attributes_dict.items():
            field_attributes.setdefault(field_name, {}).update(attributes)

class Address( Entity ):
    """The Address to be given to a Party (a Person or an Organization)"""
    __tablename__ = 'address'
    street1 = schema.Column( IdentifyingUnicode(length=128), nullable = False )
    street2 = schema.Column( IdentifyingUnicode(length=128) )

    city_geographicboundary_id = schema.Column(sqlalchemy.types.Integer(),
                                               schema.ForeignKey(City.geographicboundary_id, ondelete='cascade', onupdate='cascade'),
                                               nullable=False, index=True)
    city = orm.relationship(City, lazy='subquery')
    
    # Way for user to overrule the zip code and/or administrative division on the address level (e.g. when its not known or incomplete on the city).
    _zip_code = schema.Column(Unicode(10))
    administrative_division_id = schema.Column(sqlalchemy.types.Integer(),
                                               schema.ForeignKey(AdministrativeDivision.geographicboundary_id, ondelete='restrict', onupdate='cascade'),
                                               nullable=True, index=True)
    _administrative_division = orm.relationship(AdministrativeDivision, foreign_keys=[administrative_division_id])

    __table_args__ = (
        schema.CheckConstraint("_zip_code !~ '[-\\s\\./#,]'", name='zip_code', _create_rule=is_postgres),
        schema.CheckConstraint("_zip_code GLOB '*[^-. /#,]*'", name='zip_code', _create_rule=is_sqlite),
    )

    @property
    def administrative_division(self):
        """
        Returns the administrative division of this address.
        If the set city is part of an administrative division, it is always defined as such.
        Otherwise, it can be set manually.
        """
        if self.city is not None:
            if self.city.administrative_division is not None:
                return self.city.administrative_division
            return self._administrative_division

    @administrative_division.setter
    def administrative_division(self, value):
        if self.city is not None and self.city.administrative_division is None:
            self._administrative_division = value

    @hybrid.hybrid_property
    def zip_code( self ):
        if self.city is not None:
            return self._zip_code or self.city.code
        return self._zip_code

    @zip_code.expression
    def zip_code(cls):
        return cls._zip_code

    @zip_code.setter
    def zip_code(self, code):
        # Only allow to overrule the address' zip code if its city's code is undefined.
        if self.city is not None and not self.city.code:
            # Set the zip code to its compact and sanitized representation.
            self._zip_code = ZipcodeValidatorState.for_type(self.city.zip_code_type, code).value

    @property
    def zip_code_type(self):
        if self.city is not None:
            return self.city.zip_code_type

    @property
    def formatted_zip_code(self):
        return ZipcodeValidatorState.for_addressable(self).formatted_value

    name = orm.column_property(sql.select(
        [street1 + ', ' + sql.func.coalesce(_zip_code, GeographicBoundary.code) + ' ' + GeographicBoundary.name],
        whereclause=(GeographicBoundary.id == city_geographicboundary_id)), deferred=True)

    @classmethod
    def get_or_create(cls, session, street1, street2, city, zip_code):
        address = session.query(Address).filter_by( street1 = street1, street2 = street2, city = city, zip_code = zip_code ).first()
        if not address:
            address = cls( street1 = street1, street2 = street2, city = city, zip_code = zip_code )
            session.flush()
        return address

    def get_messages(self):
        if self.city is not None:
            yield from self.city.get_messages()

            zipcode_validator_state = ZipcodeValidatorState.for_addressable(self)
            if not zipcode_validator_state.valid:
                yield _(City.Message.invalid_zip_code.value, self._zip_code, self.city.country, ugettext(zipcode_validator_state.error_msg))

            if self.administrative_division is not None and self.city.country != self.administrative_division.country:
                yield _(City.Message.invalid_administrative_division.value, self.administrative_division, self.city.country)

    def __str__(self):
        city_name = self.city.name if self.city is not None else ''
        return u'%s, %s %s' % ( self.street1 or '', self.formatted_zip_code or '', city_name or '' )

    class Admin( EntityAdmin ):
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        list_display = ['street1', 'street2', 'city']
        form_display = ['street1', 'street2', 'zip_code', 'city', 'administrative_division']
        form_state = 'right'
        field_attributes = {
            'street1': {'minimal_column_width':30},
            'zip_code': {
                'editable': lambda o: o.city is not None and not o.city.code,
                'validator_type': RegexValidator.__name__,
                'validator_state': ZipcodeValidatorState.for_addressable,
                'tooltip': ZipcodeValidatorState.hint_for_addressable,
                },
            'administrative_division': {
                'delegate':delegates.Many2OneDelegate,
                'target': AdministrativeDivision,
                'editable': lambda o: o.city is not None and o.city.administrative_division is None
            },
        }

        def get_depending_objects( self, address ):
            for party_address in address.party_addresses:
                yield party_address
                if party_address.party != None:
                    yield party_address.party

@event.listens_for(Address.city, 'set', propagate=True)
def receive_city_set(target, city, oldvalue, initiator):
    if oldvalue is not NEVER_SET and oldvalue != city:
        if city is None or city.administrative_division is not None:
            target._administrative_division = None


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
    def street2(cls):
        return sql.select([Address.street2],
                          whereclause=cls.first_address_filter(),
                          limit=1).as_scalar()

    @street2.setter
    def street2( self, value ):
        return self._set_address_field( u'street2', value )

    @hybrid.hybrid_property
    def zip_code( self ):
        return self._get_address_field( u'zip_code' )
    
    @zip_code.setter
    def zip_code( self, value ):
        return self._set_address_field( u'zip_code', value )

    @zip_code.expression
    def zip_code(cls):
        return Address.zip_code

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

    @property
    def formatted_zip_code(self):
        if self.city is not None:
            return self.city.formatted_zip_code

    @hybrid.hybrid_property
    def administrative_division(self):
        return self._get_address_field('administrative_division')

    @administrative_division.setter
    def administrative_division( self, value ):
        return self._set_address_field('administrative_division', value)

    @administrative_division.expression
    def administrative_division(cls):
        GB = orm.aliased(GeographicBoundary)
        return sql.select([GB.code + ' ' + GB.name],
                          whereclause=sql.and_(
                              GB.id==Address.administrative_division_id,
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
    def zip_code( self ):
        return self._get_address_field( u'zip_code' )

    @zip_code.expression
    def zip_code(cls):
        return cls._zip_code

    @zip_code.setter
    def zip_code( self, value ):
        return self._set_address_field( u'zip_code', value )

    @zip_code.expression
    def zip_code( self ):
        return Address.zip_code

    @property
    def formatted_zip_code(self):
        if self.address:
            return self.address.formatted_zip_code

    @hybrid.hybrid_property
    def city( self ):
        return self._get_address_field( u'city' )
    
    @city.setter
    def city( self, value ):
        return self._set_address_field( u'city', value )

    @city.expression
    def city( self ):
        return Address.city_geographicboundary_id

    @property
    def administrative_division(self):
        return self._get_address_field( u'administrative_division' )

    @administrative_division.setter
    def administrative_division( self, value ):
        return self._set_address_field( u'administrative_division', value )

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
                         target = City),
            administrative_division = dict( editable = lambda o: o.city is not None and o.city.administrative_division is None,
                                            delegate = delegates.Many2OneDelegate,
                                            target = AdministrativeDivision),
            zip_code = dict( editable = lambda o: o.city is not None and not o.city.code),
        )


class PartyAddressRoleType( Entity ):
    __tablename__ = 'party_address_role_type'
    code = schema.Column( Unicode( 10 ) )
    description = schema.Column( Unicode( 40 ) )

    class Admin( EntityAdmin ):
        verbose_name = _('Address role type')
        list_display = ['code', 'description']

# begin category definition

class PartyCategory( Entity ):
    __tablename__ = 'party_category'
    name = schema.Column( Unicode(40), index=True, nullable = False )
    color = schema.Column(Unicode(8))
# end category definition

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
