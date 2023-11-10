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
import logging
import re

from enum import Enum

from sqlalchemy import orm, schema, sql, util
from sqlalchemy.ext.declarative.api import ( _declarative_constructor,
                                             DeclarativeMeta )
from sqlalchemy.ext import hybrid
from sqlalchemy.types import Date, Integer

from ...types import Enumeration, PrimaryKey
from ..naming import initial_naming_context, EntityNamingContext
from . statements import MUTATORS
from . import Session, options

LOGGER = logging.getLogger('camelot.core.orm.entity')

class EntityClsRegistry(object):
    """
    A Registry that stores class registration for
    discriminatory values of a :class:`.Entity` class.
    """

    class DiscriminatorType(Enum):
        """
        Enumeration that described the aggregation level of
        a class registration's discriminator value.
        """

        single =  1
        group =   2

    def __init__(self):
        """
        Construct a new :class:`.EntityClsRegistry`.
        """
        self._registry = {disc_type: dict() for disc_type in self.DiscriminatorType}
        self._exclusive = {disc_type: dict() for disc_type in self.DiscriminatorType}

    def register(self, cls, primary_discriminator, *secondary_discriminators, discriminator_type=DiscriminatorType.single, exclusive=False):
        """
        Register a class for the given discriminatory values.
        """
        assert discriminator_type in self.DiscriminatorType
        if secondary_discriminators:
            # With secondary discriminators, the primary discriminator should resolve to a map of its secondary discriminator,
            # allowing for multiple discriminated classes for the same primary discriminator.
            if primary_discriminator not in self._registry[discriminator_type]:
                self._registry[discriminator_type][primary_discriminator] = dict()
            assert isinstance(self._registry[discriminator_type][primary_discriminator], dict),\
                   'Already a class registered for the single primary discriminatory type {0}. Can not be combined with a multi-level discriminator registration.'.format(primary_discriminator)
            assert (*secondary_discriminators,) not in self._registry[discriminator_type][primary_discriminator],\
                   'Already a class registered for multi-level discriminators {}'.format(tuple(primary_discriminator, *secondary_discriminators))
            assert primary_discriminator not in self._exclusive[discriminator_type],\
                   'Already a class registered exclusively for multi-level discriminators {}'.format(tuple(primary_discriminator, ))
            self._registry[discriminator_type][primary_discriminator][(*secondary_discriminators,)] = cls
            if exclusive:
                self._exclusive[discriminator_type][primary_discriminator] = (*secondary_discriminators,)
        else:
            # With only a primary discriminator value, the registered class should resolve to it directly,
            # so there should not already by an entry present:
            assert primary_discriminator not in self._registry[discriminator_type], \
                   'Already a {} class registered for discriminatory type {}'.format(discriminator_type, primary_discriminator)
            self._registry[discriminator_type][primary_discriminator] = cls

    def get(self, primary_discriminator, *secondary_discriminators, discriminator_type=DiscriminatorType.single):
        """
        Return the class registration for the given discriminatory values, if it exists.
        """
        if primary_discriminator in self._registry[discriminator_type]:
            if isinstance(self._registry[discriminator_type][primary_discriminator], dict):
                if not secondary_discriminators and primary_discriminator in self._exclusive[discriminator_type]:
                    return list(self._registry[discriminator_type][primary_discriminator].values())[0]
                return self._registry[discriminator_type][primary_discriminator].get((*secondary_discriminators,))
            return self._registry[discriminator_type][primary_discriminator]

    def has(self, primary_discriminator, *secondary_discriminators, discriminator_type=DiscriminatorType.single):
        """
        Return True if a class registration exists for the given discriminatory values.
        """
        assert discriminator_type in self.DiscriminatorType
        return self.get(primary_discriminator, *secondary_discriminators, discriminator_type=discriminator_type) is not None

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

    Entity args
    -----------
    This metaclass also provides entity classes with a means to configure options or register traits, which can be used to facilitate various use cases involving the entity.
    These options can be passed through via the __entity_args__ class attribute,
    that supports arguments that reference locally mapped columns directly from within the class declaration (as seen in the examples below).
    Currently, the following entity args are supported:

    * 'discriminator'
       The discriminator definition registers the column or properties by which instances of the entity class can be categorized,
       on a more broader basis than the primary key identity or polymorphism.
       This discriminator definition can be a single discriminator property, or a combination of multiple.
       The primary discriminator should always be an Enumeration type column, which defines the types that are allowed as values for the discriminator column.
       The enumeration's types and/or type_groups are extracted from its definition and set as class attributes on the entity class.
       Secondary discriminators should always be relationship properties to a related Entity class.

       :example:
       | class SomeClass(Entity):
       |     __tablename__ = 'some_tablename'
       |     ...
       |     described_by = Column(IntEnum(some_class_types), ...)
       |     ...
       |     __entity_args__ = {
       |         'discriminator': described_by,
       |     }
       |     ...
       |
       | SomeClass.__types__ == some_class_types
       |
       | class OtherClass(Entity):
       |     ...
       |     described_by = Column(IntEnum(other_class_types))
       |     related_id = schema.Column(sqlalchemy.types.Integer(), schema.ForeignKey(SomeClass.id))
       |     related_entity = orm.relationship(SomeClass)
       |     ...
       |     __entity_args__ = {
       |         'discriminator': (described_by, related_entity),
       |     }
       |     ...
       |
       | OtherClass.__types__ == other_class_types

       This metaclass will also provide entity classes with the `get_cls_discriminator` method, which returns the registered discriminator definition,
       and the `get_discriminator_value` & `set_discriminator_value` method to retrieve or set the discriminator value on a provided entity instance.
       In unison with the discriminator argument, the metaclass also imparts entity classes with the ability to register and later retrieve classes for concrete discriminator values.
       These registered classes are stored in the __discriminator_cls_registry__ class argument and registered classes can be retrieved for a specific discriminator value with the 'get_cls_by_discriminator' method.
       See its documentation for more details.

       All this discriminator and types' functionality can be used by processes higher-up to quicken the creation and insertion process of entity instances, e.g. facades, pull-down add actions, etc..
       NOTE: this class registration system could possibly be moved to the level of the facade in the future, to not be limited to a single hierarchy for each entity class.

    * 'ranked_by'
       This entity argument allows registering a rank-based entity class its ranking definition.
       Like the discriminator argument, it supports the registration of a single column, both directly from or after the class declaration,
       which should be an Integer type column that holds the numeric rank value.
       The registered rank definition can be retrieved on an entity class post-declaration using the provided `get_ranked_by` method.
       See its documentation for more details.

       :example:
       | class SomeClass(Entity):
       |     __tablename__ = 'some_tablename'
       |     ...
       |     rank = Column(Integer())
       |     ...
       |     __entity_args__ = {
       |         'ranked_by': rank,
       |     }
       |     ...
       |
       | SomeClass.get_ranked_by() == (SomeClass.rank,)

       Because the ranking dimension of an entity may be more complex than a single ranking column, e.g. for financial roles the ranking dimension is seperated for each role type. 
       Therefor, the registration also supports a tuple of columns, whereby the first item should be the column that holds the rank value,
       while the remaining columns act as discriminator of the ranking dimension.
       This may well include, but not limited to, the discriminator column.

       :example:
       | class SomeClass(Entity):
       |     __tablename__ = 'some_tablename'
       |     ...
       |     described_by = Column(IntEnum(some_class_types), ...)
       |     rank = Column(Integer())
       |     ...
       |     __entity_args__ = {
       |         'ranked_by': (rank, described_by),
       |     }
       |     ...
       |
       | SomeClass.get_ranked_by() == (SomeClass.rank, SomeClass.described_by)

    * 'application_date'
       Registers the application date attribute of the target entity.
       Like the discriminator argument, it supports the registration of a single column, both directly from or after the class declaration,
       which should be of type Date.

    * 'transition_types'
       Enumeration that defines the types of state transitions instances of the entity class can undergo.

    * 'editable'
       This entity argument is a flag that when set to False will register the entity class as globally non-editable.

    * 'editable_fields'
       List of field_names that should be excluded from the globally non-editable registration, if present.

    * 'retention_level'
       Configures the data retention of the entity, e.g. how long it should be kept in the system before its final archiving or removal.

    * 'retention_cut_off_date'
       Registers a date attribute of the target entity, which value signals the point at which the entity's retention period begins.
       This argument is an optional parameter in the retention policy configuration of entities.

    Notes on metaclasses
    --------------------
    Metaclasses are not part of objects' class hierarchy whereas base classes are.
    So when a method is called on an object it will not look on the metaclass for this method, however the metaclass may have created it during the class' or object's creation.
    They are generally used for use cases outside of the default rules of object-oriented programming.
    In this case for example, the metaclass provides subclasses the means to register themselves on on of its base classes,
    which is an OOP anti-pattern as classes should not know about their subclasses.
    """

    # Supported retention levels; is explicitly set in vFinance.__init__.
    retention_levels = util.OrderedProperties()

    # new is called to create a new Entity class
    def __new__( cls, classname, bases, dict_ ):
        #
        # don't modify the Entity class itself
        #
        if classname != 'Entity':
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
            
            dict_.setdefault('__entity_args__', dict())
            
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
                if hasattr(base, '__discriminator_cls_registry__'):
                    break
            else:
                dict_.setdefault('__discriminator_cls_registry__', EntityClsRegistry())
        
            entity_args = dict_.get('__entity_args__')
            if entity_args is not None:
                discriminator = entity_args.get('discriminator')
                if discriminator is not None:
                    (primary_discriminator, *secondary_discriminators) = discriminator if isinstance(discriminator, tuple) else (discriminator,)
                    assert isinstance(primary_discriminator, (sql.schema.Column, orm.attributes.InstrumentedAttribute)),\
                           'Primary discriminator must be a single instance of `sql.schema.Column` or an `orm.attributes.InstrumentedAttribute`'
                    discriminator_col = primary_discriminator
                    if isinstance(primary_discriminator, orm.attributes.InstrumentedAttribute):
                        discriminator_col = primary_discriminator.prop.columns[0]
                    assert isinstance(discriminator_col.type, Enumeration), 'Discriminator column must be of type Enumeration'
                    assert isinstance(discriminator_col.type.enum, util.OrderedProperties), 'Discriminator column has no enumeration types defined'
                    dict_['__types__'] = discriminator_col.type.enum
                    if hasattr(discriminator_col.type.enum, 'get_groups'):
                        dict_['__type_groups__'] = discriminator_col.type.enum.get_groups()
                    dict_['__discriminator_cls_registry__'] = EntityClsRegistry()
                    assert len(secondary_discriminators) <= 1, 'Only a single secondary discriminator is currently supported'
                    for secondary_discriminator in secondary_discriminators:
                        assert isinstance(secondary_discriminator, orm.properties.RelationshipProperty), 'Secondary discriminators must be instances of `orm.properties.RelationshipProperty`'

                ranked_by = entity_args.get('ranked_by')
                if ranked_by is not None:
                    ranked_by = ranked_by if isinstance(ranked_by, tuple) else (ranked_by,)
                    for col in ranked_by:
                        assert isinstance(col, (sql.schema.Column, orm.attributes.InstrumentedAttribute)), 'Ranked by definition must be a single instance of `sql.schema.Column` or an `orm.attributes.InstrumentedAttribute` or a tuple of those instances'
                    rank_col = ranked_by[0]
                    if isinstance(rank_col, orm.attributes.InstrumentedAttribute):
                        rank_col = rank_col.prop.columns[0]
                    assert isinstance(rank_col.type, Integer), 'The first column/attributes of the ranked by definition, indicating the rank column, should be of type Integer'

                order_search_by = entity_args.get('order_search_by')
                if order_search_by is not None:
                    order_search_by = order_search_by if isinstance(order_search_by, tuple) else (order_search_by,)
                    assert len(order_search_by) <= 2, 'Can not define more than 2 search order by clauses.'

                application_date = entity_args.get('application_date')
                if application_date is not None:
                    assert isinstance(application_date, (sql.schema.Column, orm.attributes.InstrumentedAttribute)), 'Application date definition must be a single instance of `sql.schema.Column` or an `orm.attributes.InstrumentedAttribute`'
                    application_date_col = application_date.prop.columns[0] if isinstance(application_date, orm.attributes.InstrumentedAttribute) else application_date
                    assert isinstance(application_date_col.type, Date), 'The application date should be of type Date'

                transition_types = entity_args.get('transition_types')
                if transition_types is not None:
                    assert isinstance(transition_types, util.OrderedProperties), 'Transition types argument should define enumeration types'

                retention_level = entity_args.get('retention_level')
                if retention_level is not None:
                    assert retention_level in cls.retention_levels.values(), 'Unsupported retention level'

                retention_cut_off_date = entity_args.get('retention_cut_off_date')
                if retention_cut_off_date is not None:
                    assert isinstance(retention_cut_off_date, (sql.schema.Column, orm.attributes.InstrumentedAttribute)), 'Retention cut-off date definition must be a single instance of `sql.schema.Column` or an `orm.attributes.InstrumentedAttribute`'
                    retention_cut_off_date_col = retention_cut_off_date.prop.columns[0] if isinstance(retention_cut_off_date, orm.attributes.InstrumentedAttribute) else retention_cut_off_date
                    assert isinstance(retention_cut_off_date_col.type, Date), 'The retention cut-off date should be of type Date'

        _class = super( EntityMeta, cls ).__new__( cls, classname, bases, dict_ )
        # adds primary key column to the class
        if classname != 'Entity' and dict_.get('__tablename__') is not None:
            for val in dict_.values():
                if isinstance(val, schema.Column) and val.primary_key: # val.primary_key checks if the primary_key attribute of the Column is set to True
                    break
            else:
                # table.primary_key.issubset([]) tests if there are no primary keys(aka tests if empty)
                # table.primary_key returns an iterator so we can't test the length or something like that
                table = dict_.get('__table__', None)
                if table is None or table.primary_key is None:
                    _class.id = schema.Column(PrimaryKey(), **options.DEFAULT_AUTO_PRIMARYKEY_KWARGS)

            # Auto-assign entity_args and name entity argument if not configured explicitly.
            entity_args = dict_.get('__entity_args__')
            if entity_args is None:
                dict_['__entity_args__'] = entity_args = {}
            entity_name = dict_['__entity_args__'].get('name')
            if entity_name is None:
                dict_['__entity_args__']['name'] = entity_name = cls._default_entity_name(cls, classname, dict_)
            assert isinstance(entity_name, str) and len(entity_name) > 0, 'Name argument in __entity_args__ should be text-based and contain at least 1 character'

            # Bind an EntityNamingContext to the initial naming context for the entity class
            # using the entity's name configured (or auto-assigned) in the __entity_args__
            initial_naming_context.bind_context(('entity', entity_name), EntityNamingContext(_class))

        return _class

    def _default_entity_name(cls, classname, dict_):
        # The default format will split the classname by capital letters, and join the lowered result by underscore.
        # e.g. classname 'ThisIsATestClass' will result in the entity name 'this_is_a_test_class'
        return '_'.join(re.findall('.[^A-Z]*', classname)).lower()

    def get_polymorphic_types(cls):
        """
        In case of a polymorphic base class with a polymorphic discriminator column
        that is of type Enumeration, return its contained type enumeration.
        """
        polymorphic_on = cls.__mapper_args__.get('polymorphic_on')
        if polymorphic_on is not None:
            polymorphic_on_col = polymorphic_on
            if isinstance(polymorphic_on, orm.attributes.InstrumentedAttribute):
                polymorphic_on_col = polymorphic_on.prop.columns[0]
            if isinstance(polymorphic_on_col.type, Enumeration):
                return polymorphic_on_col.type.enum

    def get_cls_by_discriminator(cls, primary_discriminator, *secondary_discriminators):
        """
        Retrieve the corresponding class for the given discriminator value if one is registered on this class or its base.
        This can be the class that is specifically registered for the given discriminator value, or a possible registered default class otherwise.
        Providing no value will also return the default registered class if present.
        Additionally, in case of a polymorphic base class, passing one of the polymorphic identities will also retrieve
        the entity corresponding to the identity based on the polymorphic map.

        :param primary_discriminator: can be one of either following values:
          * None: will lookup a possible registered default class
          * a member of a sqlalchemy.util.OrderedProperties instance.
            If this class or its base have types registration enabled, this should be a member of the set __types__ or a member of the
            __type_groups__, that get auto-set in case the set types are grouped.
        :param secondary_discriminators: optional secondary Entity class or instance discriminator values.
        :return: the class that is registered for the given discriminator values, which inherits from the class where the discriminators are registered on, or the class itself if not.
                 In case the primary discriminator value is:
                   * None; the registered default class will be returned, if present.
                   * a member of the allowed __type_groups__; a possible registered class for the type group will be returned, or the registered default class otherwise.
                   * a member of the allowed __types__; a possible registered class for the type will be returned,
                     otherwise a possible registered class for the group of the type, if applicable, and otherwise the registered default class.
                 In the latter two cases, the secondary discriminators may discriminate between multi-level discriminated registered classes.
                 Examples:
                  | BaseClass.get_cls_by_discriminator(allowed_types.certain_type.name) == CertainTypeClass
                  | BaseClass.get_cls_by_discriminator(allowed_type_groups.certain_registered_type_group.name) == RegisteredClassForGroup
                  | BaseClass.get_cls_by_discriminator(allowed_types.certain_unregistered_type.name) == RegisteredDefaultClass
                  | BaseClass.get_cls_by_discriminator(allowed_types.certain_type.name, Organization) == CertainTypeClassWithOrganization
                  | BaseClass.get_cls_by_discriminator(allowed_types.certain_type.name, Person) == CertainTypeClassWithPerson
        :raises : an AttributeException when the given argument is not a valid type
        """
        if 'polymorphic_on' in cls.__mapper_args__ and primary_discriminator in cls.__mapper__.polymorphic_map:
            return cls.__mapper__.polymorphic_map[primary_discriminator].entity
        if cls.__types__ is not None:
            if primary_discriminator in cls.__types__:
                # Support passing secondary discriminator arguments both on the instance as the class level.
                secondary_discriminators = [
                    secondary_discriminator.__class__ if not isinstance(secondary_discriminator, EntityMeta) \
                    else secondary_discriminator for secondary_discriminator in secondary_discriminators]

                # First check if a class is registered under a single-type discriminatory value.
                if (registered_class := cls.__discriminator_cls_registry__.get(primary_discriminator, *secondary_discriminators)) is not None:
                    return registered_class

                # If no single-type registration exists, try with its type group (if applicable).
                if cls.__type_groups__ is not None and \
                   (type_group := cls.__types__[primary_discriminator].grouped_by) is not None and \
                   (registered_class := cls.__discriminator_cls_registry__.get(
                       type_group.name, *secondary_discriminators, discriminator_type=EntityClsRegistry.DiscriminatorType.group)) is not None:
                    return registered_class

            # If no other more concrete class registration is found, return a default class registration if it exists.
            if (registered_class := cls.__discriminator_cls_registry__.get(None)) is not None:
                return registered_class

    def _get_entity_arg(cls, key):
        for cls_ in (cls,) + cls.__mro__:
            if hasattr(cls_, '__entity_args__') and key in cls_.__entity_args__:
                return cls_.__entity_args__[key]
    
    def get_cls_discriminator(cls):
        """
        Retrieve this entity class discriminator definition.
        """
        discriminator = cls._get_entity_arg('discriminator')
        if discriminator is not None:
            discriminator = discriminator if isinstance(discriminator, tuple) else (discriminator,)
            discriminator_cols = [
                getattr(cls, discriminator_col.key) \
                if isinstance(discriminator_col, (sql.schema.Column, orm.properties.RelationshipProperty)) \
                else discriminator_col for discriminator_col in discriminator
            ]
            return tuple(discriminator_cols)

    def get_discriminator_value(cls, entity_instance):
        """Return the given entity instance's discriminator value."""
        assert isinstance(entity_instance, cls)
        discriminator = cls.get_cls_discriminator()
        if discriminator is not None:
            return tuple([discriminator_prop.__get__(entity_instance, None) for discriminator_prop in discriminator])

    def set_discriminator_value(cls, entity_instance, primary_discriminator_value, *secondary_discriminator_values):
        """Set the given entity instance's discriminator with the provided discriminator value."""
        assert isinstance(entity_instance, cls)
        discriminator = cls.get_cls_discriminator()
        if discriminator is not None:
            (primary_discriminator, *secondary_discriminators) = discriminator
            if primary_discriminator_value is not None:
                assert primary_discriminator_value in cls.__types__.__members__, '{} is not a valid discriminator value for this entity.'.format(primary_discriminator_value)
                primary_discriminator.__set__(entity_instance, primary_discriminator_value)
                for secondary_discriminator_prop, secondary_discriminator_value in zip(secondary_discriminators, secondary_discriminator_values):
                    entity = secondary_discriminator_prop.prop.entity.entity
                    assert isinstance(secondary_discriminator_value, entity), '{} is not a valid secondary discriminator value for this entity. Must be of type {}'.format(secondary_discriminator_value, entity)
                    secondary_discriminator_prop.__set__(entity_instance, secondary_discriminator_value)

    def get_secondary_discriminator_types(cls):
        if cls.get_cls_discriminator() is not None:
            (_, *secondary_discriminators) = cls.get_cls_discriminator()
            return [secondary_discriminator.prop.entity.entity for secondary_discriminator in secondary_discriminators]
        return []

    def get_ranked_by(cls):
        ranked_by = cls._get_entity_arg('ranked_by')
        if ranked_by is not None:
            ranked_by = ranked_by if isinstance(ranked_by, tuple) else (ranked_by,)
            rank_cols = [getattr(cls, rank_col.key) if isinstance(rank_col, sql.schema.Column) else rank_col for rank_col in ranked_by]
            return tuple(rank_cols)

    def get_order_search_by(cls):
        order_search_by = cls._get_entity_arg('order_search_by')
        if order_search_by is not None:
            order_search_by = order_search_by if isinstance(order_search_by, tuple) else (order_search_by,)
            order_by_clauses = []
            for order_by in order_search_by:
                if isinstance(order_by, sql.schema.Column):
                    order_by_clauses.append(getattr(cls, order_by.key))
                elif isinstance(order_by, hybrid.hybrid_property):
                    order_by_clauses.append(getattr(cls, order_by.fget.__name__))
                else:
                    order_by_clauses.append(order_by)
            return tuple(order_by_clauses)

    @property
    def transition_types(cls):
        return cls._get_entity_arg('transition_types')

    @property
    def retention_level(cls):
        return cls._get_entity_arg('retention_level')

    @property
    def retention_cut_off_date(cls):
        retention_cut_off_date = cls._get_entity_arg('retention_cut_off_date')
        if retention_cut_off_date is not None:
            mapper = orm.class_mapper(cls)
            return mapper.get_property(retention_cut_off_date.key).class_attribute

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

    def is_applicable_at(self, at):
        """
        Return whether this entity instance is applicable at the given date.
        This method requires the entity class to have its application date range
        configured by the 'application_date' __entity_args__ argument.
        An instance is applicable at the given date when it is later than the instance's
        application date, and the application date is not later than end_of_times.

        :raises: An AssertionError when the application_date is not configured in the entity's __entity_args__.
        """
        from camelot.model.authentication import end_of_times
        entity = type(self)
        assert entity._get_entity_arg('application_date') is not None
        assert isinstance(at, datetime.date)
        mapper = orm.class_mapper(entity)
        application_date_prop = mapper.get_property(entity._get_entity_arg('application_date').key)
        application_date = application_date_prop.class_attribute.__get__(self, None)
        return application_date is not None and not (application_date >= end_of_times() or at < application_date)
