from sqlalchemy import schema, orm

from . properties import Property
from . statements import ClassMutator

class Field(Property):
    '''
    Represents the definition of a 'field' on an entity.

    This class represents a column on the table where the entity is stored.
    '''

    def __init__(self, type, *args, **kwargs):
        super(Field, self).__init__()

        self.colname = kwargs.pop('colname', None)
        self.synonym = kwargs.pop('synonym', None)
        self.deferred = kwargs.pop('deferred', False)
        if 'required' in kwargs:
            kwargs['nullable'] = not kwargs.pop('required')
        self.type = type
        self.primary_key = kwargs.get('primary_key', False)

        self.column = None
        self.property = None

        self.args = args
        self.kwargs = kwargs

    def attach(self, entity, name):
        # If no colname was defined (through the 'colname' kwarg), set
        # it to the name of the attr.
        if self.colname is None:
            self.colname = name
        super(Field, self).attach(entity, name)

    def create_pk_cols(self):
        if self.primary_key:
            self.create_col()

    def create_non_pk_cols(self):
        if not self.primary_key:
            self.create_col()

    def create_col( self ):
        self.column = schema.Column( self.colname, self.type, *self.args, **self.kwargs )
        self.entity._descriptor.add_column( self.column )

    def create_properties(self):
        if self.deferred:
            group = None
            if isinstance(self.deferred, basestring):
                group = self.deferred
            self.property = orm.deferred( self.column, group = group )
        elif self.name != self.colname:
            # if the property name is different from the column name, we need
            # to add an explicit property (otherwise nothing is needed as it's
            # done automatically by SA)
            self.property = self.column

        if self.property is not None:
            self.entity._descriptor.add_property( self.name, self.property )

        if self.synonym:
            self.entity._descriptor.add_property( self.synonym, orm.synonym( self.name ) )
        
class has_field( ClassMutator ):
    
    def process( self, entity_dict, name, *args, **kwargs ):
        entity_dict[ name ] = Field( *args, **kwargs )
