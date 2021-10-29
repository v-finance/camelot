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
Actions to filter table views
"""
import datetime
import decimal
import operator

from camelot.core.sql import like_op
from camelot.view import utils
from camelot.view.controls import delegates

from dataclasses import dataclass

from sqlalchemy import orm, sql
from sqlalchemy.sql.operators import between_op

from ...core.utils import ugettext
from ...core.item_model import PreviewRole
from ...core.item_model.proxy import AbstractModelFilter
from ...core.qt import Qt
from ...view.utils import locale

from .base import Action, Mode, RenderHint
from .field_action import FieldActionModelContext

_numerical_operators = (operator.eq, operator.ne, operator.lt, operator.le, operator.gt, operator.ge, between_op)
_text_operators = (operator.eq, operator.ne, like_op)

@dataclass
class FilterMode(Mode):

    checked: bool = False

    def __init__(self, value, verbose_name, checked=False):
        super(FilterMode, self).__init__(name=value, verbose_name=verbose_name)
        self.checked = checked

    def decorate_query(self, query, value):
        return self.decorator(query, value)

# This used to be:
#
#     class All(object):
#         pass
#
# It has been replaced by All = '__all' to allow serialization
#
All = '__all'

class Filter(Action):
    """Base class for filters"""

    name = 'filter'

    def __init__(self, attribute, default=All, verbose_name=None):
        """
        :param attribute: the attribute on which to filter, this attribute
            may contain dots to indicate relationships that need to be followed, 
            eg.  'person.name'

        :param default: the default value to filter on when the view opens,
            defaults to showing all records.
        
        :param verbose_name: the name of the filter as shown to the user, defaults
            to the name of the field on which to filter.
        """
        self.attribute = attribute
        self.default = default
        self.verbose_name = verbose_name
        self.exclusive = True
        self.joins = None
        self.column = None
        self.attributes = None
        self.filter_names = []

    def get_name(self):
        return '{}_{}'.format(self.name, self.attribute)

    def gui_run(self, gui_context, value):
        model = gui_context.item_view.model()
        if model is not None:
            model.set_filter(self, value)

    def decorate_query(self, query, values):
        if All in values:
            return query
        if self.joins:
            query = query.join(*self.joins)
        if 'precision' in self.attributes:
            delta = pow( 10,  -1*self.attributes['precision'])
            for value in values:
                query = query.filter(sql.and_(self.column < value+delta,
                                              self.column > value-delta))
        else:
            not_none_values = [v for v in values if v is not None]
            if len(not_none_values):
                where_clause = self.column.in_(not_none_values)
            else:
                where_clause = False
            if None in values:
                where_clause = sql.or_(where_clause,
                                       self.column==None)
            query = query.filter(where_clause)
        return query

    def get_state(self, model_context):
        """
        :return:  a :class:`filter_data` object
        """
        state = super(Filter, self).get_state(model_context)
        session = model_context.session
        entity = model_context.admin.entity

        if self.joins is None:
            self.joins = []
            related_admin = model_context.admin
            for field_name in self.attribute.split('.'):
                attributes = related_admin.get_field_attributes(field_name)
                self.filter_names.append(attributes['name'])
                # @todo: if the filter is not on an attribute of the relation, but on 
                # the relation itselves
                if 'target' in attributes:
                    self.joins.append(getattr(related_admin.entity, field_name))
                    related_admin = attributes['admin']
            self.column = getattr(related_admin.entity, field_name)
            self.attributes = attributes
        
        query = session.query(self.column).select_from(entity).join(*self.joins)
        query = query.distinct()

        modes = list()

        for value in query:
            if 'to_string' in self.attributes:
                verbose_name = self.attributes['to_string'](value[0])
            else:
                verbose_name = value[0]
            if self.attributes.get('translate_content', False):
                verbose_name = ugettext(verbose_name)
            mode = FilterMode(value=value[0],
                              verbose_name=verbose_name,
                              checked=((value[0]==self.default) or (self.exclusive==False)))
        
            # option_name name can be of type ugettext_lazy, convert it to unicode
            # to make it sortable
            modes.append(mode)

        state.verbose_name = self.verbose_name or self.filter_names[0]
        # sort outside the query to sort on the verbose name of the value
        modes.sort(key=lambda state:state.verbose_name)
        # put all mode first, no mater of its verbose name
        if self.exclusive:
            all_mode = FilterMode(value=All,
                                  verbose_name=ugettext('All'),
                                  checked=(self.default==All))
            modes.insert(0, all_mode)
        else:
            #if attributes.get('nullable', True):
            none_mode = FilterMode(value=None,
                                   verbose_name=ugettext('None'),
                                   checked=True)
            modes.append(none_mode)
        state.modes = modes
        return state

class GroupBoxFilter(Filter):
    """Filter where the items are displayed in a QGroupBox"""

    render_hint = RenderHint.EXCLUSIVE_GROUP_BOX
    name = 'group_box_filter'

    def __init__(self, attribute, default=All, verbose_name=None, exclusive=True):
        super().__init__(attribute, default, verbose_name)
        self.exclusive = exclusive
        self.render_hint = RenderHint.EXCLUSIVE_GROUP_BOX if exclusive else RenderHint.NON_EXCLUSIVE_GROUP_BOX

class ComboBoxFilter(Filter):
    """Filter where the items are displayed in a QComboBox"""

    render_hint = RenderHint.COMBO_BOX
    name = 'combo_box_filter'

class AbstractFilterStrategy(object):
    """
    Abstract interface for defining filter clauses as part of an entity admin's query.
    :attribute name: string that uniquely identifies this filter strategy class.
    """

    name = None    
    operators = []
    delegate = None

    def __init__(self, key, where=None, verbose_name=None):
        """
        :param key: String that identifies this filter strategy instance within the context of an admin/entity.
        :param where: an optional additional condition that should be met for the filter clause to apply.
        :param verbose_name: Optional verbose name to override the default verbose name behaviour based on this strategy's key.
        """
        assert isinstance(key, str)
        self._key = key
        self.where = where
        self._verbose_name = verbose_name
    
    def get_clause(self, text, admin, session):
        """
        Return a search clause for the given search text.
        :param admin: The entity admin that will use the resulting search clause as part of its search query.
        :param session: The session in which the search query takes place.
        """
        raise NotImplementedError
    
    def value_to_string(self, filter_value, admin):
        """
        Turn the given filter value into its corresponding string representation applicable for this filter strategy, based on the given admin.
        """
        raise NotImplementedError
    
    @property
    def key(self):
        return self._key
    
    def get_verbose_name(self):
        if self._verbose_name is not None:
            return self._verbose_name
        return ugettext(self.key.replace(u'_', u' ').capitalize())

class FieldFilter(AbstractFilterStrategy):
    """
    Abstract interface for defining a column-based filter clause on a queryable attribute of an entity, as part of that entity admin's query.
    Implementations of this interface should define it's python type, which will be asserted to match with that of the set attribute.
    """

    attribute = None

    def __init__(self, attribute, where=None, key=None, verbose_name=None):
        """
        :param attribute: a queryable attribute for which this field filter should be applied. It's key will be used as this field filter's key.
        :param key: Optional string to use as this strategy's key. By default the attribute's key will be used.
        """
        self.assert_valid_attribute(attribute)
        key = key or attribute.key
        super().__init__(key, where, verbose_name)
        self.attribute = attribute
    
    @classmethod
    def assert_valid_attribute(cls, attribute):
        assert isinstance(attribute, orm.attributes.QueryableAttribute), 'The given attribute is not a valid QueryableAttribute'
        if isinstance(attribute, orm.attributes.InstrumentedAttribute):
            python_type = attribute.type.python_type
        else:
            expression =  attribute.expression
            if isinstance(expression, sql.selectable.Select):
                expression = expression.as_scalar()
            python_type = expression.type.python_type
        assert issubclass(python_type, cls.python_type), 'The python_type of the given attribute does not match the python_type of this filter strategy'
    
    def get_clause(self, text, admin, session):
        """
        Return a search clause consisting of this field search's type clause,
        expanded with condition on the attribute being set (None check) and the optionally set where condition.
        """
        field_attributes = admin.get_field_attributes(self.attribute.key)
        search_clause = self.get_type_clause(text, field_attributes)
        if search_clause is not None:
            where_conditions = [self.attribute != None]
            if self.where is not None:
                where_conditions.append(self.where)
            return sql.and_(*where_conditions, search_clause)
    
    def get_type_clause(self, text, field_attributes):
        """
        Return a column-based expression search clause on this search strategy's attribute for the given search text.
        :param field_attributes: The field attributes for this search strategy's attribute on the entity admin
                                 that will use the resulting search clause as part of its search query.
        """
        raise NotImplementedError

class RelatedFilter(AbstractFilterStrategy):
    """
    Filter strategy for defining a filter clause as part of an entity admin's query on fields of one of its related entities.
    """

    name = 'related_filter'
    delegate = delegates.PlainTextDelegate

    def __init__(self, *field_filters, joins, where=None, key=None, verbose_name=None):
        """
        :param field_filters: field filter strategies for the fields on which this related filter should apply.
        :param joins: join definition between the entity on which the query this related filter is part of takes place,
                      and the related entity of the given field filters.
        :param key: Optional string to use as this strategy's key. By default the key of this related filter's first field filter will be used.
        """
        assert isinstance(joins, list) and len(joins) > 0
        for field_search in field_filters:
            assert isinstance(field_search, FieldFilter)
        key = key or field_filters[0].key
        super().__init__(key, where, verbose_name)
        self.field_filters = field_filters
        self.joins = joins

    def get_clause(self, text, admin, session):
        """
        Return a search clause consisting of a check on the admin's entity's id being present in a related search subquery.
        The subquery will use this related search strategy's joins to join the entity with the related entity on which the set search fields are defined.
        where the search clauses of each.
        The subquery is composed based on this related search strategy's joins and where condition,
        """        
        related_query = session.query(admin.entity.id)

        for join in self.joins:
            related_query = related_query.join(join)

        if self.where is not None:
            related_query.filter(self.where)

        field_filter_clauses = []
        for field_filter in self.field_filters:
            related_admin = admin.get_related_admin(field_filter.attribute.class_)
            field_filter_clause = field_filter.get_clause(text, related_admin, session)
            if field_filter_clause is not None:
                field_filter_clauses.append(field_filter_clause)
                
        if field_filter_clauses:
            related_query = related_query.filter(sql.or_(*field_filter_clauses))
            related_query = related_query.subquery()
            filter_clause = admin.entity.id.in_(related_query)
            return filter_clause
    
    def value_to_string(self, filter_value, admin):
        for field_filter in self.field_filters:
            related_admin = admin.get_related_admin(field_filter.attribute.class_)
            return field_filter.value_to_string(filter_value, related_admin)

class NoFilter(FieldFilter):

    name = 'no_filter'

    def __init__(self, attribute):
        super().__init__(attribute, key=str(attribute))
        
    @classmethod
    def assert_valid_attribute(cls, attribute):
        pass
    
    def get_clause(self, text, admin, session):
        return None
    
    def value_to_string(self, filter_value, admin):
        return filter_value
    
    def get_verbose_name(self):
        return None

class StringFilter(FieldFilter):
    
    name = 'string_filter'
    python_type = str
    operators = _text_operators
    delegate = delegates.PlaintTextDelegate

    # Flag that configures whether this string search strategy should be performed when the search text only contains digits.
    allow_digits = True
    
    def __init__(self, attribute, allow_digits=True, where=None, key=None, verbose_name=None):
        super().__init__(attribute, where, key, verbose_name)
        self.allow_digits = allow_digits
        
    def get_type_clause(self, text, field_attributes):
        if not text.isdigit() or self.allow_digits:
            return sql.operators.ilike_op(self.attribute, '%'+text+'%')
    
    def value_to_string(self, filter_value, admin):
        return filter_value
    
class DecimalFilter(FieldFilter):
    
    name = 'decimal_filter'
    python_type = (float, decimal.Decimal)
    operators = _numerical_operators
    delegate = delegates.FloatDelegate    

    def get_type_clause(self, text, field_attributes):
        try:
            float_value = field_attributes.get('from_string', utils.float_from_string)(text)
            precision = self.attribute.type.precision
            if isinstance(precision, (tuple)):
                precision = precision[1]
            delta = 0.1**( precision or 0 )
            return sql.and_(self.attribute>=float_value-delta, self.attribute<=float_value+delta)
        except utils.ParsingError:
            pass
    
    def value_to_string(self, value, admin):
        field_attributes = admin.get_field_attributes(self.attribute.key)
        delegate = field_attributes.get('delegate')
        suffix = ' ' + field_attributes.get('suffix', '')
        model_context = FieldActionModelContext()
        model_context.admin = admin
        model_context.value = value
        model_context.field_attributes = field_attributes
        standard_item = delegate.get_standard_item(locale(), model_context)
        value_str = standard_item.data(PreviewRole)
        return value_str.replace(suffix, '')
        
class TimeFilter(FieldFilter):
    
    name = 'time_filter'
    python_type = datetime.time
    operators = _numerical_operators
    delegate = delegates.TimeDelegate

    def get_type_clause(self, text, field_attributes):
        try:
            return (self.attribute==field_attributes.get('from_string', utils.time_from_string)(text))
        except utils.ParsingError:
            pass
    
    def value_to_string(self, value, admin):
        field_attributes = admin.get_field_attributes(self.attribute.key)
        delegate = field_attributes.get('delegate')
        model_context = FieldActionModelContext()
        model_context.admin = admin
        model_context.value = value
        model_context.field_attributes = field_attributes
        standard_item = delegate.get_standard_item(locale(), model_context)
        return standard_item.data(PreviewRole)

class DateFilter(FieldFilter):

    name = 'date_filter'
    python_type = datetime.date
    operators = _numerical_operators
    delegate = delegates.DateDelegate
    
    def get_type_clause(self, text, field_attributes):
        try:
            return (self.attribute==field_attributes.get('from_string', utils.date_from_string)(text))
        except utils.ParsingError:
            pass
    
    def value_to_string(self, value, admin):
        field_attributes = admin.get_field_attributes(self.attribute.key)
        delegate = field_attributes.get('delegate')
        model_context = FieldActionModelContext()
        model_context.admin = admin
        model_context.value = value
        model_context.field_attributes = field_attributes
        standard_item = delegate.get_standard_item(locale(), model_context)
        return standard_item.data(PreviewRole)
    
class IntFilter(FieldFilter):

    name = 'int_filter'
    python_type = int
    operators = _numerical_operators
    delegate = delegates.IntegerDelegate
    
    def get_type_clause(self, text, field_attributes):
        try:
            return (self.attribute==field_attributes.get('from_string', utils.int_from_string)(text))
        except utils.ParsingError:
            pass

    def value_to_string(self, value, admin):
        field_attributes = admin.get_field_attributes(self.attribute.key)
        delegate = field_attributes.get('delegate')
        to_string = field_attributes.get('to_string')
        model_context = FieldActionModelContext()
        model_context.admin = admin
        model_context.value = value
        model_context.field_attributes = field_attributes
        standard_item = delegate.get_standard_item(locale(), model_context)
        return to_string(standard_item.data(Qt.EditRole))

class BoolFilter(FieldFilter):

    name = 'bool_filter'
    python_type = bool
    operators = (operator.eq,)
    delegate = delegates.BoolDelegate
    
    def get_type_clause(self, text, field_attributes):
        try:
            return (self.attribute==field_attributes.get('from_string', utils.bool_from_string)(text))
        except utils.ParsingError:
            pass

    def value_to_string(self, value, admin):
        field_attributes = admin.get_field_attributes(self.attribute.key)
        delegate = field_attributes.get('delegate')
        to_string = field_attributes.get('to_string')
        model_context = FieldActionModelContext()
        model_context.admin = admin
        model_context.value = value
        model_context.field_attributes = field_attributes
        standard_item = delegate.get_standard_item(locale(), model_context)
        return to_string(standard_item.data(Qt.EditRole))
    
class SearchFilter(Action, AbstractModelFilter):

    render_hint = RenderHint.SEARCH_BUTTON
    name = 'search_filter'

    #shortcut = QtGui.QShortcut(QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Find),
                               #self)
    
    def __init__(self, admin):
        Action.__init__(self)
        # dirty : action requires admin as argument
        self.admin = admin

    def get_state(self, model_context):
        state = Action.get_state(self, model_context)
        return state

    def decorate_query(self, query, text):
        if (text is None) or (len(text.strip())==0):
            return query
        return self.admin.decorate_search_query(query, text)

    def gui_run(self, gui_context):
        # overload the action gui run to avoid a progress dialog
        # popping up while searching
        super(SearchFilter, self).gui_run(gui_context)

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        value = mode
        if (value is not None) and len(value) == 0:
            value = None
        yield action_steps.SetFilter(self, value)
