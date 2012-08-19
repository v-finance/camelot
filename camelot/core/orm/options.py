from sqlalchemy import types

from . statements import ClassMutator

DEFAULT_AUTO_PRIMARYKEY_NAME = "id"
DEFAULT_AUTO_PRIMARYKEY_TYPE = types.Integer

class using_options( ClassMutator ):
    
    def process( self, entity_dict, tablename = None, order_by = None ):
        if tablename:
            entity_dict['__tablename__'] = tablename
        if order_by:
            mapper_args = entity_dict.get('__mapper_args__', {} )
            mapper_args['order_by'] = order_by
            
class using_table_options( ClassMutator ):
    
    def process( self, entity_dict, tablename = None, order_by = None ):
        raise NotImplementedError()
    
class using_mapper_options( ClassMutator ):
    
    def process( self, entity_dict, tablename = None, order_by = None ):    
        raise NotImplementedError()
    
class options_defaults( ClassMutator ):
    
    def process( self, entity_dict, tablename = None, order_by = None ):    
        raise NotImplementedError()
    
class using_options_defaults( ClassMutator ):
    
    def process( self, entity_dict, tablename = None, order_by = None ):    
        raise NotImplementedError()
