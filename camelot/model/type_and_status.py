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
Convenience classes to give entities a status, and create the needed related
status tables for each entity.  Status changes are tracked in a related status
history table.

Possible statuses can be defined as an enumeration or as a reference to a
table of related statuses.

Enumeration
-----------

In this setup there is a limited number of possible statuses an object can
have, this cannot be changed by the user of the application.

.. literalinclude:: ../../test/test_model.py
   :start-after: begin status enumeration definition
   :end-before: end status enumeration definition

Related status type table
-------------------------

In this setup, an additional table with possible status types is created.
The user of the application can modify this table and create additional
statuses as needed.

"""
import datetime

import six

from sqlalchemy import orm, sql, schema, types, inspection
from sqlalchemy.ext import hybrid

from camelot.admin.action import list_filter
from camelot.model.authentication import end_of_times
from camelot.admin.action import Action
from camelot.admin.entity_admin import EntityAdmin
from camelot.types import Enumeration, PrimaryKey
from camelot.core.orm.properties import EntityBuilder
from camelot.core.orm import Entity
from camelot.core.item_model.proxy import AbstractModelFilter
from camelot.core.exception import UserException
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.view import action_steps

class TypeMixin(object):
    """Mixin class to describe the different types of objects
    
    .. attribute:: code
       
        the code for this type that will be shown in the drop down lists
       
    .. attribute:: description
       
        a longer description that will be shown in tooltips
    """

    code = schema.Column(types.Unicode(10), index=True, nullable=False)
    description = schema.Column(types.Unicode( 40 ), index = True)

    def __str__(self):
        return self.code or u''

class StatusTypeMixin(TypeMixin):
    """Mixin class to describe the different statuses an object can have
    """
    pass

class TypeAdmin(EntityAdmin):
    list_display = ['code', 'description']
    form_display = ['code', 'description']
    field_attributes = {'code': {'name': _('Code')},
                        'description': {'name': _('Description')}
                        }

class StatusTypeAdmin(TypeAdmin):
    pass

class StatusHistory( object ):
    """Mixin class to track the history of the status an object
    has.

    .. attribute:: status_datetime For statuses that occur at a specific point in time
    .. attribute:: status_from_date For statuses that require a date range
    .. attribute:: from_date When a status was enacted or set
    """

    status_datetime = schema.Column(types.Date, nullable=True, index=True)
    status_from_date = schema.Column(types.Date, nullable=True, index=True)
    status_thru_date = schema.Column(types.Date, nullable=True, index=True)
    from_date = schema.Column(types.Date, nullable=False, index=True,
                              default=datetime.date.today)
    thru_date = schema.Column(types.Date, nullable=False, index=True,
                              default=end_of_times)


    def __str__( self ):
        return six.text_type(self.classified_by or u'')

    def sort_key(self):
        """Key to be used to sort the status histories to get a single
        status history at a specific date.

        The default order is :

        - if status_from_date of history a comes before history b,
          history a comes before history b

        - if history a has a primary key and history b has no primary key,
          history a comes before history b

        - if the primary key of history a is smaller than the primary key
          of history b, history a comes before history b.

        This ensures that the order matches the one of the default sql
        queries, but it allows changing the status without assigning
        primary keys yet.
        """
        state = inspection.inspect(self)
        return (self.status_from_date, state.has_identity, state.identity)

class StatusHistoryAdmin( EntityAdmin ):
    list_display = ['status_from_date', 'status_thru_date', 'classified_by']
    field_attributes = {'from_date': {'name': _('From date')},
                        'thru_date': {'name': _('Thru date')},
                        'status_from_date': {'editable': False},
                        'status_thru_date': {'editable': False},
                        'classified_by': {'editable': False},
                        }

    def get_depending_objects(self, obj):
        if obj.status_for is not None:
            yield obj.status_for
    
    def get_related_toolbar_actions(self, toolbar_area, direction):
        return []

class Status( EntityBuilder ):
    """EntityBuilder that adds a related status table(s) to an `Entity`.

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

    :param status_history_table: the tablename to use to store the status
        history

    :param status_type_table: the tablename to use to store the status types
    """

    def __init__( self, enumeration = None, 
                  status_history_table = None, status_type_table=None ):
        super( Status, self ).__init__()
        self.property = None
        self.enumeration = enumeration
        self.status_history_table = status_history_table
        self.status_type_table = status_type_table

    def attach( self, entity, name ):
        super( Status, self ).attach( entity, name )
        assert entity != Entity

        if self.status_history_table==None:
            self.status_history_table = entity.__name__.lower() + '_status'
        if self.status_type_table==None:
            self.status_type_table = entity.__name__.lower() + '_status_type'

        status_history_admin = type( entity.__name__ + 'StatusHistoryAdmin',
                                     ( StatusHistoryAdmin, ),
                                     { 'verbose_name':_(entity.__name__ + ' Status'),
                                       'verbose_name_plural':_(entity.__name__ + ' Statuses'), } )

        # use `type` instead of `class`, to give status type and history
        # classes a specific name, so these classes can be used whithin the
        # memento and the fixture module
        if self.enumeration is None:

            status_type_admin = type( entity.__name__ + 'StatusType',
                                      ( StatusTypeAdmin, ),
                                      { 'verbose_name':_(entity.__name__ + ' Status'),
                                        'verbose_name_plural':_(entity.__name__ + ' Statuses'), } )

            status_type = type( entity.__name__ + 'StatusType', 
                                (StatusTypeMixin, entity._descriptor.get_top_entity_base(),),
                                { '__tablename__':self.status_type_table,
                                  'Admin':status_type_admin } )

            foreign_key = schema.ForeignKey( status_type.id,
                                             ondelete = 'cascade', 
                                             onupdate = 'cascade')

            status_history = type( entity.__name__ + 'StatusHistory',
                                   ( StatusHistory, entity._descriptor.get_top_entity_base(), ),
                                   {'__tablename__':self.status_history_table,
                                    'classified_by_id':schema.Column(
                                        PrimaryKey(),
                                        foreign_key,
                                        nullable=False,
                                        index=True),
                                    'classified_by':orm.relationship( status_type ),
                                    'Admin':status_history_admin, } )
        else:
            status_type = None
            status_history = type( entity.__name__ + 'StatusHistory',
                                   ( StatusHistory, entity._descriptor.get_top_entity_base(), ),
                                   {'__tablename__':self.status_history_table,
                                    'classified_by':schema.Column(
                                        Enumeration( self.enumeration ), 
                                        nullable=False,
                                        index=True
                                        ),
                                    'Admin':status_history_admin,} )
            setattr( entity, '_%s_enumeration'%name, self.enumeration )

        self.status_type = status_type
        self.status_history = status_history
        setattr( entity, '_%s_type'%name, status_type )
        setattr( entity, '_%s_history'%name, self.status_history )

    def create_tables(self):
        self.status_history.__table__.schema = self.entity.__table__.schema
        self.status_history.__table__.info = self.entity.__table__.info.copy()
        if self.status_type is not None:
            self.status_type.__table__.schema = self.entity.__table__.schema
            self.status_type.__table__.info = self.entity.__table__.info.copy()

    def create_non_pk_cols( self ):
        table = orm.class_mapper( self.entity ).local_table
        for col in table.primary_key.columns:
            col_name = u'status_for_%s'%col.name
            if not hasattr( self.status_history, col_name ):
                constraint = schema.ForeignKey(col,
                                               ondelete = 'cascade', 
                                               onupdate = 'cascade')
                column = schema.Column(PrimaryKey(),
                                       constraint,
                                       nullable=False,
                                       index=True)
                setattr( self.status_history, col_name, column )

    def create_properties( self ):
        if not self.property:
            backref = orm.backref(self.name, cascade='all, delete, delete-orphan')
            self.property = orm.relationship(self.entity, backref = backref, enable_typechecks=False)
            self.status_history.status_for = self.property

class StatusMixin( object ):
    """This class adds additional methods to classes that have a status.
    Such as methods to retrieve and modify the status.
    """

    def get_status_from_date( self, classified_by ):
        """
        :param classified_by: the status for which to get the last `status_from_date`
        :return: the last date at which the status changed to `classified_by`, None if no such
            change occured yet
        """
        status_histories = [status_history for status_history in self.status if status_history.classified_by == classified_by]
        if len(status_histories):
            status_histories.sort(key=self._status_history.sort_key,
                                  reverse=True)
            return status_histories[0].status_from_date

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
        status_histories = list(self.status)
        status_histories.sort(key=self._status_history.sort_key,
                              reverse=True)
        for status_history in status_histories:
            if status_history.status_from_date <= status_date and status_history.status_thru_date >= status_date:
                return status_history

    @staticmethod
    def current_status_query( status_history, status_class ):
        """
        :param status_history: the class or columns that represents the status history
        :param status_class: the class or columns of the class that have a status
        :return: a select statement that looks for the current status of the status_class
        """
        SH = orm.aliased(status_history)
        return sql.select( [SH.classified_by],
                           whereclause = sql.and_( SH.status_for_id == status_class.id,
                                                   SH.status_from_date <= sql.functions.current_date(),
                                                   SH.status_thru_date >= sql.functions.current_date() ),
                           ).order_by(SH.status_from_date.desc(), SH.id.desc()).limit(1)

    @hybrid.hybrid_property
    def current_status( self ):
        status_history = self.get_status_history_at()
        if status_history != None:
            return status_history.classified_by

    @current_status.expression
    def current_status( cls ):
        return StatusMixin.current_status_query( cls._status_history, cls ).label( 'current_status' )

    def change_status(self, new_status, 
                      status_from_date=None,
                      status_thru_date=end_of_times(),
                      session=None):
        """
        Change the status of this object.  This method does not start a
        transaction, but it is advised to run this method in a transaction.
        """
        if not status_from_date:
            status_from_date = datetime.date.today()
        history_type = self._status_history
        session = session or orm.object_session( self )
        old_status_query = session.query(history_type)
        old_status_query = old_status_query.filter(
            sql.and_(history_type.status_for==self,
                     history_type.status_from_date <= status_from_date,
                     history_type.status_thru_date >= status_from_date)
        )
        if self.id is not None:
            new_thru_date = datetime.date.today() - datetime.timedelta(days=1)
            new_status_thru_date = status_from_date - datetime.timedelta(days=1)
            for old_status in old_status_query.yield_per(10):
                old_status.thru_date = new_thru_date
                old_status.status_thru_date = new_status_thru_date
        new_status = history_type(status_for = self,
                                  classified_by = new_status,
                                  status_from_date = status_from_date,
                                  status_thru_date = status_thru_date,
                                  from_date = datetime.date.today(),
                                  thru_date = end_of_times())
        session.flush()

class ChangeStatus( Action ):
    """
    An action that changes the status of an object within a transaction
    
    :param new_status: the new status of the object
    :param verbose_name: the name of the action

    Before changing the status, the validity of the object will be checked.
    This state of the action does not depend on the validity of the object, as
    this might slow down list views too much.
    """

    def __init__( self, new_status, verbose_name = None ):
        self.verbose_name = verbose_name or _(new_status)
        self.new_status = new_status

    def before_status_change(self, model_context, obj):
        """
        Use this method to implement checks or actions that need to happen
        before the status is changed, but within the transaction
        """
        yield action_steps.UpdateProgress(text=_('Change status'))

    def after_status_change(self, model_context, obj):
        """
        Use this method to implement checks or actions that need to happen
        before the status is changed, but within the transaction
        """
        yield action_steps.UpdateProgress(text=_('Changed status'))

    def model_run(self, model_context, new_status=None):
        """
        :param new_status: overrule the new_status defined at the class level,
            this can be used when overwwriting the `model_run` method in a
            subclass
        """
        new_status = new_status or self.new_status
        validator = model_context.admin.get_validator()
        for obj in model_context.get_selection():
            for message in validator.validate_object(obj):
                raise UserException(message)
        with model_context.session.begin():
            for obj in model_context.get_selection():
                # the number of status changes as seen in the UI
                number_of_statuses = len(obj.status)
                history_type = obj._status_history
                history = model_context.session.query(history_type)
                history = history.filter(history_type.status_for==obj)
                history = history.with_for_update(nowait=True)
                history_count = sum(1 for _h in history.yield_per(10))
                if number_of_statuses != history_count:
                    if obj not in model_context.session.new:
                        model_context.session.expire(obj)
                    yield action_steps.UpdateObjects([obj])
                    raise UserException(_('Concurrent status change'),
                                        detail=_('Another user changed the status'),
                                        resolution=_('Try again if needed'))
                if obj.current_status != new_status:
                    for step in self.before_status_change(model_context, obj):
                        yield step
                    obj.change_status(new_status)
                    for step in self.after_status_change(model_context, obj):
                        yield step
                    yield action_steps.UpdateObjects([obj])
            yield action_steps.FlushSession(model_context.session)

class StatusFilter(list_filter.GroupBoxFilter, AbstractModelFilter):
    """
    Filter to be used in a table view to enable filtering on the status
    of an object.  This filter will display all available statuses, and as
    such, needs not to query the distinct values used in the database to
    build up it's widget.
    
    :param attribute: the attribute that holds the status
    """

    def decorate_query(self, query, values):
        if list_filter.All in values:
            return query
        if (len(values) == 0) and (self.exclusive==False):
            return query.filter(self.column==None)
        query = query.outerjoin(*self.joins)
        where_clauses = [self.column==v for v in values]
        query = query.filter(sql.or_(*where_clauses))
        return query

    def filter(self, it, value):
        """
        Allow the status filter to work on list of objects instead of
        queries.
        """
        if list_filter.All in value:
            for obj in it:
                yield obj
        elif len(value) > 0:
            today = datetime.date.today()
            for obj in it:
                for history in getattr(obj, self.attribute):
                    if history.status_from_date <= today <= history.status_thru_date:
                        if history.classified_by in value:
                            yield obj

    def get_entity_id(self, model_context):
        return model_context.admin.entity.id

    def get_state(self, model_context):
        state = Action.get_state(self, model_context)
        admin = model_context.admin
        self.attributes = admin.get_field_attributes(self.attribute)
        history_type = self.attributes['target']
        history_admin = admin.get_related_admin(history_type)
        classification_fa = history_admin.get_field_attributes('classified_by')

        target = classification_fa.get('target')
        if target is not None:
            choices = [(st, st.code) for st in target.query.all()]
        else:
            choices = classification_fa['choices']

        state.modes = []
        modes = []
        current_date = sql.functions.current_date()
        self.joins = (history_type, sql.and_(history_type.status_from_date <= current_date,
                                             history_type.status_for_id == self.get_entity_id(model_context),
                                             history_type.status_thru_date >= current_date)
                      )
        self.column = getattr(history_type, 'classified_by')

        for value, name in choices:
            mode = list_filter.FilterMode(
                value=value,
                verbose_name=name,
                checked=((self.default==value) or (self.exclusive==False))
            )
            modes.append(mode)

        if self.exclusive:
            all_mode = list_filter.FilterMode(value=list_filter.All,
                                              verbose_name=ugettext('All'),
                                              checked=(self.default==list_filter.All))
            modes.insert(0, all_mode)
        else:
            none_mode = list_filter.FilterMode(value=None,
                                               verbose_name=ugettext('None'),
                                               checked=True)
            modes.append(none_mode)

        state.modes = modes
        state.verbose_name = self.attributes['name']
        return state

class Type(EntityBuilder):
    """EntityBuilder that adds a related type table to an `Entity`.

    An additional `Type` entity is created, this is the list of possible types an
    entity can have.

    :param type_table: the tablename used to store the `Type` entity

    :param nullable: if the underlying column is nullable
    
    :param type_verbose_name: the verbose name of the `Type Entity`
    
    :param type_verbose_name_plural: the verbose plural name of the `Type Entity`
    """

    def __init__(self,
                 type_table=None,
                 nullable=False,
                 type_verbose_name=None,
                 type_verbose_name_plural=None,
                 ):
        super(Type, self ).__init__()
        self.property = None
        self.type_table = type_table
        self.nullable = nullable
        self.type_verbose_name = type_verbose_name
        self.type_verbose_name_plural = type_verbose_name_plural

    def attach( self, entity, name ):
        super(Type, self ).attach( entity, name )
        assert entity != Entity

        if self.type_table is None:
            self.type_table = entity.__tablename__ + '_type'

        # use `type` instead of `class`, to give status type and history
        # classes a specific name, so these classes can be used whithin the
        # memento and the fixture module

        type_verbose_name = self.type_verbose_name or _(entity.__name__ + ' Type')
        type_verbose_name_plural = self.type_verbose_name_plural or _(entity.__name__ + ' Type')
        
        type_admin = type( entity.__name__ + 'TypeAdmin',
                           ( TypeAdmin, ),
                           { 'verbose_name':  type_verbose_name,
                             'verbose_name_plural': type_verbose_name_plural, }
                           )

        type_entity = type( entity.__name__ + 'Type', 
                            (TypeMixin, entity._descriptor.get_top_entity_base(),),
                            { '__tablename__':self.type_table,
                              'Admin':type_admin }
                            )

        self.type_entity = type_entity
        setattr(entity, '_%s_type'%name, self.type_entity)

    def create_non_pk_cols( self ):
        table = orm.class_mapper(self.type_entity).local_table
        for col in table.primary_key.columns:
            col_name = u'%s_%s'%(self.name, col.name)
            if not hasattr(self.entity, col_name):
                constraint = schema.ForeignKey(col,
                                               ondelete = 'restrict', 
                                               onupdate = 'cascade')
                column = schema.Column(PrimaryKey(),
                                       constraint,
                                       index=True,
                                       nullable=self.nullable)
                setattr(self.entity, col_name, column )

    def create_properties( self ):
        if not self.property:
            self.property = orm.relationship(self.type_entity)
            setattr(self.entity, self.name, self.property)


class TypeFilter(list_filter.GroupBoxFilter):
    """
    Filter to be used in a table view to enable filtering on the type
    of an object.  This filter will display all available types, and as
    such, needs not to query the distinct values used in the database to
    build up it's widget.
    
    :param attribute: the attribute that holds the type
    """

    def decorate_query(self, query, values):
        if list_filter.All in values:
            return query
        if (len(values) == 0) and (self.exclusive==False):
            return query.filter(self.column==None)
        where_clauses = [self.column==v for v in values]
        query = query.filter(sql.or_(*where_clauses))
        return query

    def get_state(self, model_context):
        state = Action.get_state(self, model_context)
        admin = model_context.admin
        self.attributes = admin.get_field_attributes(self.attribute)
        type_type = self.attributes['target']

        choices = [(t, t.code) for t in type_type.query.all()]

        state.modes = []
        modes = []
        self.column = getattr(admin.entity, self.attribute)

        for value, name in choices:
            mode = list_filter.FilterMode(
                value=value,
                verbose_name=name,
                checked=(self.exclusive==False),
            )
            modes.append(mode)

        if self.exclusive:
            all_mode = list_filter.FilterMode(value=list_filter.All,
                                              verbose_name=ugettext('All'),
                                              checked=(self.default==list_filter.All))
            modes.insert(0, all_mode)
        else:
            none_mode = list_filter.FilterMode(value=None,
                                               verbose_name=ugettext('None'),
                                               checked=True)
            modes.append(none_mode)

        state.modes = modes
        state.verbose_name = self.attributes['name']
        return state

