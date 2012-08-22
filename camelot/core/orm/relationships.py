from sqlalchemy import schema
from sqlalchemy.orm import relationship, backref

from . properties import DeferredProperty
from . entity import EntityBase

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
        
    def _config(self, cls, mapper, key):
        """Create a Column with ForeignKey as well as a relationship()."""

        super( Relationship, self )._config( cls, mapper, key )

        pk_target, fk_target = self._get_pk_fk(cls, self.target)
        pk_table = pk_target.__table__
        pk_col = list(pk_table.primary_key)[0]
        
        if pk_target == self.target:
            column_kwargs = self.kwargs.pop( 'column_kwargs', {} )
            column_kwargs.setdefault( 'index', True )
            fk_colname = '%s_%s'%(key, pk_col.key)
            fk_col = schema.Column( fk_colname, pk_col.type, schema.ForeignKey(pk_col), **column_kwargs )
            setattr(fk_target, fk_colname, fk_col)

        #self.kwargs.setdefault( 'collection_class', set )
        self.create_properties()
        
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
    
    def create_properties( self ):
        if self.property or self.backref:
            return

        kwargs = self.get_prop_kwargs()
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
    
    def match_type_of(self, other):
        return isinstance(other, ManyToOne)
    
    def get_prop_kwargs(self):
        kwargs = {'uselist': self.uselist}
        kwargs.update( self.kwargs )
        return kwargs    
    
class OneToMany( OneToOne ):
    """Generates a one to many relationship."""
    uselist = True

    def _get_pk_fk( self, cls, target_cls ):
        return cls, target_cls

class ManyToOne( Relationship ):
    """Generates a many to one relationship."""

    process_order = 1
    
    def _get_pk_fk( self, cls, target_cls ):
        return target_cls, cls
    
    def get_prop_kwargs( self ):
        kwargs = {'uselist': False}
        kwargs.update( self.kwargs )
        return kwargs    
    
    def match_type_of(self, other):
        return isinstance(other, (OneToMany, OneToOne))    

class ManyToMany( DeferredProperty ):
    """Generates a many to many relationship."""

    process_order = 3
    
    def __init__( self, target, tablename, local_colname, remote_colname, **kw ):
        self.target = target
        self.tablename = tablename
        self.local = local_colname
        self.remote = remote_colname
        self.kw = kw

    def _config(self, cls, mapper, key):
        """Create an association table between parent/target
        as well as a relationship()."""

        target_cls = cls._decl_class_registry[self.target]
        local_pk = list(cls.__table__.primary_key)[0]
        target_pk = list(target_cls.__table__.primary_key)[0]
        t = schema.Table(
                self.tablename,
                cls.metadata,
                schema.Column(self.local, schema.ForeignKey(local_pk), primary_key=True),
                schema.Column(self.remote, schema.ForeignKey(target_pk), primary_key=True),
                keep_existing=True
            )
        rel = relationship(target_cls,
                secondary=t,
                # use list instead of set because collection proxy does not
                # work with sets
                collection_class=self.kw.get('collection_class', list)
            )
        setattr(cls, key, rel)
        self._setup_reverse(key, rel, target_cls)
        
    def match_type_of(self, other):
        return isinstance(other, ManyToMany) 
    
# to be defined
def belongs_to():
    raise NotImplementedError()

def has_one():
    raise NotImplementedError()

def has_many():
    raise NotImplementedError()

def has_and_belongs_to_many():
    raise NotImplementedError()
