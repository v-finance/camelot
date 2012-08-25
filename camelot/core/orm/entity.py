import sys

from sqlalchemy import orm, schema
from sqlalchemy.ext.declarative import ( _declarative_constructor,
                                         DeclarativeMeta )

from . statements import MUTATORS
from . properties import EntityBuilder, Property
from . import options

class EntityDescriptor(object):
    """
    EntityDescriptor holds information about the Entity before it is
    passed to Declarative.  It is used to search for inverse relations
    defined on an Entity before the relation is passed to Declarative.
    """

    def __init__( self, entity ):
        self.entity = entity
        self.parent = None
        self.relationships = []
        self.has_pk = False
        self._pk_col_done = False
        self.module = sys.modules.get( entity.__module__ )
        self.builders = [] 
        self.constraints = []
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
                schema.Column( colname, options.DEFAULT_AUTO_PRIMARYKEY_TYPE,
                               primary_key = True ) )
        self._pk_col_done = True
        
    def create_properties(self):
        self.call_builders( 'create_properties' )        
        
    def add_column( self, col ):
        setattr( self.entity, col.name, col )
        if col.primary_key:
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
        return super( EntityMeta, cls ).__new__( cls, classname, bases, dict_ )
    
    # init is called after the creation of the new Entity class, and can be
    # used to initialize it
    def __init__( cls, classname, bases, dict_ ):
        from . properties import Property
        if classname != 'Entity':
            cls._descriptor = EntityDescriptor( cls )
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
        
        
class EntityBase( object ):
    """A declarative base class that adds some methods that used to be
    available in Elixir"""
    
    def __init__( self, *args, **kwargs ): 
        from . import Session
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
        
        mapper = orm.class_mapper( cls )
        pk_props = mapper.primary_key

        # if all pk are present and not None
        if not [1 for p in pk_props if data.get( p.key ) is None]:
            pk_tuple = tuple( [data[prop.key] for prop in pk_props] )
            record = cls.query.get(pk_tuple)
            if record is None:
                if surrogate:
                    raise Exception("cannot create surrogate with pk")
                else:
                    record = cls()
        else:
            if surrogate:
                record = cls()
            else:
                raise Exception("cannot create non surrogate without pk")
        record.from_dict( data )
        return record
    
    def from_dict(self, data):
        """
        Update a mapped class with data from a JSON-style nested dict/list
        structure.
        """
        # surrogate can be guessed from autoincrement/sequence but I guess
        # that's not 100% reliable, so we'll need an override

        mapper = orm.object_mapper( self )

        for key, value in data.iteritems():
            if isinstance(value, dict):
                dbvalue = getattr(self, key)
                rel_class = mapper.get_property(key).mapper.class_
                pk_props = orm.class_mapper( rel_class ).primary_key

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

    def to_dict( self, deep = {}, exclude = [] ):
        """Generate a JSON-style nested dict/list structure from an object."""
        
        mapper = orm.object_mapper( self )
        
        col_prop_names = [p.key for p in mapper.iterate_properties \
                                      if isinstance(p, orm.properties.ColumnProperty)]
        data = dict([(name, getattr(self, name))
                     for name in col_prop_names if name not in exclude])
        for rname, rdeep in deep.iteritems():
            dbdata = getattr(self, rname)
            #FIXME: use attribute names (ie coltoprop) instead of column names
            fks = mapper.get_property( rname ).remote_side
            exclude = [ c.name for c in fks ]
            if dbdata is None:
                data[rname] = None
            elif isinstance(dbdata, list):
                data[rname] = [ o.to_dict( rdeep, exclude ) for o in dbdata ]
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