from sqlalchemy import schema, sql
from sqlalchemy.orm import relationship, backref, class_mapper

from . properties import DeferredProperty
from . entity import EntityBase
from . fields import Field
from . statements import ClassMutator
from . import options

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
            if isinstance( self.of_kind, basestring ):
                self._target = self.entity._decl_class_registry[self.of_kind]
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
                 field=None,
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
        if required is not None:
            column_kwargs['nullable'] = not required
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
                fk_name = options.CONSTRAINT_NAMEFORMAT % \
                          {'tablename': source_desc.tablename,
                           'colnames': '_'.join(fk_colnames)}
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
    for cols, constraint in constraint_map.iteritems():
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
