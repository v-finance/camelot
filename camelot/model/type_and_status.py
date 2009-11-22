'''

Created on Sep 25, 2009

@author: Erik De Rijcke

'''
from elixir.entity import Entity, EntityMeta

from sqlalchemy.types import Date, Unicode
from elixir.fields import Field
from elixir.options import using_options
from elixir.relationships import ManyToOne, OneToMany
from camelot.model.authentication import end_of_times
from camelot.view.elixir_admin import EntityAdmin
from camelot.types import Code
import datetime

def type_3_status( statusable_entity, metadata, collection, verbose_entity_name = None ):
    '''
    Creates a new type 3 status related to the given entity
    .. statusable_entity:: A string referring to an entity.
    '''
    t3_status_name = statusable_entity + '_status'
    t3_status_type_name = statusable_entity + '_status_type'

    class Type3StatusTypeMeta( EntityMeta ):
        def __new__( cls, classname, bases, dictionary ):
            return EntityMeta.__new__( cls, t3_status_type_name,
                                 bases, dictionary )
        def __init__( self, classname, bases, dictionary ):
            EntityMeta.__init__( self, t3_status_type_name,
                                  bases, dictionary )

    class Type3StatusType( Entity, ):
        using_options( tablename = t3_status_type_name.lower(), metadata=metadata, collection=collection )
        __metaclass__ = Type3StatusTypeMeta

        code = Field( Code( parts = ['>AAAA'] ), index = True,
                           required = True, unique = True )
        description = Field( Unicode( 40 ), index = True )

        def __unicode__( self ):
            return 'Status type: %s : %s' % ( '.'.join( self.code ), self.description )

        class Admin( EntityAdmin ):
            list_display = ['code', 'description']
            verbose_name = statusable_entity + ' Status Type'
            if verbose_entity_name is not None:
                verbose_name = verbose_entity_name + ' Status Type'

    class Type3StatusMeta( EntityMeta ):
        def __new__( cls, classname, bases, dictionary ):
            return EntityMeta.__new__( cls, t3_status_name,
                                       bases, dictionary )
        def __init__( self, classname, bases, dictionary ):
            EntityMeta.__init__( self, t3_status_name,
                                 bases, dictionary )

    class Type3Status( Entity, ):
        """
        Status Pattern
        .. attribute:: status_datetime For statuses that occur at a specific point in time
        .. attribute:: status_from_date For statuses that require a date range
        .. attribute:: from_date When a status was enacted or set
        """
        using_options( tablename = t3_status_name.lower(), metadata=metadata, collection=collection )
        __metaclass__ = Type3StatusMeta

        status_datetime = Field( Date, required = False )
        status_from_date = Field( Date, required = False )
        status_thru_date = Field( Date, required = False )
        from_date = Field( Date, required = True, default = datetime.date.today )
        thru_date = Field( Date, required = True, default = end_of_times )

        status_for = ManyToOne( statusable_entity, #required = True,
                                 ondelete = 'cascade', onupdate = 'cascade' )
        classified_by = ManyToOne( t3_status_type_name, required = True,
                                   ondelete = 'cascade', onupdate = 'cascade' )

        class Admin( EntityAdmin ):
            verbose_name = statusable_entity + ' Status'
            verbose_name_plural = statusable_entity + ' Statuses'
            list_display = ['status_from_date', 'status_thru_date', 'classified_by']
            verbose_name = statusable_entity + ' Status'
            if verbose_entity_name is not None:
                verbose_name = verbose_entity_name + ' Status'

        def __unicode__( self ):
            return u'Status'

    return t3_status_name

def entity_type( typable_entity, metadata, collection, verbose_entity_name = None ):
    '''
    Creates a new type related to the given entity.
    .. typeable_entity:: A string referring to an entity.
    '''
    type_name = typable_entity + '_type'

    class TypeMeta( EntityMeta ):
        def __new__( cls, classname, bases, dictionary ):
            return EntityMeta.__new__( cls, type_name,
                                       bases, dictionary )
        def __init__( self, classname, bases, dictionary ):
            EntityMeta.__init__( self, type_name,
                                 bases, dictionary )

    class Type( Entity ):
        using_options( tablename = type_name.lower(), metadata=metadata, collection=collection )
        __metaclass__ = TypeMeta

        type_description_for = OneToMany( typable_entity )
        description = Field( Unicode( 48 ), required = True )

        class Admin( EntityAdmin ):
            verbose_name = typable_entity + ' Type'
            list_display = ['description', ]
            verbose_name = typable_entity + ' Type'
            if verbose_entity_name is not None:
                verbose_name = verbose_entity_name + ' Status'

        def __unicode__( self ):
            return u'Type: %s' % ( self.description )

    return type_name
