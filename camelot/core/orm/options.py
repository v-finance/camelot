from sqlalchemy import types

from . statements import ClassMutator

DEFAULT_AUTO_PRIMARYKEY_NAME = "id"
DEFAULT_AUTO_PRIMARYKEY_TYPE = types.Integer

OLD_M2MCOL_NAMEFORMAT = lambda data:"%(tablename)s_%(key)s%(numifself)s"%data
ALTERNATE_M2MCOL_NAMEFORMAT = lambda data:"%(inversename)s_%(key)s"%data

def default_m2m_column_formatter(data):
    if data['selfref']:
        return ALTERNATE_M2MCOL_NAMEFORMAT(data)
    else:
        return OLD_M2MCOL_NAMEFORMAT(data)

NEW_M2MCOL_NAMEFORMAT = default_m2m_column_formatter

# format constants
FKCOL_NAMEFORMAT = "%(relname)s_%(key)s"
M2MCOL_NAMEFORMAT = NEW_M2MCOL_NAMEFORMAT
CONSTRAINT_NAMEFORMAT = "%(tablename)s_%(colnames)s_fk"
MULTIINHERITANCECOL_NAMEFORMAT = "%(entity)s_%(key)s"

options_defaults = dict(
    identity=None,
    tablename=None,
    shortnames=False,
    auto_primarykey=True,
    order_by=None,
    table_options={},
)

valid_options = options_defaults.keys() + [
    'metadata',
    'session',
]

class using_options( ClassMutator ):
    
    def process( self, entity_dict, tablename = None, order_by = None, **kwargs ):
        if tablename:
            entity_dict['__tablename__'] = tablename
        if order_by:
            mapper_args = entity_dict.setdefault('__mapper_args__', {} )
            mapper_args['order_by'] = order_by
        for kwarg in kwargs:
            if kwarg in valid_options:
                setattr( entity_dict['_descriptor'], kwarg, kwargs[kwarg])
            else:
                raise Exception("'%s' is not a valid option for entities."
                                % kwarg)
    
