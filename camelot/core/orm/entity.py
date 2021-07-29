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

import bisect
import logging


from sqlalchemy import orm, schema, sql, util
from sqlalchemy.ext.declarative.api import ( _declarative_constructor,
                                             DeclarativeMeta )
from sqlalchemy.ext import hybrid

from ...types import Enumeration, PrimaryKey
from . statements import MUTATORS
from . properties import EntityBuilder
from . import Session, options

LOGGER = logging.getLogger('camelot.core.orm.entity')

class EntityDescriptor(object):
    """
    EntityDescriptor holds information about the Entity before it is
    passed to Declarative.  It is used to search for inverse relations
    defined on an Entity before the relation is passed to Declarative.

    :param entity_base: The Declarative base class used to subclass the
        entity
    """

    global_counter = 0

    def __init__( self, entity_base ):
        self.processed = False
        self.entity_base = entity_base
        self.parent = None
        self.relationships = []
        self.has_pk = False
        self._pk_col_done = False
        self.builders = [] 
        self.constraints = []
        self.counter = EntityDescriptor.global_counter
        EntityDescriptor.global_counter += 1
        # set default value for other options
        for key, value in options.options_defaults.items():
            if isinstance( value, dict ):
                value = value.copy()
            setattr( self, key, value )

    def set_entity( self, entity ):
        self.entity = entity
        self.tablename = entity.__tablename__
        #
        # verify if a primary key was set manually
        #
        for key, value in entity.__dict__.items():
            if isinstance( value, schema.Column ):
                if value.primary_key:
                    self.has_pk = True
    
    def get_top_entity_base(self):
        """
        :return: the Declarative base class in the top of the class hierarchy
        """
        base_descriptor = getattr( self.entity_base, '_descriptor', None )
        if base_descriptor is not None:
            return base_descriptor.get_top_entity_base()
        return self.entity_base

    def add_builder( self, builder ):
        """Add an `EntityBuilder`
        """
        # builders have to be executed in the order they were
        # created
        bisect.insort( self.builders, builder )

    @property
    def primary_keys( self ):
        return self.entity.__table__.primary_key

    @property
    def table_fullname( self ):
        return self.entity.__tablename__

    @property
    def metadata( self ):
        return self.entity.__table__.metadata

    def create_non_pk_cols(self):
        self.call_builders( 'create_non_pk_cols' )

    def create_pk_cols( self ):
        """
        Create primary_key columns. That is, call the 'create_pk_cols'
        builders then add a primary key to the table if it hasn't already got
        one and needs one.

        This method is "semi-recursive" in some cases: it calls the
        create_keys method on ManyToOne relationships and those in turn call
        create_pk_cols on their target. It shouldn't be possible to have an
        infinite loop since a loop of primary_keys is not a valid situation.
        """
        self.call_builders( 'create_pk_cols' )

        if self._pk_col_done:
            return

        self._pk_col_done = True

    def create_properties(self):
        self.call_builders( 'create_properties' )

    def create_tables(self):
        self.call_builders( 'create_tables' )

    def finalize(self):
        self.call_builders( 'finalize' )
        mapper = orm.class_mapper(self.entity)
        if self.order_by:
            mapper.order_by = self.translate_order_by( self.order_by )
        # set some convenience attributes to the Entity
        setattr(self.entity, 'table', mapper.local_table)

    def add_column( self, key, col ):
        setattr( self.entity, key, col )
        if hasattr( col, 'primary_key' ) and col.primary_key:
            self.has_pk = True   

    def add_constraint( self, constraint ):
        self.constraints.append( constraint )            

    def append_constraints( self ): 
        table = orm.class_mapper( self.entity ).local_table
        for constraint in self.constraints:
            table.append_constraint( constraint )

    def get_inverse_relation( self, rel, check_reverse=True ):
        '''
        Return the inverse relation of rel, if any, None otherwise.
        '''
        matching_rel = None
        for other_rel in self.relationships:
            if rel.is_inverse( other_rel ):
                if matching_rel is None:
                    matching_rel = other_rel
                else:
                    raise Exception(
                        "Several relations match as inverse of the '%s' "
                        "relation in entity '%s'. You should specify "
                        "inverse relations manually by using the inverse "
                        "keyword."
                        % (rel.name, rel.entity.__name__))
        # When a matching inverse is found, we check that it has only
        # one relation matching as its own inverse. We don't need the result
        # of the method though. But we do need to be careful not to start an
        # infinite recursive loop.
        if matching_rel and check_reverse:
            rel.entity._descriptor.get_inverse_relation(matching_rel, False)

        return matching_rel

    def add_property( self, name, prop ):
        mapper = orm.class_mapper( self.entity )
        mapper.add_property( name, property )

    def call_builders(self, what):
        for builder in self.builders:
            if hasattr(builder, what):
                getattr(builder, what)()

    def find_relationship(self, name):
        for rel in self.relationships:
            if rel.name == name:
                return rel
        if self.parent:
            return self.parent._descriptor.find_relationship(name)
        else:
            return None    

    def translate_order_by( self, order_by ):
        if isinstance( order_by, str ):
            order_by = [order_by]

        order = []

        mapper = orm.class_mapper( self.entity )
        for colname in order_by:
            prop = mapper.columns[ colname.strip('-') ]
            if colname.startswith('-'):
                prop = sql.desc( prop )
            order.append( prop )

        return order        

class EntityMeta( DeclarativeMeta ):
    """
    Subclass of :class:`sqlalchmey.ext.declarative.DeclarativeMeta`.
    This metaclass processes the Property and ClassMutator objects.
    
    Facade class registration
    -------------------------
    This metaclass also provides type-based entity classes with a means to register facade classes for specific types, type groups or a default one for unregistered types,
    on one of its base classes, to allow type-specific facade and related Admin behaviour.
    To use this behaviour, the '__facade_args__' property is used on both the base Entity class for which specific facade classes are needed,
    as on the specific facade classes.
    This property is a dictionary that contains all the necessary facade arguments.
    On the base class, it should contain the 'discriminator' argument, which should reference the type column of the base class that is used to discriminate facade classes.
    This column should be an Enumeration type column, which defines the types that are allowed registering classes for.
    In order to register a facade class for a specific type, the 'type' argument should be defined as a specific type of the base Entity class' '__types__'.
    To register a class as the default class for types that do not have a specific class registered, the 'default' argument can be provided and set to True.
    In case the registered types are grouped, it is also possible to register a facade class for one of those type groups and thereby registering if as the default class
    for all types in that group if they do not have a specific class registered.
    
    :example: | class SomeClass(Entity):
              |     __tablename__ = 'some_tablename'
              |     ...
              |     described_by = Column(IntEnum(some_class_types), ...)
              |     ...
              |     __facade_args__ = {
              |         'discriminator': described_by
              |     }
              |     ...
              |
              | class SomeFacadeClass(SomeClass)
              |     __facade_args__ = {
              |         'type': some_class_types.certain_type.name
              |     }
              |     ...
              |
              | class SomeGroupFacadeClass(SomeClass)
              |     __facade_args__ = {
              |         'group': allowed_type_groups.certain_type_group.name
              |     }
              |     ...
              |
              | class DefaultFacadeClass(SomeClass)
              |     __facade_args__ = {
              |         'default': True
              |     }
              |     ...
    
    This metaclass also provides each entity class with a way to generically retrieve a registered classes for a specific type with the 'get_cls_by_type' method.
    This will return the registered class for a specific given type or type group, if any are registered on the class (or its Base). See its documentation for more details.
    
    :example: | SomeClass.get_cls_by_type(some_class_types.certain_type.name) == SomeFacadeClass
              | SomeClass.get_cls_by_type(some_class_types.unregistered_type.name) == DefaultFacadeClass
              | BaseClass.get_cls_by_type(allowed_type_groups.certain_registered_type_group.name) == RegisteredClassForGroup
    
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
            entity_base = None
            for base in bases:
                # in case the base class is itself a subclass of Entity,
                # get to Entity itself.
                if hasattr(base, '_decl_class_registry'):
                    entity_base = base
                    break
            dict_['_descriptor'] = EntityDescriptor( entity_base )
            #
            # process the mutators
            #
            for mutator, args, kwargs in dict_.get( MUTATORS, [] ):
                mutator.process( dict_, *args, **kwargs )
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
            
            for base in bases:
                if hasattr(base, '__facade_args__'):
                    break
            else:
                dict_.setdefault('__facade_args__', dict())
            
            for base in bases:
                if hasattr(base, '__types__'):
                    break
            else:
                dict_.setdefault('__types__', None)
            
            for base in bases:
                if hasattr(base, '__type_groups__'):
                    break
            else:
                dict_.setdefault('__type_groups__', None)
            
            for base in bases:
                if hasattr(base, '__cls_for_type__'):
                    break
            else:
                dict_.setdefault('__cls_for_type__', dict())
        
            facade_args = dict_.get('__facade_args__')
            if facade_args is not None:
                discriminator = facade_args.get('discriminator')
                if discriminator is not None:
                    assert isinstance(discriminator, (sql.schema.Column, orm.attributes.InstrumentedAttribute)), 'Discriminator must be a sql.schema.Column or an InstrumentedAttribute'
                    discriminator_col = discriminator
                    if isinstance(discriminator, orm.attributes.InstrumentedAttribute):
                        discriminator_col = discriminator.prop.columns[0]
                    assert isinstance(discriminator_col.type, Enumeration), 'Discriminator column must be of type Enumeration'
                    assert isinstance(discriminator_col.type.enum, util.OrderedProperties), 'Discriminator column has no enumeration types defined'
                    dict_['__types__'] = discriminator_col.type.enum
                    if hasattr(discriminator_col.type.enum, 'get_groups'):
                        dict_['__type_groups__'] = discriminator_col.type.enum.get_groups()
                    dict_['__cls_for_type__'] = dict()
            
        _class = super( EntityMeta, cls ).__new__( cls, classname, bases, dict_ )
        # adds primary key column to the class
        if classname != 'Entity' and dict_.get('__tablename__') is not None:
            for val in dict_.values():
                if isinstance(val, schema.Column) and val.primary_key: # val.primary_key checks if the primary_key attribute of the Column is set to True
                    break
            else:
                # table.primary_key.issubset([]) tests if there are no primary keys(aka tests if empty)
                # table.primary_key returns an iterator so we can't test the length or something like that
                if (table := dict_.get('__table__', None)) is None or table.primary_key.issubset([]):
                    _class.id = schema.Column(PrimaryKey(), **options.DEFAULT_AUTO_PRIMARYKEY_KWARGS)
                
        cls.register_class(cls, _class, dict_)
        return _class
    
    def register_class(cls, _class, dict_):
        facade_args = dict_.get('__facade_args__')
        if facade_args is not None:
            _type = facade_args.get('type')
            if _type is not None:
                assert _class.__types__ is not None, 'This class has no types defined to register classes for.'
                assert _type in _class.__types__.__members__, 'The type this class registers for is not a member of the types that are allowed.'
                assert _type not in _class.__cls_for_type__, 'Already a class defined for type {0}'.format(_type)
                _class.__cls_for_type__[_type] = _class
            _default = facade_args.get('default')
            if _default == True:
                assert _class.__types__ is not None, 'This class has no types defined to register classes for.'
                assert _type is None, 'Can not register this class for a specific type and as the default class'
                assert None not in _class.__cls_for_type__, 'Already a default class defined for types {}: {}'.format(_class.__types__, _class.__cls_for_type__[None])
                _class.__cls_for_type__[None] = _class
            _group = facade_args.get('type_group')
            if _group is not None:
                assert _class.__type_groups__ is not None, 'This class has no type groups defined to register classes for.'
                assert _type is None, 'Can not register this class for both a specific type and for a specific type group'
                assert _default is None, 'Can not register this class as both the default class and for a specific type group'
                assert _group in _class.__type_groups__.__members__, 'The type group this class registers for is not a member of the type groups that are allowed.'
                assert _group not in _class.__cls_for_type__, 'Already a class defined for type group {0}'.format(_group)
                _class.__cls_for_type__[_group] = _class
                
    def get_cls_by_type(cls, _type):
        """
        Retrieve the corresponding class for the given type or type_group if one is registered on this class or its base.
        This can be the class that is specifically registered for the given type or type group, or a possible registered default class otherwise.
        Providing no type will also return the default registered class if present.
        
        :param _type:  either None which will lookup a possible registered default class, or a member of a sqlalchemy.util.OrderedProperties instance.
                       If this class or its base have types registration enabled, this should be a member of the set __types__ or a member of the
                       __type_groups__, that get auto-set in case the set types are grouped.
        :return:       the class that is registered for the given type, which inherits from the class where the allowed types are registered on, or the class itself if not.
                       In case the given type is:
                        * None; the registered default class will be returned, if present.
                        * a member of the allowed __type_groups__; a possible registered class for the type group will be returned, or the registered default class otherwise.
                        * a member of the allowed __types__; a possible registered class for the type will be returned,
                          otherwise a possible registered class for the group of the type, if applicable, and otherwise the registered default class.
                       Examples:
                       | BaseClass.get_cls_by_type(allowed_types.certain_type.name) == CertainTypeClass
                       | BaseClass.get_cls_by_type(allowed_type_groups.certain_registered_type_group.name) == RegisteredClassForGroup
                       | BaseClass.get_cls_by_type(allowed_types.certain_unregistered_type.name) == RegisteredDefaultClass
        :raises :      an AttributeException when the given argument is not a valid type
        """
        if cls.__types__ is not None:
            groups = cls.__type_groups__.__members__ if cls.__type_groups__ is not None else []
            types = cls.__types__
            if _type is None or _type in types.__members__ or _type in groups:
                group = _type
                if groups and _type in types.__members__ and types[_type].grouped_by is not None:
                    group = types[_type].grouped_by.name
                
                return cls.__cls_for_type__.get(_type) or \
                       cls.__cls_for_type__.get(group) or \
                       cls.__cls_for_type__.get(None)
            LOGGER.warn("No registered class found for '{0}' (of type {1})".format(_type, type(_type)))
            raise Exception("No registered class found for '{0}' (of type {1})".format(_type, type(_type)))
    
    def _get_facade_arg(cls, key):
        for cls_ in (cls,) + cls.__mro__:
            if hasattr(cls_, '__facade_args__') and key in cls_.__facade_args__:
                return cls_.__facade_args__[key]
    
    def get_cls_discriminator(cls):
        discriminator = cls._get_facade_arg('discriminator')
        if discriminator is not None:
            if isinstance(discriminator, sql.schema.Column):
                return getattr(cls, discriminator.key)
            return discriminator

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

    @hybrid.hybrid_property
    def query( self ):
        return Session().query( self.__class__ )

    @query.expression
    def query( cls ):
        return Session().query( cls )

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

