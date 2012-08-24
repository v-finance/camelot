
from sqlalchemy.orm import column_property

from . statements import ClassMutator

class Property( object ):
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
        # register this property as a builder
        entity._descriptor.add_property( self )

    def __repr__(self):
        return "Property(%s, %s)" % (self.name, self.entity)

class DeferredProperty( Property ):
    """Abstract base class for all properties of an Entity that are not 
    handled by Declarative but should be handled after a mapper was
    configured"""
        
    def _config( self, cls, mapper, key ):
        self.name = key
        self.entity = cls
        
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
        
    def _config( self, cls, mapper, key ):
        if hasattr(self.prop, '__call__'):
            prop_value = self.prop( mapper.local_table.c )
        else:
            prop_value = self.prop
        setattr( cls, key, prop_value )
        
class ColumnProperty( GenericProperty ):

    def _config(self, cls, mapper, key):
        setattr( cls, key, column_property( self.prop( mapper.local_table.c ).label(None), 
                                            *self.args, 
                                            **self.kwargs ) )

class has_property( ClassMutator ):
    
    def process( self, entity_dict, name, prop, *args, **kwargs ):
        entity_dict[ name ] = GenericProperty( prop, *args, **kwargs )
