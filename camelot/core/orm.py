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

logger = logging.getLogger('camelot.core.orm')

import sqlalchemy.types
from camelot.core.sql import metadata
from sqlalchemy import schema, orm, ForeignKey, types
from sqlalchemy.ext.declarative import ( declared_attr, declarative_base, 
                                         DeclarativeMeta )
from sqlalchemy.orm import scoped_session, sessionmaker

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

class Field( schema.Column ):
    """Subclass of :class:`sqlalchemy.schema.Column`
    """
    
    def __init__( self, type, *args, **kwargs ):
        if 'required' in kwargs:
            kwargs['nullable'] = not kwargs.pop( 'required' )
        super( Field, self ).__init__( type, *args, **kwargs )
        
class Property( object ):
    """
    Abstract base class for all properties of an Entity that are not handled
    by Declarative but should be handled by EntityMeta
    """
    pass
    
class ManyToOne( Property ):
    """An Entity property that creates a :class:`sqlalchemy.orm.relationship`
    and a :class:`sqlalchemy.schema.Column` property.
    """
    
    def __init__( self, argument=None, secondary = None, **kwargs ):
        self.argument = argument
        self.secondary = secondary
        self.kwargs = kwargs
        target_table_name = argument.lower()
        self.column = Field( sqlalchemy.types.Integer(),
                             ForeignKey( '%s.id'%target_table_name ) )
        
    def attach( self, dict_, name ):
        dict_[ name + '_id' ] = self.column
        dict_[ name ] = orm.relationship( self.argument )
        
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
    
    def __new__( cls, classname, bases, dict_ ):
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
        # add a primary key
        #
        primary_key_column = schema.Column( DEFAULT_AUTO_PRIMARYKEY_TYPE,
                                            primary_key = True )
        dict_[ DEFAULT_AUTO_PRIMARYKEY_NAME ] = primary_key_column
        #
        # handle the Properties
        #
        for key, value in dict_.items():
            if isinstance( value, Property ):
                value.attach( dict_, key )
        return super( EntityMeta, cls ).__new__( cls, classname, bases, dict_ )
        
class Entity( object ):
    """A declarative base class that adds some methods that used to be
    available in Elixir"""
    
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
                                      if isinstance(p, ColumnProperty)]
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
        return object_session(self).flush([self], *args, **kwargs)

    def delete(self, *args, **kwargs):
        return object_session(self).delete(self, *args, **kwargs)

    def expire(self, *args, **kwargs):
        return object_session(self).expire(self, *args, **kwargs)

    def refresh(self, *args, **kwargs):
        return object_session(self).refresh(self, *args, **kwargs)

    def expunge(self, *args, **kwargs):
        return object_session(self).expunge(self, *args, **kwargs)
    
    # query methods
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
                           metaclass = EntityMeta )

def refresh_session( session ):
    """Session refresh expires all objects in the current session and sends
    a local entity update signal via the remote_signals mechanism

    this method ought to be called in the model thread.
    """
    from camelot.view.remote_signals import get_signal_handler
    import sqlalchemy.exc as sa_exc
    logger.debug('session refresh requested')
    signal_handler = get_signal_handler()
    refreshed_objects = []
    expunged_objects = []
    for _key, obj in session.identity_map.items():
        try:
            session.refresh( obj )
            refreshed_objects.append( obj )
        except sa_exc.InvalidRequestError:
            #
            # this object could not be refreshed, it was probably deleted
            # outside the scope of this session, so assume it is deleted
            # from the application its point of view
            #
            session.expunge( obj )
            expunged_objects.append( obj )
    for obj in refreshed_objects:
        signal_handler.sendEntityUpdate( None, obj )
    for obj in expunged_objects:
        signal_handler.sendEntityDelete( None, obj )
    return refreshed_objects
