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
import six

from sqlalchemy import schema, orm

from . properties import EntityBuilder
from . statements import ClassMutator

"""
This module provides support for defining the fields (columns) of your
entities. This module sole reason of existence is to keep existing Elixir
model definitions working.  Do not use it when writing new code, instead
use Declarative directly.

Two syntaxes are supported, the default attribute-based syntax as well as 
the `has_field` DSL statement.

Attribute-based syntax
----------------------

Here is a quick example of how to use the object-oriented syntax.

.. sourcecode:: python

    class Person(Entity):
        id = Field(Integer, primary_key=True)
        name = Field(String(50), required=True)
        ssn = Field(String(50), unique=True)
        biography = Field(Text)
        join_date = Field(DateTime, default=datetime.datetime.now)
        photo = Field(Binary, deferred=True)
        _email = Field(String(20), colname='email', synonym='email')

        def _set_email(self, email):
           self._email = email
        def _get_email(self):
           return self._email
           
        email = property(_get_email, _set_email)


The Field class takes one mandatory argument, which is its type. Please refer
to SQLAlchemy documentation for a list of `types supported by SQLAlchemy
<http://docs.sqlalchemy.org/en/rel_0_7/core/types.html>`_.

Following that first mandatory argument, fields can take any number of
optional keyword arguments. Please note that all the **arguments** that are
**not specifically processed by the Camelot orm module**, as mentioned in the 
documentation below **are passed on to the 
:class:`sqlalchemy:sqlalchemy.schema.Column` object**.

The following non SQLAlchemy-specific arguments are supported:

+-------------------+---------------------------------------------------------+
| Argument Name     | Description                                             |
+===================+=========================================================+
| ``required``      | Specify whether or not this field can be set to None    |
|                   | (left without a value). Defaults to ``False``, unless   |
|                   | the field is a primary key.                             |
+-------------------+---------------------------------------------------------+
| ``colname``       | Specify a custom name for the column of this field. By  |
|                   | default the column will have the same name as the       |
|                   | attribute.                                              |
+-------------------+---------------------------------------------------------+
| ``deferred``      | Specify whether this particular column should be        |
|                   | fetched by default (along with the other columns) when  |
|                   | an instance of the entity is fetched from the database  |
|                   | or rather only later on when this particular column is  |
|                   | first referenced. This can be useful when one wants to  |
|                   | avoid loading a large text or binary field into memory  |
|                   | when its not needed. Individual columns can be lazy     |
|                   | loaded by themselves (by using ``deferred=True``)       |
|                   | or placed into groups that lazy-load together (by using |
|                   | ``deferred`` = `"group_name"`).                         |
+-------------------+---------------------------------------------------------+
| ``synonym``       | Specify a synonym name for this field. The field will   |
|                   | also be usable under that name in keyword-based Query   |
|                   | functions such as filter_by. The Synonym class (see the |
|                   | `properties` module) provides a similar functionality   |
|                   | with an (arguably) nicer syntax, but a limited scope.   |
+-------------------+---------------------------------------------------------+

has_field
---------

The `has_field` statement allows you to define fields one at a time.

The first argument is the name of the field, the second is its type. Following
these, any number of keyword arguments can be specified for additional
behavior. 

Here is a quick example of how to use ``has_field``.

.. sourcecode:: python

    class Person(Entity):
        has_field('id', Integer, primary_key=True)
        has_field('name', String(50))
"""

class Field(EntityBuilder):
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
        self.property = None
        self.column = None
        self.column_created = False

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
        if self.column_created:
            return
        self.column = schema.Column( self.colname, self.type, *self.args, **self.kwargs )
        self.column_created = True
        if self.deferred:
            group = None
            if isinstance( self.deferred, six.string_types ):
                group = self.deferred
            self.column = orm.deferred( self.column, group = group )            
        self.entity._descriptor.add_column( self.kwargs.get( 'key', self.name ), self.column )

    def create_properties(self):
        if self.property is not None:
            self.entity._descriptor.add_property( self.name, self.property )

        if self.synonym:
            self.entity._descriptor.add_property( self.synonym, orm.synonym( self.name ) )
        
class has_field( ClassMutator ):
    
    def process( self, entity_dict, name, *args, **kwargs ):
        entity_dict[ name ] = Field( *args, **kwargs )


