from sqlalchemy import schema, orm

from . properties import Property
from . statements import ClassMutator

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

    def attach( self, entity, name ):
        if self.deferred:
            setattr( entity, name, orm.deferred( self ) )
        
class has_field( ClassMutator ):
    
    def process( self, entity_dict, name, *args, **kwargs ):
        entity_dict[ name ] = Field( *args, **kwargs )
