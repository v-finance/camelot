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

"""This module complements the sqlalchemy orm module, it contains the global
`Session` factory to create `session` objects.  Whenever a `session`
is needed it can be constructed with a call of `Session` ::
    
    session = Session
        
when using Elixir, Elixir needs to be told to use this session factory ::
    
    elixir.session = Session

when using Declarative, this module contains an `Entity` class that can
be used as a `declarative_base` and has some classes that mimic Elixir
behavior
"""

import logging
import sys

LOGGER = logging.getLogger('camelot.core.orm')

import sqlalchemy.types
from camelot.core.sql import metadata
from sqlalchemy import schema, orm, ForeignKey, types, event
from sqlalchemy.ext.declarative import ( declarative_base, 
                                         _declarative_constructor,
                                         DeclarativeMeta )
from sqlalchemy.orm import ( scoped_session, sessionmaker, deferred, 
                             column_property, mapper, relationship )

# format constants
FKCOL_NAMEFORMAT = "%(relname)s_%(key)s"
CONSTRAINT_NAMEFORMAT = "%(tablename)s_%(colnames)s_fk"
MULTIINHERITANCECOL_NAMEFORMAT = "%(entity)s_%(key)s"

# other global constants
DEFAULT_AUTO_PRIMARYKEY_NAME = "id"
DEFAULT_AUTO_PRIMARYKEY_TYPE = types.Integer
DEFAULT_POLYMORPHIC_COL_NAME = "row_type"
POLYMORPHIC_COL_SIZE = 40
POLYMORPHIC_COL_TYPE = types.String( POLYMORPHIC_COL_SIZE )

MUTATORS = '__mutators__'


#
# Singleton session factory, to be used when a session is needed
#
Session = scoped_session( sessionmaker( autoflush = False,
                                        autocommit = True,
                                        expire_on_commit = False ) )

#
# Singleton registry for subclasses of entity that have been mapped
#

class_registry = dict()

#
# There are 3 base classes that each act in a different way
#
# * ClassMutator : DSL like statements that modify the Entity at definition
#   time
# * Property : modify an Entity at construction time
# * DeferredProperty : modify an Entity after the mapping has been configured
#

class ClassMutator( object ):
    """Class to create DSL statements such as `using_options`.  This is used
    to transform Elixir like DSL statements in Declarative class attributes.
    The use of these statements is discouraged in any new code, and exists for
    compatibility with Elixir model definitions"""
    
    def __init__( self, *args, **kwargs ):
        # jam this mutator into the class's mutator list
        class_locals = sys._getframe(1).f_locals
        mutators = class_locals.setdefault(MUTATORS, [])
        mutators.append( (self, args, kwargs) )
        
    def process( self, entity_dict, *args, **kwargs ):
        """
        Process one mutator.  This methed should be overwritten in a subclass
        """
        pass

class Property( object ):
    """
    Abstract base class for all properties of an Entity that are not handled
    by Declarative but should be handled by EntityMeta before a new Entity
    subclass is constructed
    """
    pass

class DeferredProperty( object ):
    """    Abstract base class for all properties of an Entity that are not 
    handled by Declarative but should be handled after a mapper was
    configured"""

    def _setup_reverse( self, key, rel, target_cls ):
        """Setup bidirectional behavior between two relationships."""

        reverse = self.kw.get( 'reverse' )
        if reverse:
            reverse_attr = getattr( target_cls, reverse )
            if not isinstance( reverse_attr, DeferredProperty ):
                reverse_attr.property._add_reverse_property( key )
                rel._add_reverse_property( reverse )

@event.listens_for( mapper, 'after_configured' )
def _process_deferred_properties():
    """After all mappers have been configured, process the Deferred Propoperties
    """
    LOGGER.debug( 'process deferred properties' )
    deferred_properties = []
    for cls in class_registry.values():
        mapper = orm.class_mapper( cls )
        # set some convenience attributes to the Entity
        setattr( cls, 'table', mapper.local_table )
        setattr( cls, 'query', Session().query( cls ) )
        # loop over the properties to process the defered properties
        for key, value in cls.__dict__.items():
            if isinstance( value, DeferredProperty ):
                deferred_properties.append( ( value.process_order, key, value, cls, mapper ) )
    deferred_properties.sort( key = lambda dp:dp[0] )
    for _order, key, value, cls, mapper in deferred_properties:
        try:
            value._config( cls, mapper, key )
        except Exception, e:
            LOGGER.fatal( 'Could not process DeferredProperty %s of class %s'%( key, cls.__name__ ),
                          exc_info = e )
            raise

class Field( schema.Column, Property ):
    """Subclass of :class:`sqlalchemy.schema.Column` with behavior compatible
    with :class:`elixir.Field` and only exists for porting Elixir code to 
    Declarative.  It's use in new code is discouraged.
    """
    
    def __init__( self, type, *args, **kwargs ):
        self.colname = kwargs.pop( 'colname', None )
        self.deferred = kwargs.pop( 'deferred', False )
        if 'required' in kwargs:
            kwargs['nullable'] = not kwargs.pop( 'required' )
        super( Field, self ).__init__( type, *args, **kwargs )

    def attach( self, dict_, name ):
        if self.deferred:
            dict_[ name ] = deferred( self )
        dict_[ name ] = self

class Relationship( DeferredProperty ):
    """Generates a one to many or many to one relationship."""

    process_order = 0
    
    def __init__(self, target, **kw):
        self.target = target
        self.kw = kw

    def _config(self, cls, mapper, key):
        """Create a Column with ForeignKey as well as a relationship()."""

        if isinstance( self.target, basestring ):
            target_cls = cls._decl_class_registry[self.target]
        else:
            target_cls = self.target

        pk_target, fk_target = self._get_pk_fk(cls, target_cls)
        pk_table = pk_target.__table__
        pk_col = list(pk_table.primary_key)[0]
        
        fk_colname = '%s_%s'%(key, pk_col.key)
        
        if hasattr(fk_target, fk_colname):
            fk_col = getattr(fk_target, fk_colname)
        else:
            fk_col = schema.Column(fk_colname, pk_col.type, ForeignKey(pk_col))
            setattr(fk_target, fk_colname, fk_col)

        rel = relationship(target_cls,
                primaryjoin=fk_col==pk_col,
                collection_class=self.kw.get('collection_class', set)
            )
        setattr(cls, key, rel)
        self._setup_reverse(key, rel, target_cls)

class OneToMany( Relationship ):
    """Generates a one to many relationship."""

    process_order = 2
    
    def _get_pk_fk( self, cls, target_cls ):
        return cls, target_cls

class ManyToOne( Relationship ):
    """Generates a many to one relationship."""

    process_order = 1
    
    def _get_pk_fk( self, cls, target_cls ):
        return target_cls, cls

class ManyToMany( DeferredProperty ):
    """Generates a many to many relationship."""

    process_order = 3
    
    def __init__( self, target, tablename, local_colname, remote_colname, **kw ):
        self.target = target
        self.tablename = tablename
        self.local = local_colname
        self.remote = remote_colname
        self.kw = kw

    def _config(self, cls, mapper, key):
        """Create an association table between parent/target
        as well as a relationship()."""

        target_cls = cls._decl_class_registry[self.target]
        local_pk = list(cls.__table__.primary_key)[0]
        target_pk = list(target_cls.__table__.primary_key)[0]
        t = schema.Table(
                self.tablename,
                cls.metadata,
                schema.Column(self.local, ForeignKey(local_pk), primary_key=True),
                schema.Column(self.remote, ForeignKey(target_pk), primary_key=True),
                keep_existing=True
            )
        rel = relationship(target_cls,
                secondary=t,
                # use list instead of set because collection proxy does not
                # work with sets
                collection_class=self.kw.get('collection_class', list)
            )
        setattr(cls, key, rel)
        self._setup_reverse(key, rel, target_cls)
                    
class ColumnProperty( DeferredProperty ):

    process_order = 4
    
    def __init__( self, prop, *args, **kwargs ):
        super( ColumnProperty, self ).__init__()
        self.prop = prop
        self.args = args
        self.kwargs = kwargs
        
    def _config(self, cls, mapper, key):
        setattr( cls, key, column_property( self.prop( mapper.local_table.c ).label(None), 
                                            *self.args, 
                                            **self.kwargs ) )

def setup_all( create_tables=False, *args, **kwargs ):
    """Create all tables that are registered in the metadata
    """
    if create_tables:
        metadata.create_all( *args, **kwargs )
        
class using_options( ClassMutator ):
    
    def process( self, entity_dict, tablename = None, order_by = None ):
        if tablename:
            entity_dict['__tablename__'] = tablename
        if order_by:
            mapper_args = entity_dict.get('__mapper_args__', {} )
            mapper_args['order_by'] = order_by

class EntityMeta( DeclarativeMeta ):
    """Subclass of :class:`sqlalchmey.ext.declarative.DeclarativeMeta`.  This
    metaclass processes the Property and ClassMutator objects.
    """
    
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
            if '__tablename__' not in dict_:
                dict_['__tablename__'] = classname.lower()     
            #
            # handle the Properties
            #
            has_primary_key = False
            for key, value in dict_.items():
                if isinstance( value, schema.Column ):
                    if value.primary_key:
                        has_primary_key = True
                if isinstance( value, Property ):
                    value.attach( dict_, key )
            if has_primary_key == False:
                #
                # add a primary key
                #
                primary_key_column = schema.Column( DEFAULT_AUTO_PRIMARYKEY_TYPE,
                                                    primary_key = True )
                dict_[ DEFAULT_AUTO_PRIMARYKEY_NAME ] = primary_key_column            
        return super( EntityMeta, cls ).__new__( cls, classname, bases, dict_ )
    
    # init is called after the creation of the new Entity class, and can be
    # used to initialize it
    def __init__( cls, classname, bases, dict_ ):
        super( EntityMeta, cls ).__init__( classname, bases, dict_ )
        if '__table__' in cls.__dict__:
            setattr( cls, 'table', cls.__dict__['__table__'] )
        
class Entity( object ):
    """A declarative base class that adds some methods that used to be
    available in Elixir"""
    
    def __init__( self, *args, **kwargs ): 
        _declarative_constructor( self, *args, **kwargs ) 
        Session().add( self ) 
                        
    #
    # methods below were copied from Elixir to mimic the Elixir Entity
    # behavior
    #
    def from_dict(self, data):
        """
        Update a mapped class with data from a JSON-style nested dict/list
        structure.
        """
        # surrogate can be guessed from autoincrement/sequence but I guess
        # that's not 100% reliable, so we'll need an override

        mapper = sqlalchemy.orm.object_mapper(self)

        for key, value in data.iteritems():
            if isinstance(value, dict):
                dbvalue = getattr(self, key)
                rel_class = mapper.get_property(key).mapper.class_
                pk_props = rel_class._descriptor.primary_key_properties

                # If the data doesn't contain any pk, and the relationship
                # already has a value, update that record.
                if not [1 for p in pk_props if p.key in data] and \
                   dbvalue is not None:
                    dbvalue.from_dict(value)
                else:
                    record = rel_class.update_or_create(value)
                    setattr(self, key, record)
            elif isinstance(value, list) and \
                 value and isinstance(value[0], dict):

                rel_class = mapper.get_property(key).mapper.class_
                new_attr_value = []
                for row in value:
                    if not isinstance(row, dict):
                        raise Exception(
                                'Cannot send mixed (dict/non dict) data '
                                'to list relationships in from_dict data.')
                    record = rel_class.update_or_create(row)
                    new_attr_value.append(record)
                setattr(self, key, new_attr_value)
            else:
                setattr(self, key, value)

    def to_dict(self, deep={}, exclude=[]):
        """Generate a JSON-style nested dict/list structure from an object."""
        col_prop_names = [p.key for p in self.mapper.iterate_properties \
                                      if isinstance(p, orm.properties.ColumnProperty)]
        data = dict([(name, getattr(self, name))
                     for name in col_prop_names if name not in exclude])
        for rname, rdeep in deep.iteritems():
            dbdata = getattr(self, rname)
            #FIXME: use attribute names (ie coltoprop) instead of column names
            fks = self.mapper.get_property(rname).remote_side
            exclude = [c.name for c in fks]
            if dbdata is None:
                data[rname] = None
            elif isinstance(dbdata, list):
                data[rname] = [o.to_dict(rdeep, exclude) for o in dbdata]
            else:
                data[rname] = dbdata.to_dict(rdeep, exclude)
        return data

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
    
    @classmethod
    def get_by(cls, *args, **kwargs):
        """
        Returns the first instance of this class matching the given criteria.
        This is equivalent to:
        session.query(MyClass).filter_by(...).first()
        """
        return cls.query.filter_by(*args, **kwargs).first()

    @classmethod
    def get(cls, *args, **kwargs):
        """
        Return the instance of this class based on the given identifier,
        or None if not found. This is equivalent to:
        session.query(MyClass).get(...)
        """
        return cls.query.get(*args, **kwargs)

Entity = declarative_base( cls = Entity, 
                           metadata = metadata,
                           metaclass = EntityMeta,
                           class_registry = class_registry,
                           constructor = None,
                           name = 'Entity' )
