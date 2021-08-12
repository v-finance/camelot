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
'''
This module provides support for defining relationships between your
entities.  Two syntaxes are supported to do so: the default
`Attribute-based syntax`_ which supports the following types of relationships:
ManyToOne_, OneToMany_, OneToOne_ and ManyToMany_, as well as a
`DSL-based syntax`_ which provides the following statements: belongs_to_,
has_many_, has_one_ and has_and_belongs_to_many_.

======================
Attribute-based syntax
======================

The first argument to all these "normal" relationship classes is the name of
the class (entity) you are relating to.

Following that first mandatory argument, any number of additional keyword
arguments can be specified for advanced behavior. See each relationship type
for a list of their specific keyword arguments. At this point, we'll just note
that all the arguments that are not specifically processed, as
mentioned in the documentation below are passed on to the SQLAlchemy
``relationship`` function. So, please refer to the `SQLAlchemy relationship function's
documentation <http://docs.sqlalchemy.org/en/rel_0_7/orm/tutorial.html
#building-a-relationship>`_ for further detail about which
keyword arguments are supported.

You should keep in mind that the following
keyword arguments are automatically generated and should not be used
unless you want to override the default value provided : ``uselist``,
``remote_side``, ``secondary``, ``primaryjoin`` and ``secondaryjoin``.

Additionally, if you want a bidirectionnal relationship, you should define the
inverse relationship on the other entity explicitly (as opposed to how
SQLAlchemy's backrefs are defined). In non-ambiguous situations, relationships will
be matched together automatically. If there are several relationships
of the same type between two entities, you have to disambiguate the
situation by giving the name of the inverse relationship in the ``inverse``
keyword argument.

Here is a detailed explanation of each relation type:

`ManyToOne`
-----------

Describes the child's side of a parent-child relationship.  For example,
a `Pet` object may belong to its owner, who is a `Person`.  This could be
expressed like so:

.. sourcecode:: python

    class Pet(Entity):
        owner = ManyToOne('Person')

Behind the scene, assuming the primary key of the `Person` entity is
an integer column named `id`, the ``ManyToOne`` relationship will
automatically add an integer column named `owner_id` to the entity, with a
foreign key referencing the `id` column of the `Person` entity.

In addition to the keyword arguments inherited from SQLAlchemy's relation
function, ``ManyToOne`` relationships accept the following optional arguments
which will be directed to the created column:

+----------------------+------------------------------------------------------+
| Option Name          | Description                                          |
+======================+======================================================+
| ``colname``          | Specify a custom name for the foreign key column(s). |
|                      | This argument accepts either a single string or a    |
|                      | list of strings. The number of strings passed must   |
|                      | match the number of primary key columns of the target|
|                      | entity. If this argument is not used, the name of the|
|                      | column(s) is generated with the pattern              |
|                      | defined in options.FKCOL_NAMEFORMAT, which is, by    |
|                      | default: "%(relname)s_%(key)s", where relname is the |
|                      | name of the ManyToOne relationship, and 'key' is the |
|                      | name (key) of the primary column in the target       |
|                      | entity. That's with, in the above Pet/owner example, |
|                      | the name of the column would be: "owner_id".         |
+----------------------+------------------------------------------------------+
| ``required``         | Specify whether or not this field can be set to None |
|                      | (left without a value). Defaults to ``False``,       |
|                      | unless the field is a primary key.                   |
+----------------------+------------------------------------------------------+
| ``primary_key``      | Specify whether or not the column(s) created by this |
|                      | relationship should act as a primary_key.            |
|                      | Defaults to ``False``.                               |
+----------------------+------------------------------------------------------+
| ``column_kwargs``    | A dictionary holding any other keyword argument you  |
|                      | might want to pass to the Column.                    |
+----------------------+------------------------------------------------------+
| ``target_column``    | Name (or list of names) of the target column(s).     |
|                      | If this argument is not specified, the target entity |
|                      | primary key column(s) are used.                      |
+----------------------+------------------------------------------------------+

The following optional arguments are also supported to customize the
ForeignKeyConstraint that is created:

+----------------------+------------------------------------------------------+
| Option Name          | Description                                          |
+======================+======================================================+
| ``use_alter``        | If True, SQLAlchemy will add the constraint in a     |
|                      | second SQL statement (as opposed to within the       |
|                      | create table statement). This permits to define      |
|                      | tables with a circular foreign key dependency        |
|                      | between them.                                        |
+----------------------+------------------------------------------------------+
| ``ondelete``         | Value for the foreign key constraint ondelete clause.|
|                      | May be one of: ``cascade``, ``restrict``,            |
|                      | ``set null``, or ``set default``.                    |
+----------------------+------------------------------------------------------+
| ``onupdate``         | Value for the foreign key constraint onupdate clause.|
|                      | May be one of: ``cascade``, ``restrict``,            |
|                      | ``set null``, or ``set default``.                    |
+----------------------+------------------------------------------------------+
| ``constraint_kwargs``| A dictionary holding any other keyword argument you  |
|                      | might want to pass to the Constraint.                |
+----------------------+------------------------------------------------------+

In some cases, you may want to declare the foreign key column explicitly,
instead of letting it be generated automatically.  There are several reasons to
that: it could be because you want to declare it with precise arguments and
using column_kwargs makes your code ugly, or because the name of
your column conflicts with the property name (in which case an error is
thrown).  In those cases, you can use the ``field`` argument to specify an
already-declared field to be used for the foreign key column.

For example, for the Pet example above, if you want the database column
(holding the foreign key) to be called 'owner', one should use the field
parameter to specify the field manually.

.. sourcecode:: python

    class Pet(Entity):
        owner_id = Field(Integer, colname='owner')
        owner = ManyToOne('Person', field=owner_id)

+----------------------+------------------------------------------------------+
| Option Name          | Description                                          |
+======================+======================================================+
| ``field``            | Specify the previously-declared field to be used for |
|                      | the foreign key column. Use of this parameter is     |
|                      | mutually exclusive with the colname and column_kwargs|
|                      | arguments.                                           |
+----------------------+------------------------------------------------------+


Additionally, the belongs_to_ statement is supported as an alternative,
DSL-based, syntax to define ManyToOne_ relationships.


`OneToMany`
-----------

Describes the parent's side of a parent-child relationship when there can be
several children.  For example, a `Person` object has many children, each of
them being a `Person`. This could be expressed like so:

.. sourcecode:: python

    class Person(Entity):
        parent = ManyToOne('Person')
        children = OneToMany('Person')

Note that a ``OneToMany`` relationship **cannot exist** without a
corresponding ``ManyToOne`` relationship in the other way. This is because the
``OneToMany`` relationship needs the foreign key created by the ``ManyToOne``
relationship.

In addition to keyword arguments inherited from SQLAlchemy, ``OneToMany``
relationships accept the following optional (keyword) arguments:

+--------------------+--------------------------------------------------------+
| Option Name        | Description                                            |
+====================+========================================================+
| ``order_by``       | Specify which field(s) should be used to sort the      |
|                    | results given by accessing the relation field.         |
|                    | Note that this sort order is only applied when loading |
|                    | objects from the database. Objects appended to the     |
|                    | collection afterwards are not re-sorted in-memory on   |
|                    | the fly.                                               |
|                    | This argument accepts either a string or a list of     |
|                    | strings, each corresponding to the name of a field in  |
|                    | the target entity. These field names can optionally be |
|                    | prefixed by a minus (for descending order).            |
+--------------------+--------------------------------------------------------+
| ``filter``         | Specify a filter criterion (as a clause element) for   |
|                    | this relationship. This criterion will be ``and_`` ed  |
|                    | with the normal join criterion (primaryjoin) generated |
|                    | by Elixir for the relationship. For example:           |
|                    | boston_addresses =                                     |
|                    | OneToMany('Address', filter=Address.city == 'Boston')  |
+--------------------+--------------------------------------------------------+

Additionally, an alternate DSL-based is supported, syntax to define
OneToMany_ relationships, with the has_many_ statement.


`OneToOne`
----------

Describes the parent's side of a parent-child relationship when there is only
one child.  For example, a `Car` object has one gear stick, which is
represented as a `GearStick` object. This could be expressed like so:

.. sourcecode:: python

    class Car(Entity):
        gear_stick = OneToOne('GearStick', inverse='car')

    class GearStick(Entity):
        car = ManyToOne('Car')

Note that a ``OneToOne`` relationship **cannot exist** without a corresponding
``ManyToOne`` relationship in the other way. This is because the ``OneToOne``
relationship needs the foreign_key created by the ``ManyToOne`` relationship.

Additionally, an alternate DSL-based syntax is supported to define
OneToOne_ relationships, with the has_one_ statement.


`ManyToMany`
------------

Describes a relationship in which one kind of entity can be related to several
objects of the other kind but the objects of that other kind can be related to
several objects of the first kind.  For example, an `Article` can have several
tags, but the same `Tag` can be used on several articles.

.. sourcecode:: python

    class Article(Entity):
        tags = ManyToMany('Tag')

    class Tag(Entity):
        articles = ManyToMany('Article')

Behind the scene, the ``ManyToMany`` relationship will automatically create an
intermediate table to host its data.

Note that you don't necessarily need to define the inverse relationship.  In
our example, even though we want tags to be usable on several articles, we
might not be interested in which articles correspond to a particular tag.  In
that case, we could have omitted the `Tag` side of the relationship.

If your ``ManyToMany`` relationship is self-referencial, the entity
containing it is autoloaded (and you don't intend to specify both the
primaryjoin and secondaryjoin arguments manually), you must specify at least
one of either the ``remote_colname`` or ``local_colname`` argument.

In addition to keyword arguments inherited from SQLAlchemy, ``ManyToMany``
relationships accept the following optional (keyword) arguments:

+--------------------+--------------------------------------------------------+
| Option Name        | Description                                            |
+====================+========================================================+
| ``tablename``      | Specify a custom name for the intermediary table. This |
|                    | can be used both when the tables needs to be created   |
|                    | and when the table is autoloaded/reflected from the    |
|                    | database. If this argument is not used, a name will be |
|                    | automatically generated by Elixir depending on the name|
|                    | of the tables of the two entities of the relationship, |
|                    | the name of the relationship, and, if present, the name|
|                    | of its inverse. Even though this argument is optional, |
|                    | it is wise to use it if you are not sure what are the  |
|                    | exact consequence of using a generated table name.     |
+--------------------+--------------------------------------------------------+
| ``schema``         | Specify a custom schema for the intermediate table.    |
|                    | This can be used both when the tables needs to         |
|                    | be created and when the table is autoloaded/reflected  |
|                    | from the database.                                     |
+--------------------+--------------------------------------------------------+
| ``remote_colname`` | A string or list of strings specifying the names of    |
|                    | the column(s) in the intermediary table which          |
|                    | reference the "remote"/target entity's table.          |
+--------------------+--------------------------------------------------------+
| ``local_colname``  | A string or list of strings specifying the names of    |
|                    | the column(s) in the intermediary table which          |
|                    | reference the "local"/current entity's table.          |
+--------------------+--------------------------------------------------------+
| ``table``          | Use a manually created table. If this argument is      |
|                    | used, Elixir won't generate a table for this           |
|                    | relationship, and use the one given instead.           |
+--------------------+--------------------------------------------------------+
| ``order_by``       | Specify which field(s) should be used to sort the      |
|                    | results given by accessing the relation field.         |
|                    | Note that this sort order is only applied when loading |
|                    | objects from the database. Objects appended to the     |
|                    | collection afterwards are not re-sorted in-memory on   |
|                    | the fly.                                               |
|                    | This argument accepts either a string or a list of     |
|                    | strings, each corresponding to the name of a field in  |
|                    | the target entity. These field names can optionally be |
|                    | prefixed by a minus (for descending order).            |
+--------------------+--------------------------------------------------------+
| ``ondelete``       | Value for the foreign key constraint ondelete clause.  |
|                    | May be one of: ``cascade``, ``restrict``,              |
|                    | ``set null``, or ``set default``.                      |
+--------------------+--------------------------------------------------------+
| ``onupdate``       | Value for the foreign key constraint onupdate clause.  |
|                    | May be one of: ``cascade``, ``restrict``,              |
|                    | ``set null``, or ``set default``.                      |
+--------------------+--------------------------------------------------------+
| ``table_kwargs``   | A dictionary holding any other keyword argument you    |
|                    | might want to pass to the underlying Table object.     |
+--------------------+--------------------------------------------------------+


================
DSL-based syntax
================

The following DSL statements provide an alternative way to define relationships
between your entities. The first argument to all those statements is the name
of the relationship, the second is the 'kind' of object you are relating to
(it is usually given using the ``of_kind`` keyword).

`belongs_to`
------------

The ``belongs_to`` statement is the DSL syntax equivalent to the ManyToOne_
relationship. As such, it supports all the same arguments as ManyToOne_
relationships.

.. sourcecode:: python

    class Pet(Entity):
        belongs_to('feeder', of_kind='Person')
        belongs_to('owner', of_kind='Person', colname="owner_id")


`has_many`
----------

The ``has_many`` statement is the DSL syntax equivalent to the OneToMany_
relationship. As such, it supports all the same arguments as OneToMany_
relationships.

.. sourcecode:: python

    class Person(Entity):
        belongs_to('parent', of_kind='Person')
        has_many('children', of_kind='Person')


`has_one`
---------

The ``has_one`` statement is the DSL syntax equivalent to the OneToOne_
relationship. As such, it supports all the same arguments as OneToOne_
relationships.

.. sourcecode:: python

    class Car(Entity):
        has_one('gear_stick', of_kind='GearStick', inverse='car')

    class GearStick(Entity):
        belongs_to('car', of_kind='Car')


`has_and_belongs_to_many`
-------------------------

The ``has_and_belongs_to_many`` statement is the DSL syntax equivalent to the
ManyToMany_ relationship. As such, it supports all the same arguments as
ManyToMany_ relationships.

.. sourcecode:: python

    class Article(Entity):
        has_and_belongs_to_many('tags', of_kind='Tag')

    class Tag(Entity):
        has_and_belongs_to_many('articles', of_kind='Article')

'''

import logging

import six

from sqlalchemy import schema, sql
from sqlalchemy.orm import relationship, backref, class_mapper

from . properties import DeferredProperty
from . entity import EntityBase
from . fields import Field
from . statements import ClassMutator
from . import options

LOGGER = logging.getLogger( 'camelot.core.orm.relationships' )

class Relationship( DeferredProperty ):
    """Generates a one to many or many to one relationship."""

    process_order = 0
    
    def __init__(self, of_kind, inverse=None, *args, **kwargs):
        super( Relationship, self ).__init__()
        self.of_kind = of_kind
        self.inverse_name = inverse
        self._target = None
        self.property = None # sqlalchemy property
        self.backref = None  # sqlalchemy backref
        self.args = args
        self.kwargs = kwargs

    @property
    def target( self ):
        if not self._target:
            if isinstance( self.of_kind, six.string_types ):
                try:
                    # for Elixir compatibility, support full class names,
                    # including the modules, but only use the last part
                    # SQLA will issue warnings when multiple classes have the
                    # same name
                    self._target = self.entity._decl_class_registry[self.of_kind.split('.')[-1]]
                except KeyError:
                    LOGGER.error( 'Error setting up %s of %s'%( self.name,
                                                                self.entity.__name__ ) )
                    raise
            else:
                self._target = self.of_kind
        return self._target
    
    def attach( self, entity, name ):
        super( Relationship, self ).attach( entity, name )
        entity._descriptor.relationships.append( self )
        
    @property
    def inverse(self):
        if not hasattr(self, '_inverse'):
            if self.inverse_name:
                desc = self.target._descriptor
                inverse = desc.find_relationship(self.inverse_name)
                if inverse is None:
                    raise Exception(
                              "Couldn't find a relationship named '%s' in "
                              "entity '%s' or its parent entities."
                              % (self.inverse_name, self.target.__name__))
                assert self.match_type_of(inverse), \
                    "Relationships '%s' in entity '%s' and '%s' in entity " \
                    "'%s' cannot be inverse of each other because their " \
                    "types do not form a valid combination." % \
                    (self.name, self.entity.__name__,
                     self.inverse_name, self.target.__name__)
            else:
                check_reverse = not self.kwargs.get( 'viewonly', False )
                if issubclass(self.target, EntityBase):
                    inverse = self.target._descriptor.get_inverse_relation(
                        self, check_reverse=check_reverse)
                else:
                    inverse = None
            self._inverse = inverse
            if inverse and not self.kwargs.get('viewonly', False):
                inverse._inverse = self

        return self._inverse
    
    def match_type_of(self, other):
        return False
    
    def is_inverse( self, other ):
        # viewonly relationships are not symmetrical: a viewonly relationship
        # should have exactly one inverse (a ManyToOne relationship), but that
        # inverse shouldn't have the viewonly relationship as its inverse.
        return not other.kwargs.get('viewonly', False) and \
               other is not self and \
               self.match_type_of( other ) and \
               self.entity == other.target and \
               other.entity == self.target and \
               (self.inverse_name == other.name or not self.inverse_name) and \
               (other.inverse_name == self.name or not other.inverse_name)
    
    def create_pk_cols( self ):
        self.create_keys( True )

    def create_non_pk_cols( self ):
        self.create_keys( False )
        
    def create_keys( self, pk ):
        '''
        Subclasses (ie. concrete relationships) may override this method to
        create foreign keys.
        '''
        pass
        
    def create_properties( self ):
        if self.property or self.backref:
            return

        kwargs = self.get_prop_kwargs()
        if 'order_by' in kwargs:
            kwargs['order_by'] = \
                self.target._descriptor.translate_order_by( kwargs['order_by'] )
            
        # viewonly relationships need to create "standalone" relations (ie
        # shouldn't be a backref of another relation).
        if self.inverse and not kwargs.get( 'viewonly', False ):
            # check if the inverse was already processed (and thus has already
            # defined a backref we can use)
            if self.inverse.backref:
                # let the user override the backref argument
                if 'backref' not in kwargs:
                    kwargs['backref'] = self.inverse.backref
            else:
                # SQLAlchemy doesn't like when 'secondary' is both defined on
                # the relation and the backref
                kwargs.pop('secondary', None)

                # define backref for use by the inverse
                self.backref = backref( self.name, **kwargs )
                return
        
        self.property = relationship( self.target, **kwargs )
        setattr( self.entity, self.name, self.property )

class OneToOne( Relationship ):

    uselist = False
    process_order = 2
    
    def __init__(self, of_kind, filter=None, *args, **kwargs):
        self.filter = filter
        if filter is not None:
            # We set viewonly to True by default for filtered relationships,
            # unless manually overridden.
            # This is not strictly necessary, as SQLAlchemy allows non viewonly
            # relationships with a custom join/filter. The example at:
            # SADOCS/05/mappers.html#advdatamapping_relation_customjoin
            # is not viewonly. Those relationships can be used as if the extra
            # filter wasn't present when inserting. This can lead to a
            # confusing behavior (if you insert data which doesn't match the
            # extra criterion it'll get inserted anyway but you won't see it
            # when you query back the attribute after a round-trip to the
            # database).
            if 'viewonly' not in kwargs:
                kwargs['viewonly'] = True
        super(OneToOne, self).__init__(of_kind, *args, **kwargs)
    
    def match_type_of(self, other):
        return isinstance(other, ManyToOne)
    
    def create_keys( self, pk ):
        # make sure an inverse relationship exists
        if pk == False and self.inverse is None:
            raise Exception(
                      "Couldn't find any relationship in '%s' which "
                      "match as inverse of the '%s' relationship "
                      "defined in the '%s' entity. If you are using "
                      "inheritance you "
                      "might need to specify inverse relationships "
                      "manually by using the 'inverse' argument."
                      % (self.target, self.name,
                         self.entity))
        
    def get_prop_kwargs(self):
        kwargs = {'uselist': self.uselist}

        #TODO: for now, we don't break any test if we remove those 2 lines.
        # So, we should either complete the selfref test to prove that they
        # are indeed useful, or remove them. It might be they are indeed
        # useless because the remote_side is already setup in the other way
        # (ManyToOne).
        if self.entity.table is self.target.table:
            #FIXME: IF this code is of any use, it will probably break for
            # autoloaded tables
            kwargs['remote_side'] = self.inverse.foreign_key

        # Contrary to ManyToMany relationships, we need to specify the join
        # clauses even if this relationship is not self-referencial because
        # there could be several ManyToOne from the target class to us.
        joinclauses = self.inverse.primaryjoin_clauses
        if self.filter:
            # We need to make a copy of the joinclauses, to not add the filter
            # on the backref
            joinclauses = joinclauses[:] + [self.filter(self.target.table.c)]
        if joinclauses:
            kwargs['primaryjoin'] = sql.and_(*joinclauses)

        kwargs.update(self.kwargs)

        return kwargs    
    
class OneToMany( OneToOne ):
    """Generates a one to many relationship."""
    uselist = True

    def _get_pk_fk( self, cls, target_cls ):
        return cls, target_cls

class ManyToOne( Relationship ):
    """Generates a many to one relationship."""

    process_order = 1
    
    def __init__(self, of_kind,
                 column_kwargs=None,
                 colname=None, required=None, primary_key=None,
                 field=None, nullable=None,
                 constraint_kwargs=None,
                 use_alter=None, ondelete=None, onupdate=None,
                 target_column=None,
                 *args, **kwargs):

        # 1) handle column-related args

        # check that the column arguments don't conflict
        assert not ( isinstance( field, (schema.Column, Field) ) and (column_kwargs or colname)), \
               "ManyToOne can accept the 'field' argument or column " \
               "arguments ('colname' or 'column_kwargs') but not both!"

        if colname and not isinstance(colname, list):
            colname = [colname]
        self.colname = colname or []

        column_kwargs = column_kwargs or {}
        # kwargs go by default to the relation(), so we need to manually
        # extract those targeting the Column
        assert (nullable is None or required is None), \
               "Either specify required or nullable, but not both"
        if required is not None:
            column_kwargs['nullable'] = not required
        if nullable is not None:
            column_kwargs['nullable'] = nullable
        if primary_key is not None:
            column_kwargs['primary_key'] = primary_key
        # by default, created columns will have an index.
        column_kwargs.setdefault('index', True)
        self.column_kwargs = column_kwargs

        if isinstance( field, (schema.Column, Field) ) and not isinstance( field, list ):
            self.field = [field]
        else:
            self.field = []

        # 2) handle constraint kwargs
        constraint_kwargs = constraint_kwargs or {}
        if use_alter is not None:
            constraint_kwargs['use_alter'] = use_alter
        if ondelete is not None:
            constraint_kwargs['ondelete'] = ondelete
        if onupdate is not None:
            constraint_kwargs['onupdate'] = onupdate
        self.constraint_kwargs = constraint_kwargs

        # 3) misc arguments
        if target_column and not isinstance( target_column, list ):
            target_column = [target_column]
        self.target_column = target_column

        self.foreign_key = []
        self.primaryjoin_clauses = []

        super(ManyToOne, self).__init__( of_kind, *args, **kwargs )    
    
    def _get_pk_fk( self, cls, target_cls ):
        return target_cls, cls
    
    def create_keys( self, pk ):
        '''
        Find all primary keys on the target and create foreign keys on the
        source accordingly.
        '''

        if self.foreign_key:
            return
        
        if self.column_kwargs.get('primary_key', False) != pk:
            return        

        source_desc = self.entity._descriptor
        target_table = self.target_table

        fk_refcols = []
        fk_colnames = []

        if self.target_column is None:
            target_columns = target_table.primary_key.columns
        else:
            target_columns = [target_table.columns[col]
                              for col in self.target_column]

        if not target_columns:
            raise Exception("No primary key found in target table ('%s') "
                            "for the '%s' relationship of the '%s' entity."
                            % (target_table.name, self.name,
                               self.entity.__name__))
        if self.colname and \
           len(self.colname) != len(target_columns):
            raise Exception(
                    "The number of column names provided in the colname "
                    "keyword argument of the '%s' relationship of the "
                    "'%s' entity is not the same as the number of columns "
                    "of the primary key of '%s'."
                    % (self.name, self.entity.__name__,
                       self.target.__name__))

        for key_num, target_col in enumerate(target_columns):
            if self.field:
                col = self.field[key_num]
                if isinstance( col, Field ):
                    col.create_col()
                    col = col.column
            else:
                if self.colname:
                    colname = self.colname[key_num]
                else:
                    colname = options.FKCOL_NAMEFORMAT % \
                              {'relname': self.name,
                               'key': target_col.key}

                # We can't add the column to the table directly as the
                # table might not be created yet.
                col = schema.Column( colname, 
                                     target_col.type,
                                     **self.column_kwargs )

                # If the column name was specified, and it is the same as
                # this property's name, there is going to be a conflict.
                # Don't allow this to happen.
                if col.key == self.name:
                    raise ValueError(
                             "ManyToOne named '%s' in '%s' conficts "
                             " with the column of the same name. "
                             "You should probably define the foreign key "
                             "field manually and use the 'field' "
                             "argument on the ManyToOne relationship"
                             % (self.name, self.entity.__name__))
                source_desc.add_column( self.column_kwargs.get( 'key', colname ), col )

            # Build the list of local columns which will be part of
            # the foreign key
            self.foreign_key.append(col)

            # Store the names of those columns
            fk_colnames.append(col.key)

            # Build the list of column "paths" the foreign key will
            # point to
            fk_refcols.append("%s.%s" % \
                              (target_table.fullname, target_col.key))

            # Build up the primary join. This is needed when you have
            # several ManyToOne relationships between two objects
            self.primaryjoin_clauses.append(col == target_col)

            if 'name' not in self.constraint_kwargs:
                # In some databases (at least MySQL) the constraint name needs
                # to be unique for the whole database, instead of per table.
                fk_name = None
                self.constraint_kwargs['name'] = fk_name

            constraint =schema.ForeignKeyConstraint( fk_colnames, fk_refcols,
                                                     **self.constraint_kwargs )
            source_desc.add_constraint( constraint )

    def get_prop_kwargs(self):
        kwargs = {'uselist': False}

        if self.entity.table is self.target_table:
            # this is needed because otherwise SA has no way to know what is
            # the direction of the relationship since both columns present in
            # the primaryjoin belong to the same table. In other words, it is
            # necessary to know if this particular relation
            # is the many-to-one side, or the one-to-xxx side. The foreignkey
            # doesn't help in this case.
            kwargs['remote_side'] = \
                [col for col in self.target_table.primary_key.columns]

        if self.primaryjoin_clauses:
            kwargs['primaryjoin'] = sql.and_(*self.primaryjoin_clauses)

        kwargs.update(self.kwargs)

        return kwargs
    
    def match_type_of(self, other):
        return isinstance(other, (OneToMany, OneToOne))    
    
    @property
    def target_table( self ):
        return class_mapper( self.target ).local_table    

class ManyToMany( Relationship ):
    uselist = True

    def __init__(self, of_kind, tablename=None,
                 local_colname=None, remote_colname=None,
                 ondelete=None, onupdate=None,
                 table=None, schema=None,
                 filter=None,
                 table_kwargs=None,
                 *args, **kwargs):
        self.user_tablename = tablename

        if local_colname and not isinstance(local_colname, list):
            local_colname = [local_colname]
        self.local_colname = local_colname or []
        if remote_colname and not isinstance(remote_colname, list):
            remote_colname = [remote_colname]
        self.remote_colname = remote_colname or []

        self.ondelete = ondelete
        self.onupdate = onupdate

        self.table = table
        self.schema = schema

        self.filter = filter
        if filter is not None:
            # We set viewonly to True by default for filtered relationships,
            # unless manually overridden.
            if 'viewonly' not in kwargs:
                kwargs['viewonly'] = True

        self.table_kwargs = table_kwargs or {}

        self.primaryjoin_clauses = []
        self.secondaryjoin_clauses = []

        super(ManyToMany, self).__init__(of_kind, *args, **kwargs)

    def column_format( self, data ):
        return options.M2MCOL_NAMEFORMAT( data )
    
    def match_type_of(self, other):
        return isinstance(other, ManyToMany)

    def create_tables(self):
        if self.table is not None:
            if 'primaryjoin' not in self.kwargs or \
               'secondaryjoin' not in self.kwargs:
                self._build_join_clauses()
            assert self.inverse is None or self.inverse.table is None or \
                   self.inverse.table is self.table
            return

        if self.inverse:
            inverse = self.inverse
            if inverse.table is not None:
                self.table = inverse.table
                self.primaryjoin_clauses = inverse.secondaryjoin_clauses
                self.secondaryjoin_clauses = inverse.primaryjoin_clauses
                return

            assert not inverse.user_tablename or not self.user_tablename or \
                   inverse.user_tablename == self.user_tablename
            assert not inverse.remote_colname or not self.local_colname or \
                   inverse.remote_colname == self.local_colname
            assert not inverse.local_colname or not self.remote_colname or \
                   inverse.local_colname == self.remote_colname
            assert not inverse.schema or not self.schema or \
                   inverse.schema == self.schema
            assert not inverse.table_kwargs or not self.table_kwargs or \
                   inverse.table_kwargs == self.table_kwargs

            self.user_tablename = inverse.user_tablename or self.user_tablename
            self.local_colname = inverse.remote_colname or self.local_colname
            self.remote_colname = inverse.local_colname or self.remote_colname
            self.schema = inverse.schema or self.schema
            self.local_colname = inverse.remote_colname or self.local_colname

        # compute table_kwargs
        complete_kwargs = options.options_defaults['table_options'].copy()
        complete_kwargs.update(self.table_kwargs)

        #needs: table_options['schema'], autoload, tablename, primary_keys,
        #entity.__name__, table_fullname
        e1_desc = self.entity._descriptor
        e2_desc = self.target._descriptor

        # First, we compute the name of the table. Note that some of the
        # intermediary variables are reused later for the constraint
        # names.

        # We use the name of the relation for the first entity
        # (instead of the name of its primary key), so that we can
        # have two many-to-many relations between the same objects
        # without having a table name collision.
        source_part = "%s_%s" % (e1_desc.tablename, self.name)

        # And we use only the name of the table of the second entity
        # when there is no inverse, so that a many-to-many relation
        # can be defined without an inverse.
        if self.inverse:
            target_part = "%s_%s" % (e2_desc.tablename, self.inverse.name)
        else:
            target_part = e2_desc.tablename

        if self.user_tablename:
            tablename = self.user_tablename
        else:
            # We need to keep the table name consistent (independant of
            # whether this relation or its inverse is setup first).
            if self.inverse and source_part < target_part:
                #XXX: use a different scheme for selfref (to not include the
                #     table name twice)?
                tablename = "%s__%s" % (target_part, source_part)
            else:
                tablename = "%s__%s" % (source_part, target_part)
        # We pre-compute the names of the foreign key constraints
        # pointing to the source (local) entity's table and to the
        # target's table

        # In some databases (at least MySQL) the constraint names need
        # to be unique for the whole database, instead of per table.
        source_fk_name = "%s_fk" % source_part
        if self.inverse:
            target_fk_name = "%s_fk" % target_part
        else:
            target_fk_name = "%s_inverse_fk" % source_part

        columns = []
        constraints = []

        for num, desc, fk_name, rel, inverse, colnames, join_clauses in (
          (0, e1_desc, source_fk_name, self, self.inverse,
           self.local_colname, self.primaryjoin_clauses),
          (1, e2_desc, target_fk_name, self.inverse, self,
           self.remote_colname, self.secondaryjoin_clauses)):

            fk_colnames = []
            fk_refcols = []
            if colnames:
                assert len(colnames) == len(desc.primary_keys)
            else:
                # The data generated here will be fed to the M2M column
                # formatter to generate the name of the columns of the
                # intermediate table for *one* side of the relationship,
                # that is, from the intermediate table to the current
                # entity, as stored in the "desc" variable.
                data = {# A) relationships info

                        # the name of the rel going *from* the entity
                        # we are currently generating a column pointing
                        # *to*. This is generally *not* what you want to
                        # use. eg in a "Post" and "Tag" example, with
                        # relationships named 'tags' and 'posts', when
                        # creating the columns from the intermediate
                        # table to the "Post" entity, 'relname' will
                        # contain 'tags'.
                        'relname': rel and rel.name or 'inverse',

                        # the name of the inverse relationship. In the
                        # above example, 'inversename' will contain
                        # 'posts'.
                        'inversename': inverse and inverse.name
                                               or 'inverse',
                        # is A == B?
                        'selfref': e1_desc is e2_desc,
                        # provided for backward compatibility, DO NOT USE!
                        'num': num,
                        # provided for backward compatibility, DO NOT USE!
                        'numifself': e1_desc is e2_desc and str(num + 1)
                                                        or '',
                        # B) target information (from the perspective of
                        #    the intermediate table)
                        'target': desc.entity,
                        'entity': desc.entity.__name__.lower(),
                        'tablename': desc.tablename,

                        # C) current (intermediate) table name
                        'current_table': tablename
                       }
                colnames = []
                for pk_col in desc.primary_keys:
                    data.update(key=pk_col.key)
                    colnames.append(self.column_format(data))

            for pk_col, colname in zip(desc.primary_keys, colnames):
                col = schema.Column(colname, pk_col.type, primary_key=True)
                columns.append(col)

                # Build the list of local columns which will be part
                # of the foreign key.
                fk_colnames.append(colname)

                # Build the list of column "paths" the foreign key will
                # point to
                target_path = "%s.%s" % (desc.table_fullname, pk_col.key)
                fk_refcols.append(target_path)

                # Build join clauses (in case we have a self-ref)
                if self.entity is self.target:
                    join_clauses.append(col == pk_col)

            onupdate = rel and rel.onupdate
            ondelete = rel and rel.ondelete

            #FIXME: fk_name is misleading
            constraints.append(
                schema.ForeignKeyConstraint(fk_colnames, fk_refcols,
                                            name=fk_name, onupdate=onupdate,
                                            ondelete=ondelete))

        args = columns + constraints
        self.table = schema.Table( tablename, e1_desc.metadata,
                                   *args, **complete_kwargs)

    def _build_join_clauses(self):
        # In the case we have a self-reference, we need to build join clauses
        if self.entity is self.target:
            if not self.local_colname and not self.remote_colname:
                raise Exception(
                    "Self-referential ManyToMany "
                    "relationships in autoloaded entities need to have at "
                    "least one of either 'local_colname' or 'remote_colname' "
                    "argument specified. The '%s' relationship in the '%s' "
                    "entity doesn't have either."
                    % (self.name, self.entity.__name__))

            self.primaryjoin_clauses, self.secondaryjoin_clauses = \
                _get_join_clauses(self.table,
                                  self.local_colname, self.remote_colname,
                                  self.entity.table)

    def get_prop_kwargs(self):
        kwargs = {'secondary': self.table,
                  'uselist': self.uselist}

        if self.filter:
            # we need to make a copy of the joinclauses
            secondaryjoin_clauses = self.secondaryjoin_clauses[:] + \
                                    [self.filter(self.target.table.c)]
        else:
            secondaryjoin_clauses = self.secondaryjoin_clauses

        if self.target is self.entity or self.filter:
            kwargs['primaryjoin'] = sql.and_(*self.primaryjoin_clauses)
            kwargs['secondaryjoin'] = sql.and_(*secondaryjoin_clauses)

        kwargs.update(self.kwargs)

        return kwargs

    def is_inverse(self, other):
        return super(ManyToMany, self).is_inverse(other) and \
               (self.user_tablename == other.user_tablename or
                (not self.user_tablename and not other.user_tablename))
    
class belongs_to( ClassMutator ):

    def process( self, entity_dict, name, *args, **kwargs ):
        entity_dict[ name ] = ManyToOne( *args, **kwargs )

class has_one( ClassMutator ):

    def process( self, entity_dict, name, *args, **kwargs ):
        entity_dict[ name ] = OneToOne( *args, **kwargs )

class has_many( ClassMutator ):
    
    def process( self, entity_dict, name, *args, **kwargs ):
        entity_dict[ name ] = OneToMany( *args, **kwargs )

class has_and_belongs_to_many( ClassMutator ):

    def process( self, entity_dict, name, *args, **kwargs ):
        entity_dict[ name ] = ManyToMany( *args, **kwargs )
        
def _get_join_clauses( local_table, local_cols1, local_cols2, target_table ):
    primary_join, secondary_join = [], []
    cols1 = local_cols1[:]
    cols1.sort()
    cols1 = tuple(cols1)

    if local_cols2 is not None:
        cols2 = local_cols2[:]
        cols2.sort()
        cols2 = tuple(cols2)
    else:
        cols2 = None

    # Build a map of fk constraints pointing to the correct table.
    # The map is indexed on the local col names.
    constraint_map = {}
    for constraint in local_table.constraints:
        if isinstance(constraint, schema.ForeignKeyConstraint):
            use_constraint = True
            fk_colnames = []

            # if all columns point to the correct table, we use the constraint
            #TODO: check that it contains as many columns as the pk of the
            #target entity, or even that it points to the actual pk columns
            for fk in constraint.elements:
                if fk.references(target_table):
                    # local column key
                    fk_colnames.append(fk.parent.key)
                else:
                    use_constraint = False
            if use_constraint:
                fk_colnames.sort()
                constraint_map[tuple(fk_colnames)] = constraint

    # Either the fk column names match explicitely with the columns given for
    # one of the joins (primary or secondary), or we assume the current
    # columns match because the columns for this join were not given and we
    # know the other join is either not used (is None) or has an explicit
    # match.

#TODO: rewrite this. Even with the comment, I don't even understand it myself.
    for cols, constraint in six.iteritems(constraint_map):
        if cols == cols1 or (cols != cols2 and
                             not cols1 and (cols2 in constraint_map or
                                            cols2 is None)):
            join = primary_join
        elif cols == cols2 or (cols2 == () and cols1 in constraint_map):
            join = secondary_join
        else:
            continue
        for fk in constraint.elements:
            join.append(fk.parent == fk.column)
    return primary_join, secondary_join

