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
"""
This module provides the :class:`camelot.core.orm.entity.EntityBase` declarative base class, 
as well as its metaclass :class:`camelot.core.orm.entity.EntityMeta`.  Those are the building
blocks for creating the :class:`camelot.core.orm.Entity`.

These classes can be reused if a custom base class is needed.
"""

import datetime
import functools
import logging

from sqlalchemy import orm, schema
from sqlalchemy.orm.decl_api import ( _declarative_constructor,
                                      DeclarativeMeta )

from ...types import Enumeration, PrimaryKey
from . import Session

LOGGER = logging.getLogger('camelot.core.orm.entity')

class EntityMeta( DeclarativeMeta ):
    """
    Specialized metaclass for Entity classes that inherits from :class:`sqlalchmey.ext.declarative.DeclarativeMeta`.
    It provides entities with the following behaviour and/or functionality:

    Auto-setting of primary key column
    ----------------------------------
    If no primary key column is defined in an entity's class definition yet, an primary key column named 'id' will be set on the class.
    NOTE: this behaviour is deprecated, and should be replaced by explicity primary column definitions in the entity classes themselves
    before switching to SQLAlchemy version 1.4. In that SQLA version, the `sqlalchemy.ext.declarative` package is integrated into `sqlalchemy.orm`
    and the declarative mapping registry style is changed, which impacts this primary key column setting.

    Notes on metaclasses
    --------------------
    Metaclasses are not part of objects' class hierarchy whereas base classes are.
    So when a method is called on an object it will not look on the metaclass for this method, however the metaclass may have created it during the class' or object's creation.
    They are generally used for use cases outside of the default rules of object-oriented programming.
    In this case for example, the metaclass provides subclasses the means to register themselves on on of its base classes,
    which is an OOP anti-pattern as classes should not know about their subclasses.
    """

    # new is called to create a new Entity class
    def __new__( cls, classname, bases, dict_ ):
        #
        # don't modify the Entity class itself
        #
        if classname != 'Entity':
            #
            # use default tablename if none set
            #
            for base in bases:
                if hasattr(base, '__tablename__'):
                    break
            else:
                dict_.setdefault('__tablename__', classname.lower())
            for base in bases:
                if hasattr(base, '__mapper_args__'):
                    break
            else:
                dict_.setdefault('__mapper_args__', dict())

        _class = super( EntityMeta, cls ).__new__( cls, classname, bases, dict_ )
        # adds primary key column to the class
        if classname != 'Entity':
            if dict_.get('__tablename__') is not None:
                for val in dict_.values():
                    if isinstance(val, schema.Column) and val.primary_key: # val.primary_key checks if the primary_key attribute of the Column is set to True
                        break
                else:
                    # table.primary_key.issubset([]) tests if there are no primary keys(aka tests if empty)
                    # table.primary_key returns an iterator so we can't test the length or something like that
                    table = dict_.get('__table__', None)
                    if table is None or table.primary_key is None:
                        _class.id = schema.Column(PrimaryKey(), primary_key=True)

        return _class

    @property
    def endpoint(cls):
        from vfinance.interface.endpoint import Endpoint
        return Endpoint.get(cls)

    def get_polymorphic_types(cls):
        """
        In case of a polymorphic base class with a polymorphic discriminator column
        that is of type Enumeration, return its contained type enumeration.
        Note: a class which both defines the polymorphic on as a polymoprhic identity,
        is not considered a polymorphic base class.
        """
        polymorphic_on = cls.__mapper_args__.get('polymorphic_on')
        polymorphic_identity = cls.__mapper_args__.get('polymorphic_identity')
        if polymorphic_on is not None and polymorphic_identity is None:
            polymorphic_on_col = polymorphic_on
            if isinstance(polymorphic_on, orm.attributes.InstrumentedAttribute):
                polymorphic_on_col = polymorphic_on.prop.columns[0]
            if isinstance(polymorphic_on_col.type, Enumeration):
                return polymorphic_on_col.type.enum

    def get_cls_by_discriminator(cls, primary_discriminator, *secondary_discriminators):
        return cls.endpoint.get_cls_by_discriminator(primary_discriminator, *secondary_discriminators)

    def get_discriminator_value(cls, entity_instance):
        """Return the given entity instance's discriminator value."""
        assert isinstance(entity_instance, cls)
        if cls.endpoint.discriminator is not None:
            return tuple([discriminator_prop.__get__(entity_instance, None) for discriminator_prop in cls.endpoint.discriminator])

    def set_discriminator_value(cls, entity_instance, primary_discriminator_value, *secondary_discriminator_values):
        """Set the given entity instance's discriminator with the provided discriminator value."""
        assert isinstance(entity_instance, cls)
        if cls.endpoint.discriminator is not None:
            (primary_discriminator, *secondary_discriminators) = cls.endpoint.discriminator
            if primary_discriminator_value is not None:
                assert primary_discriminator_value in cls.endpoint.discriminator_types.__members__, '{} is not a valid discriminator value for this entity.'.format(primary_discriminator_value)
                primary_discriminator.__set__(entity_instance, primary_discriminator_value)
                for secondary_discriminator_prop, secondary_discriminator_value in zip(secondary_discriminators, secondary_discriminator_values):
                    entity = secondary_discriminator_prop.prop.entity.entity
                    assert isinstance(secondary_discriminator_value, entity), '{} is not a valid secondary discriminator value for this entity. Must be of type {}'.format(secondary_discriminator_value, entity)
                    secondary_discriminator_prop.__set__(entity_instance, secondary_discriminator_value)

    def get_secondary_discriminator_types(cls):
        return cls.endpoint.get_secondary_discriminator_types()

    # init is called after the creation of the new Entity class, and can be
    # used to initialize it
    def __init__( cls, classname, bases, dict_ ):
        #
        # Calling DeclarativeMeta's __init__ creates the mapper and
        # the table for this class
        #
        super( EntityMeta, cls ).__init__( classname, bases, dict_ )
        if '__table__' in cls.__dict__:
            setattr( cls, 'table', cls.__dict__['__table__'] )

#
# Keep these functions separated from EntityBase to be able
# to reuse them in parts unrelated to EntityBase
#

def update_or_create_entity( cls, data, surrogate = True ):
    mapper = orm.class_mapper( cls )
    if mapper.polymorphic_on is not None:
        # assume the mapper is polymorphic on a column, otherwise we're unable
        # to deserialize it anyway
        polymorphic_property = mapper.get_property_by_column(mapper.polymorphic_on)
        try:
            polymorphic_identifier = data[polymorphic_property.key]
            mapper = mapper.polymorphic_map[polymorphic_identifier]
        except KeyError:
            # we can only select a subclass if the polymporthic identifier is
            # in the data and that identifier is known to the mapper
            pass
        cls = mapper.class_

    pk_props = mapper.primary_key

    # if all pk are present and not None
    if not [1 for p in pk_props if data.get( p.key ) is None]:
        pk_tuple = tuple( [data[prop.key] for prop in pk_props] )
        record = cls.query.get(pk_tuple)
        if record is None:
            record = cls()
    else:
        if surrogate:
            record = cls()
        else:
            raise Exception("cannot create non surrogate without pk")
    dict_to_entity( record, data )
    return record

def dict_to_entity( entity, data ):
    """Update a mapped object with data from a JSON-style nested dict/list
    structure.

    :param entity: the Entity object into which to store the data
    :param data: a `dict` with data to store into the entity
    """
    # surrogate can be guessed from autoincrement/sequence but I guess
    # that's not 100% reliable, so we'll need an override

    mapper = orm.object_mapper( entity )

    for key, value in data.items():
        if isinstance( value, dict ):
            dbvalue = getattr( entity, key )
            rel_class = mapper.get_property(key).mapper.class_
            pk_props = orm.class_mapper( rel_class ).primary_key

            # If the data doesn't contain any pk, and the relationship
            # already has a value, update that record.
            if not [1 for p in pk_props if p.key in data] and \
               dbvalue is not None:
                dict_to_entity( dbvalue, value )
            else:
                record = update_or_create_entity( rel_class, value)
                setattr(entity, key, record)
        elif isinstance(value, list) and \
             value and isinstance(value[0], dict):

            rel_class = mapper.get_property(key).mapper.class_
            new_attr_value = []
            for row in value:
                if not isinstance(row, dict):
                    raise Exception(
                        'Cannot send mixed (dict/non dict) data '
                        'to list relationships in from_dict data.')
                record = update_or_create_entity( rel_class, row)
                new_attr_value.append(record)
            setattr(entity, key, new_attr_value)
        else:
            setattr(entity, key, value)

def entity_to_dict( entity, deep = {}, exclude = [], deep_primary_key=False ):
    """Generate a JSON-style nested dict/list structure from an object.

    :param deep_primary_key: when related objects are generated, preserve
        the primary key of those related objects
    """

    mapper = orm.object_mapper( entity )

    col_prop_names = [p.key for p in mapper.iterate_properties \
                      if isinstance(p, orm.properties.ColumnProperty)]
    data = dict([(name, getattr(entity, name))
                 for name in col_prop_names if name not in exclude])
    for rname, rdeep in deep.items():
        dbdata = getattr(entity, rname)
        prop = mapper.get_property( rname )
        fks = prop.remote_side
        #FIXME: use attribute names (ie coltoprop) instead of column names
        remote_exclude = exclude + [ c.name for c in fks ]
        if prop.direction==orm.interfaces.MANYTOONE and deep_primary_key:
            remote_exclude = exclude
        if dbdata is None:
            data[rname] = None            
        elif isinstance(dbdata, list):            
            data[rname] = [ entity_to_dict( o, rdeep, remote_exclude, deep_primary_key ) for o in dbdata ]
        else:
            data[rname] = entity_to_dict( dbdata, rdeep, remote_exclude, deep_primary_key )

    return data    

@functools.total_ordering
class EntityBase( object ):
    """A declarative base class that adds some methods that used to be
    available in Elixir"""

    def __init__( self, *args, **kwargs ): 
        session = kwargs.pop('_session', None)
        _declarative_constructor( self, *args, **kwargs )
        # due to cascading rules and a constructor argument, the object might
        # allready be in a session
        if orm.object_session( self ) == None:
            if session==None:
                session=Session()
            session.add( self ) 

    #
    # methods below were copied from camelot.core.orm to mimic the Elixir Entity
    # behavior
    #

    def set( self, **kwargs ):
        for key, value in kwargs.items():
            setattr( self, key, value )

    @classmethod
    def update_or_create( cls, data, surrogate = True ):
        return update_or_create_entity( cls, data, surrogate )

    def from_dict( self, data ):
        """
        Update a mapped class with data from a JSON-style nested dict/list
        structure.
        """
        return dict_to_entity( self, data )

    def to_dict( self, deep = {}, exclude = [], deep_primary_key=False ):
        """Generate a JSON-style nested dict/list structure from an object."""
        return entity_to_dict( self, deep, exclude, deep_primary_key )

    # session methods
    def flush(self, *args, **kwargs):
        return orm.object_session(self).flush([self], *args, **kwargs)

    def delete(self, *args, **kwargs):
        return orm.object_session(self).delete(self, *args, **kwargs)

    def expire(self, *args, **kwargs):
        return orm.object_session(self).expire(self, *args, **kwargs)

    def refresh(self, *args, **kwargs):
        return orm.object_session(self).refresh(self, *args, **kwargs)

    def expunge(self, *args, **kwargs):
        return orm.object_session(self).expunge(self, *args, **kwargs)

    def __lt__(self, other):
        return id(self) < id(other)

    @classmethod
    def get_by(cls, *args, **kwargs):
        """
        Returns the first instance of this class matching the given criteria.
        This is equivalent to:
        session.query(MyClass).filter_by(...).first()
        """
        return Session().query( cls ).filter_by(*args, **kwargs).first()

    @classmethod
    def get(cls, *args, **kwargs):
        """
        Return the instance of this class based on the given identifier,
        or None if not found. This is equivalent to:
        session.query(MyClass).get(...)
        """
        return Session().query( cls ).get(*args, **kwargs)

    def is_applicable_at(self, at):
        """
        Return whether this entity instance is applicable at the given date.
        This method requires the entity class to have its application date range
        configured in a `vfinance.interface.endpoint.Endpoint`.
        An instance is applicable at the given date when it is later than the instance's
        application date, and the application date is not later than end_of_times.

        :raises: An AssertionError when the application_date is not configured in a `vfinance.interface.endpoint.Endpoint`.
        """
        # @todo : move this method to a place where end of times is known
        end_of_times = datetime.date(2400, 12, 31)
        entity = type(self)
        assert entity.endpoint.application_date is not None
        assert isinstance(at, datetime.date)
        application_date = entity.endpoint.application_date.__get__(self, None)
        return application_date is not None and not (application_date >= end_of_times or at < application_date)
