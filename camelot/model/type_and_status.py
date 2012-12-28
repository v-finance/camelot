#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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
"""
Convenience classes to give entities a status, and create the needed status
tables for each entity.

"""
import datetime

from sqlalchemy import orm, sql, schema, types
from sqlalchemy.ext import hybrid

from camelot.model.authentication import end_of_times
from camelot.admin.action import Action
from camelot.admin.entity_admin import EntityAdmin
from camelot.types import Enumeration
from camelot.core.orm.properties import Property
from camelot.core.orm import Entity
from camelot.core.utils import ugettext_lazy as _
from camelot.view import action_steps

class StatusType( object ):
    """Mixin class to describe the different statuses an
    object can have
    """

    code = schema.Column( types.Unicode(10), index = True, nullable = False, unique = True )
    description = schema.Column( types.Unicode( 40 ), index = True )

    def __unicode__( self ):
	return self.code or ''

    class Admin( EntityAdmin ):
	list_display = ['code', 'description']
	form_display = ['code', 'description']
	#verbose_name = statusable_entity + ' Status Type'
	#if verbose_entity_name is not None:
	    #verbose_name = verbose_entity_name + ' Status Type'	
	
class StatusHistory( object ):
    """Mixin class to track the history of the status an object
    has.
    
    .. attribute:: status_datetime For statuses that occur at a specific point in time
    .. attribute:: status_from_date For statuses that require a date range
    .. attribute:: from_date When a status was enacted or set
    """
    
    status_datetime = schema.Column( types.Date, nullable = True )
    status_from_date = schema.Column( types.Date, nullable = True )
    status_thru_date = schema.Column( types.Date, nullable = True )
    from_date = schema.Column( types.Date, nullable = False, default = datetime.date.today )
    thru_date = schema.Column( types.Date, nullable = False, default = end_of_times )

    #status_for = ManyToOne( statusable_entity, #required = True,
                             #ondelete = 'cascade', onupdate = 'cascade' )
    
    #if not enumeration:
	#classified_by = ManyToOne( t3_status_type_name, required = True,
                                   #ondelete = 'cascade', onupdate = 'cascade' )
    #else:
	#classified_by = Field(Enumeration(enumeration), required=True, index=True)

    class Admin( EntityAdmin ):
	#verbose_name = statusable_entity + ' Status'
	#verbose_name_plural = statusable_entity + ' Statuses'
	list_display = ['status_from_date', 'status_thru_date', 'classified_by']
	#verbose_name = statusable_entity + ' Status'
	#if verbose_entity_name is not None:
	    #verbose_name = verbose_entity_name + ' Status'

    def __unicode__( self ):
	return u'Status'

class Status( Property ):
    """Property that adds a related status table(s) to an `Entity`.
    
    These additional entities are created :
    
     * a `StatusType` this is the list of possible statuses an entity can have.
       If the `enumeration` parameter is used at construction, no such entity is
       created, and the list of possible statuses is limited to this enumeration.
       
     * a `StatusHistory` is the history of statusses an object has had.  The Status
       History refers to which `StatusType` was valid at a certain point in time.
       
    :param enumeration: if this parameter is used, no `StatusType` entity is created, 
        but the status type is described by the enumeration.  This parameter should
	be a list of all possible statuses the entity can have ::
	
	    enumeration = [(1, 'draft'), (2,'ready')]
    """
    
    def __init__( self, enumeration = None ):
	super( Status, self ).__init__()
	self.property = None
	self.enumeration = enumeration
	    
    def attach( self, entity, name ):
	super( Status, self ).attach( entity, name )
	assert entity != Entity
	
	status_name = entity.__name__.lower() + '_status'
	status_type_name = entity.__name__.lower() + '_status_type'
	
	if self.enumeration == None:
	    
	    class EntityStatusType( StatusType, entity._descriptor.entity_base ):
		__tablename__ = status_type_name
	    
	    class EntityStatusHistory( StatusHistory, entity._descriptor.entity_base ):
		__tablename__ = status_name
		classified_by_id = schema.Column( types.Integer(), schema.ForeignKey( EntityStatusType.id,
		                                                                      ondelete = 'cascade', 
		                                                                      onupdate = 'cascade'), nullable = False )
		classified_by = orm.relationship( EntityStatusType )
	    
	    self.status_type = EntityStatusType
	    setattr( entity, '_%s_type'%name, self.status_type )

	else:
	    
	    class EntityStatusHistory( StatusHistory, entity._descriptor.entity_base ):
		__tablename__ = status_name
		classified_by = schema.Column( Enumeration( self.enumeration ), 
		                               nullable=False, index=True )
	    
	self.status_history = EntityStatusHistory
	setattr( entity, '_%s_history'%name, self.status_history )
	
    def create_non_pk_cols( self ):
	table = orm.class_mapper( self.entity ).local_table
	for col in table.primary_key.columns:
	    col_name = u'status_for_%s'%col.name
	    if not hasattr( self.status_history, col_name ):
		constraint = schema.ForeignKey( col,
		                                ondelete = 'cascade', 
		                                onupdate = 'cascade')
		column = schema.Column( types.Integer(), constraint, nullable = False )
	        setattr( self.status_history, col_name, column )
	    
    def create_properties( self ):
	if not self.property:
	    self.property = orm.relationship( self.entity, backref = self.name )
	    self.status_history.status_for = self.property
    
class StatusMixin( object ):
	
    def get_status_from_date( self, classified_by ):
	"""
	:param classified_by: the status for which to get the last from date
	:return: the last date at which the status changed to `classified_by`, None if no such
	    change occured yet
	"""
	status_histories = [status_history for status_history in self.status if status_history.classified_by == classified_by]
	if len( status_histories ):
	    status_histories.sort( key = lambda status_history:status_history.from_date, reverse = True )
	    return status_histories[0].from_date
	
    def get_status_history_at( self, status_date = None ):
	"""
	Get the StatusHistory valid at status_date
	
	:param status_date: the date at which the status history should
	    be valid.  Use today if None was given.
	:return: a StatusHistory object or None if no valid status was
	    found
	"""
	if status_date == None:
	    status_date = datetime.date.today()
	for status_history in self.status:
	    if status_history.status_from_date <= status_date and status_history.status_thru_date >= status_date:	
		return status_history	

    @staticmethod
    def current_status_query( status_history, status_class ):
	"""
	:param status_history: the class or columns that represents the status history
	:param status_class: the class or columns of the class that have a status
	:return: a select statement that looks for the current status of the status_class
	"""
	return sql.select( [status_history.classified_by],
                          whereclause = sql.and_( status_history.status_for_id == status_class.id,
                                                  status_history.status_from_date <= sql.functions.current_date(),
                                                  status_history.status_thru_date >= sql.functions.current_date() ),
                          from_obj = [status_history.table] ).order_by(status_history.id.desc()).limit(1)
		    
    @hybrid.hybrid_property
    def current_status( self ):
	status_history = self.get_status_history_at()
	if status_history != None:
	    return status_history.classified_by
	
    @current_status.expression
    def current_status( cls ):
	return StatusMixin.current_status_query( cls._status_history, cls ).label( 'current_status' )
    
    def change_status( self, new_status, status_from_date=None, status_thru_date=end_of_times() ):
	from sqlalchemy import orm
	if not status_from_date:
	    status_from_date = datetime.date.today()
	mapper = orm.class_mapper(self.__class__)
	status_property = mapper.get_property('status')
	status_type = status_property.mapper.class_
	old_status = status_type.query.filter( sql.and_( status_type.status_for == self,
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
	orm.object_session( self ).flush()
	        
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

class ChangeStatus( Action ):
    """
    An action that changes the status of an object
    :param new_status: the new status of the object
    :param verbose_name: the name of the action
    :return: a :class:`camelot.admin.action.Action` object that changes
	the status of a selection to the new status
    """	
    
    def __init__( self, new_status, verbose_name = None ):
	self.verbose_name = verbose_name or _(new_status)
	self.new_status = new_status
	
    def model_run( self, model_context ):
	for obj in model_context.get_selection():
	    obj.change_status( self.new_status )
	yield action_steps.FlushSession( model_context.session )
