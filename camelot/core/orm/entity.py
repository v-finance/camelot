"""
This module provides the :class:`camelot.core.orm.entity.EntityBase` declarative base class, 
as well as its metaclass :class:`camelot.core.orm.entity.EntityMeta`.  Those are the building
blocks for creating the :class:`camelot.core.orm.Entity`.

These classes can be reused if a custom base class is needed.
"""

import sys

from sqlalchemy import orm, schema, sql
from sqlalchemy.ext.declarative import ( _declarative_constructor,
                                         DeclarativeMeta )
from sqlalchemy.ext import hybrid

from . fields import Field
from . statements import MUTATORS
from . properties import EntityBuilder, Property
from . import options, options_defaults, Session

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
        for key, value in options_defaults.items():
            if isinstance( value, dict ):
                value = value.copy()
            setattr( self, key, value )        
        
    def set_entity( self, entity ):
        self.entity = entity
        self.module = sys.modules.get( entity.__module__ )
        self.tablename = entity.__tablename__
        #
        # verify if a primary key was set manually
        #
        for key, value in entity.__dict__.items():
            if isinstance( value, schema.Column ):
                if value.primary_key:
                    self.has_pk = True
            if isinstance( value, EntityBuilder ):
                self.builders.append( value )
            if isinstance( value, Property ):
                value.entity = entity
                value.name = key
        # execute the builders in the order they were created
        self.builders.sort( key = lambda b:b.counter )
        
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
        if self._pk_col_done:
            return

        self.call_builders( 'create_pk_cols' )

        if not self.has_pk:
            colname = options.DEFAULT_AUTO_PRIMARYKEY_NAME

            self.add_column(
                colname,
                schema.Column( colname, options.DEFAULT_AUTO_PRIMARYKEY_TYPE,
                               primary_key = True ) )
        self._pk_col_done = True
        
    def create_properties(self):
        self.call_builders( 'create_properties' )        

    def create_tables(self):
        self.call_builders( 'create_tables' )
	
    def finalize(self):
        self.call_builders( 'finalize' )
	if self.order_by:
	    mapper = orm.class_mapper( self.entity )
	    mapper.order_by = self.translate_order_by( self.order_by )
        
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
        if isinstance( order_by, basestring ):
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
    """Subclass of :class:`sqlalchmey.ext.declarative.DeclarativeMeta`.  This
    metaclass processes the Property and ClassMutator objects.
    """
    
    # new is called to create a new Entity class
    def __new__( cls, classname, bases, dict_ ):
        #
        # don't modify the Entity class itself
        #
        if classname != 'Entity':
            entity_base = None
            for base in bases:
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
            if '__tablename__' not in dict_:
                dict_['__tablename__'] = classname.lower()
            if '__mapper_args__' not in dict_:
                dict_['__mapper_args__'] = dict()

             
        return super( EntityMeta, cls ).__new__( cls, classname, bases, dict_ )
    
    # init is called after the creation of the new Entity class, and can be
    # used to initialize it
    def __init__( cls, classname, bases, dict_ ):
        from . properties import Property
        if '_descriptor' in dict_:
            descriptor = dict_['_descriptor']
            descriptor.set_entity( cls )
            for key, value in dict_.items():
                if isinstance( value, Property ):
                    value.attach( cls, key )
            cls._descriptor.create_pk_cols()
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

    for key, value in data.iteritems():
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
    
def entity_to_dict( entity, deep = {}, exclude = []  ):
    """Generate a JSON-style nested dict/list structure from an object."""
    
    mapper = orm.object_mapper( entity )
    
    col_prop_names = [p.key for p in mapper.iterate_properties \
                                  if isinstance(p, orm.properties.ColumnProperty)]
    data = dict([(name, getattr(entity, name))
                 for name in col_prop_names if name not in exclude])
    
    for rname, rdeep in deep.iteritems():
        dbdata = getattr(entity, rname)
        prop = mapper.get_property( rname )
        if dbdata is None:
            data[rname] = None
        elif isinstance(dbdata, list):
            fks = prop.remote_side
            #FIXME: use attribute names (ie coltoprop) instead of column names
            remote_exclude = exclude + [ c.name for c in fks ]            
            data[rname] = [ entity_to_dict( o, rdeep, remote_exclude ) for o in dbdata ]
        else:
            data[rname] = entity_to_dict( dbdata, rdeep, exclude )
    
    return data    

class EntityBase( object ):
    """A declarative base class that adds some methods that used to be
    available in Elixir"""
    
    def __init__( self, *args, **kwargs ): 
        _declarative_constructor( self, *args, **kwargs ) 
        Session().add( self ) 
                                    
    #
    # methods below were copied from Elixir to mimic the Elixir Entity
    # behavior
    #
    
    def set( self, **kwargs ):
        for key, value in kwargs.iteritems():
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

    def to_dict( self, deep = {}, exclude = [] ):
        """Generate a JSON-style nested dict/list structure from an object."""
        return entity_to_dict( self, deep, exclude )

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
    def query_expression( cls ):
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
