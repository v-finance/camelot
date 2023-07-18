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

from sqlalchemy import inspection, orm, schema, sql, types, util
from sqlalchemy.ext import hybrid
from sqlalchemy.ext.declarative import declared_attr

from ..admin.admin_route import register_list_actions
from ..admin.action import Action, list_filter
from ..admin.entity_admin import EntityAdmin
from ..core.exception import UserException
from ..core.item_model.proxy import AbstractModelFilter
from ..core.orm import Entity
from ..core.utils import ugettext, ugettext_lazy as _
from ..model.authentication import end_of_times
from ..types import Enumeration, PrimaryKey
from ..view import action_steps


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
        return str(self.classified_by or u'')

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
    
    @register_list_actions('_admin_route')
    def get_related_toolbar_actions(self, direction):
        return []

class WithStatus(object):
    """
    creates related Table/class: ls.__name__ + 'StatusHistory', this table has a column classified_by, that holds the status types.
    this table has a relationship with cls. The table has a primary key column: status_for_id, and the relationship is stored in status for.
    This relationship also defines a backref(on cls) named 'status'

    cls var 'status_types': Required, sets the status types for the classified_by column
    cls var  'status_history_table': Optional, sets the tablename for the history_table
    """
    
    status_types = None
    status_history_table = None

    @declared_attr
    def _status_history(cls):
        assert isinstance(cls.status_types, (util.OrderedProperties, list)), "This class '{}', should define its status_types enumeration types.".format(cls.__name__)
        assert hasattr(cls, 'id'), "This class '{}' hasn't got an id set. Make sure the id is defined and the name of the id is 'id'".format(cls.__name__)
        status_history_table = cls.__name__.lower() + '_status' if cls.status_history_table is None else cls.status_history_table
        status_history_admin = type(cls.__name__ + 'StatusHistoryAdmin', (StatusHistoryAdmin,),
                                    {'verbose_name': _(cls.__name__ + ' Status'),
                                     'verbose_name_plural': _(cls.__name__ + ' Statuses')})
        # the status types need to be a list of tuples (with strings) so we convert the OrderedProperties
        status_types = cls.status_types
        if isinstance(status_types, util.OrderedProperties):
            status_types = [(member.id, name) for name, member in cls.status_types.__members__.items()]
        status_history = type(cls.__name__ + 'StatusHistory', (Entity, StatusHistory),
                              {'__tablename__': status_history_table,
                               'classified_by': schema.Column(Enumeration(status_types), nullable=False, index=True ),
                               'Admin': status_history_admin})

        if hasattr(cls, '__table_args__'):
            table_args = cls.__table_args__
            if not isinstance(cls.__table_args__, dict):
                table_args = cls.__table_args__[-1]
            table_info = table_args.get('info')
            status_history.__table__.info = table_info.copy()
    
        status_history.status_for_id = schema.Column(PrimaryKey(), schema.ForeignKey(cls.id, ondelete='cascade', onupdate='cascade'),
                                                     nullable=False, index=True)

        status_history.status_for = orm.relationship(cls, backref=orm.backref('status', cascade='all, delete, delete-orphan'), enable_typechecks=False)
        return status_history


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

    name = 'change_status'

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

    def model_run(self, model_context, mode, new_status=None):
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
                subsystem_obj = model_context.admin.get_subsystem_object(obj)
                # the number of status changes as seen in the UI
                number_of_statuses = len(subsystem_obj.status)
                history_type = subsystem_obj._status_history
                history = model_context.session.query(history_type)
                history = history.filter(history_type.status_for==subsystem_obj)
                history = history.with_for_update(nowait=True)
                history_count = sum(1 for _h in history.yield_per(10))
                if number_of_statuses != history_count:
                    if subsystem_obj not in model_context.session.new:
                        model_context.session.expire(subsystem_obj)
                    yield action_steps.UpdateObjects([subsystem_obj])
                    raise UserException(_('Concurrent status change'),
                                        detail=_('Another user changed the status'),
                                        resolution=_('Try again if needed'))
                if subsystem_obj.current_status != new_status:
                    for step in self.before_status_change(model_context, obj):
                        yield step
                    subsystem_obj.change_status(new_status)
                    for step in self.after_status_change(model_context, obj):
                        yield step
                    objects_to_update = [subsystem_obj]
                    if obj != subsystem_obj:
                        objects_to_update.append(obj)
                    yield action_steps.UpdateObjects(objects_to_update)
            yield action_steps.FlushSession(model_context.session)

class StatusFilter(list_filter.GroupBoxFilter, AbstractModelFilter):
    """
    Filter to be used in a table view to enable filtering on the status
    of an object.  This filter will display all available statuses, and as
    such, needs not to query the distinct values used in the database to
    build up it's widget.
    
    :param entity_with_status: an entity class that inherits from ´WithStatus' and thus holds the status to filter on.
    :param joins: in case of a related status filter, the joins required to get from the status class back to the target entity.
    """

    name = 'status_filter'
    filter_strategy = list_filter.RelatedFilter

    def __init__(self, entity_with_status, joins=[], default=list_filter.All, verbose_name=None, exclusive=True):
        assert issubclass(entity_with_status, WithStatus)
        attribute = entity_with_status._status_history.classified_by
        self.joins = joins
        super().__init__(attribute, default=default, verbose_name=verbose_name, exclusive=exclusive)

    def get_strategy(self, attribute):
        history_type = attribute.class_
        current_date = sql.functions.current_date()
        return self.filter_strategy(
            list_filter.ChoicesFilter(attribute),
            joins=[history_type.status_for] + self.joins,
            where=sql.and_(
                history_type.status_from_date <= current_date,
                history_type.status_for_id == history_type.status_for.prop.entity.class_.id,
                history_type.status_thru_date >= current_date))

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

    def get_state(self, model_context):
        state = Action.get_state(self, model_context)
        attributes = model_context.admin.get_field_attributes(self.attribute.key)
        history_type = self.attribute.class_
        history_admin = model_context.admin.get_related_admin(history_type)
        classification_fa = history_admin.get_field_attributes('classified_by')

        target = classification_fa.get('target')
        if target is not None:
            choices = [(st, st.code) for st in target.query.all()]
        else:
            choices = classification_fa['choices']

        state.modes = []
        modes = []
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
        state.verbose_name = attributes['name']
        return state
