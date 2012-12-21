"""
This module provides support for defining several options on your
entities.  

`using_options`
---------------
The 'using_options' DSL statement allows you to set up some additional
behaviors on your model objects, including table names, ordering, and
more.  To specify an option, simply supply the option as a keyword
argument onto the statement, as follows:

.. sourcecode:: python

    class Person(Entity):
        using_options(tablename='person', order_by='name')
        name = Field(Unicode(64))

        

The list of supported arguments are as follows:

+---------------------+-------------------------------------------------------+
| Option Name         | Description                                           |
+=====================+=======================================================+
| ``metadata``        | Specify a custom MetaData for this entity.            |
|                     | By default, entities uses the global                  |
|                     | ``elixir.metadata``.                                  |
|                     | This option can also be set for all entities of a     |
|                     | module by setting the ``__metadata__`` attribute of   |
|                     | that module.                                          | |
+---------------------+-------------------------------------------------------+
| ``tablename``       | Specify a custom tablename. You can either provide a  |
|                     | plain string or a callable. The callable will be      |
|                     | given the entity (ie class) as argument and must      |
|                     | return a string representing the name of the table    |
|                     | for that entity. By default, the tablename is         |
|                     | automatically generated: it is a concatenation of the |
|                     | full module-path to the entity and the entity (class) |
|                     | name itself. The result is lower-cased and separated  |
|                     | by underscores ("_"), eg.: for an entity named        |
|                     | "MyEntity" in the module "project1.model", the        |
|                     | generated table name will be                          |
|                     | "project1_model_myentity".                            |
+---------------------+-------------------------------------------------------+
| ``order_by``        | How to order select results. Either a string or a     |
|                     | list of strings, composed of the field name,          |
|                     | optionally lead by a minus (for descending order).    |
+---------------------+-------------------------------------------------------+
| ``session``         | Specify a custom contextual session for this entity.  |
|                     | By default, entities uses the global                  |
|                     | ``elixir.session``.                                   |
|                     | This option takes a ``ScopedSession`` object or       |
|                     | ``None``. In the later case your entity will be       |
|                     | mapped using a non-contextual mapper which requires   |
|                     | manual session management, as seen in pure SQLAlchemy.|
|                     | This option can also be set for all entities of a     |
|                     | module by setting the ``__session__`` attribute of    |
|                     | that module.                                          |
+---------------------+-------------------------------------------------------+

For examples, please refer to the examples and unit tests.

"""

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
    """This statement its sole reason of existence is to keep existing Elixir
    model definitions working.  Do not use it when writing new code, instead
    use Declarative directly."""
    
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
    
