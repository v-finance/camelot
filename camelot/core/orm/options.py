#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
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
|                     | ``camelot.core.orm.metadata``.                        |
|                     | This option can also be set for all entities of a     |
|                     | module by setting the ``__metadata__`` attribute of   |
|                     | that module.                                          |
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
|                     | ``camelot.core.orm.Session``.                         |
|                     | This option takes a ``ScopedSession`` object or       |
|                     | ``None``. In the later case your entity will be       |
|                     | mapped using a non-contextual mapper which requires   |
|                     | manual session management, as seen in pure SQLAlchemy.|
+---------------------+-------------------------------------------------------+

For examples, please refer to the examples and unit tests.

"""

from sqlalchemy import types


DEFAULT_AUTO_PRIMARYKEY_NAME = "id"
DEFAULT_AUTO_PRIMARYKEY_KWARGS = dict(primary_key=True, doc='The primary key')
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

valid_options = list( options_defaults.keys() ) + [
    'metadata',
    'session',
]


