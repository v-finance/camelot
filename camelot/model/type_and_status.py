#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================
'''

Created on Sep 25, 2009

@author: Erik De Rijcke

'''
import datetime

from elixir.entity import Entity, EntityMeta

from sqlalchemy.types import Date, Unicode
from sqlalchemy.sql import and_

from elixir.fields import Field
from elixir.options import using_options
from elixir.relationships import ManyToOne, OneToMany

from camelot.model.authentication import end_of_times
from camelot.admin.entity_admin import EntityAdmin
from camelot.types import Enumeration

#
# Global dict keeping track of which status class is used for which class
#
__status_classes__ = {}
__status_type_classes__ = {}

def get_status_class(cls_name):
    """
    :param cls_name: an Entity class name
    :return: the status class used for this entity
    """
    return __status_classes__[cls_name]

def get_status_type_class(cls_name):
    """
    :param cls_name: an Entity class name
    :return: the status type class used for this entity
    """
    return __status_type_classes__[cls_name]

def create_type_3_status_mixin(status_attribute):
    """Create a class that can be subclassed to provide a class that
    has a type 3 status with methods to manipulate and review its status
    :param status_attribute: the name of the type 3 status attribute
    """
    
    class Type3StatusMixin(object):

        @property
        def current_status(self):
            classified_by = None
            today = datetime.date.today()
            for status_history in self.status:
                if status_history.status_from_date<=today and status_history.status_thru_date>=today:
                    classified_by = status_history.classified_by
            return classified_by
    
        def change_status(self, new_status, status_from_date=None, status_thru_date=end_of_times()):
            from sqlalchemy import orm
            if not status_from_date:
                status_from_date = datetime.date.today()
            mapper = orm.class_mapper(self.__class__)
            status_property = mapper.get_property('status')
            status_type = status_property._get_target().class_
            old_status = status_type.query.filter( and_( status_type.status_for == self,
                                                         status_type.status_from_date <= status_from_date,
                                                         status_type.status_thru_date >= status_from_date ) ).first()
            if old_status != None:
                old_status.thru_date = datetime.date.today() - datetime.timedelta( days = 1 )
                old_status.status_thru_date = status_from_date - datetime.timedelta( days = 1 )
            new_status = status_type(    status_for = self,
                                         classified_by = new_status,
                                         status_from_date = status_from_date,
                                         status_thru_date = status_thru_date,
                                         from_date = datetime.date.today(),
                                         thru_date = end_of_times() )
            if old_status:
                self.query.session.flush( [old_status] )
            self.query.session.flush( [new_status] )        
        
    return Type3StatusMixin
    
def type_3_status( statusable_entity, metadata, collection, verbose_entity_name = None, enumeration=None ):
    '''
    Creates a new type 3 status related to the given entity
    :statusable_entity: A string referring to an entity.
    :enumeration: if this parameter is used, no status type Entity is created, but the status type is
    described by the enumeration.
    '''
    t3_status_name = statusable_entity + '_status'
    t3_status_type_name = statusable_entity + '_status_type'


    if not enumeration:
        
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
    
            code = Field( Unicode(10), index = True,
                          required = True, unique = True )
            description = Field( Unicode( 40 ), index = True )
    
            def __unicode__( self ):
                return self.code or ''
    
            class Admin( EntityAdmin ):
                list_display = ['code', 'description']
                form_display = ['code', 'description']
                verbose_name = statusable_entity + ' Status Type'
                if verbose_entity_name is not None:
                    verbose_name = verbose_entity_name + ' Status Type'

        __status_type_classes__[statusable_entity] = Type3StatusType
        
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
        
        if not enumeration:
            classified_by = ManyToOne( t3_status_type_name, required = True,
                                       ondelete = 'cascade', onupdate = 'cascade' )
        else:
            classified_by = Field(Enumeration(enumeration), required=True, index=True)

        class Admin( EntityAdmin ):
            verbose_name = statusable_entity + ' Status'
            verbose_name_plural = statusable_entity + ' Statuses'
            list_display = ['status_from_date', 'status_thru_date', 'classified_by']
            verbose_name = statusable_entity + ' Status'
            if verbose_entity_name is not None:
                verbose_name = verbose_entity_name + ' Status'

        def __unicode__( self ):
            return u'Status'

    __status_classes__[statusable_entity] = Type3Status
    
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
                verbose_name = verbose_entity_name + ' Type'

        def __unicode__( self ):
            return u'Type: %s' % ( self.description )

    return type_name


