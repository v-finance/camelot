
from sqlalchemy import orm

from . statements import ClassMutator

class EntityBuilder( object ):
    """
    Abstract base class for all entity builders. An Entity builder is a class
    of objects which can be added to an Entity (usually by using special
    properties or statements) to "build" that entity. Building an entity,
    meaning to add columns to its "main" table, create other tables, add
    properties to its mapper, ... To do so an EntityBuilder must override the
    corresponding method(s). This is to ensure the different operations happen
    in the correct order (for example, that the table is fully created before
    the mapper that use it is defined).
    """
    
    def create_pk_cols(self):
        pass

    def create_non_pk_cols(self):
        pass

    def before_table(self):
        pass

    def create_tables(self):
        '''
        Subclasses may override this method to create tables.
        '''

    def after_table(self):
        pass

    def create_properties(self):
        '''
        Subclasses may override this method to add properties to the involved
        entity.
        '''

    def before_mapper(self):
        pass

    def after_mapper(self):
        pass

    def finalize(self):
        pass
        
class Property( EntityBuilder ):
    """
    Abstract base class for all properties of an Entity that are not handled
    by Declarative but should be handled by EntityMeta before a new Entity
    subclass is constructed
    """

    def __init__(self, *args, **kwargs):
        self.entity = None
        self.name = None

    def attach( self, entity, name ):
        """Attach this property to its entity, using 'name' as name.

        Properties will be attached in the order they were declared.
        """
        self.entity = entity
        self.name = name

    def __repr__(self):
        return "Property(%s, %s)" % (self.name, self.entity)

class DeferredProperty( Property ):
    """Abstract base class for all properties of an Entity that are not 
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
        
class GenericProperty( DeferredProperty ):
    '''
    Generic catch-all class to wrap an SQLAlchemy property.

    .. sourcecode:: python

        class OrderLine(Entity):
            quantity = Field(Float)
            unit_price = Field(Numeric)
            price = GenericProperty(lambda c: column_property(
                             (c.quantity * c.unit_price).label('price')))
    '''
    
    process_order = 4
    
    def __init__( self, prop, *args, **kwargs ):
        super( GenericProperty, self ).__init__()
        self.prop = prop
        self.args = args
        self.kwargs = kwargs
        
    def create_properties(self):
        table = orm.class_mapper( self.entity ).local_table
        if hasattr( self.prop, '__call__' ):
            prop_value = self.prop( table.c )
        else:
            prop_value = self.prop
        prop_value = self.evaluate_property( prop_value )
        setattr( self.entity, self.name, prop_value )

    def evaluate_property(self, prop):
        if self.args or self.kwargs:
            raise Exception('superfluous arguments passed to GenericProperty')
        return prop
    
    def _config( self, cls, mapper, key ):
        if hasattr(self.prop, '__call__'):
            prop_value = self.prop( mapper.local_table.c )
        else:
            prop_value = self.prop
        setattr( cls, key, prop_value )
        
class ColumnProperty( GenericProperty ):

    def evaluate_property( self, prop ):
        return orm.column_property( prop.label(None), *self.args, **self.kwargs )

class has_property( ClassMutator ):
    
    def process( self, entity_dict, name, prop, *args, **kwargs ):
        entity_dict[ name ] = GenericProperty( prop, *args, **kwargs )
