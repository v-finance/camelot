from sqlalchemy import types

from . statements import ClassMutator

DEFAULT_AUTO_PRIMARYKEY_NAME = "id"
DEFAULT_AUTO_PRIMARYKEY_TYPE = types.Integer

OLD_M2MCOL_NAMEFORMAT = "%(tablename)s_%(key)s%(numifself)s"
ALTERNATE_M2MCOL_NAMEFORMAT = "%(inversename)s_%(key)s"

def default_m2m_column_formatter(data):
    if data['selfref']:
        return ALTERNATE_M2MCOL_NAMEFORMAT % data
    else:
        return OLD_M2MCOL_NAMEFORMAT % data

NEW_M2MCOL_NAMEFORMAT = default_m2m_column_formatter

# format constants
FKCOL_NAMEFORMAT = "%(relname)s_%(key)s"
M2MCOL_NAMEFORMAT = NEW_M2MCOL_NAMEFORMAT
CONSTRAINT_NAMEFORMAT = "%(tablename)s_%(colnames)s_fk"
MULTIINHERITANCECOL_NAMEFORMAT = "%(entity)s_%(key)s"

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
