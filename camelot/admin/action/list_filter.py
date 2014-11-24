#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""
Actions to filter table views
"""

import copy
import datetime

import six

from sqlalchemy import sql

from ...core.utils import ugettext, ugettext_lazy as _
from .base import Action, Mode

class FilterMode(Mode):

    def __init__(self, value, verbose_name, decorator, checked=False):
        super(FilterMode, self).__init__(name=value, verbose_name=verbose_name)
        self.decorator = decorator
        self.checked = checked

    def decorate_query(self, query, value):
        return self.decorator(query, value)

class All(object):
    pass

class Filter(Action):
    """Base class for filters"""

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

    def gui_run(self, gui_context, value):
        model = gui_context.item_view.model()
        if model is not None:
            model.set_filter_mode(self, gui_context.mode_name, value)

    def create_decorator(self, col, attributes, values, joins):
        
        def decorator(q, values):
            if joins:
                q = q.join(*joins)
            if 'precision' in attributes:
                delta = pow( 10,  -1*attributes['precision'])
                for value in values:
                    q = q.filter( sql.and_(col < value+delta, col > value-delta) )
            else:
                where_clauses = [col==v for v in values]
                q = q.filter(sql.or_(*where_clauses))
            return q
          
        return decorator

    def get_state(self, model_context):
        """
        :return:  a :class:`filter_data` object
        """
        state = super(Filter, self).get_state(model_context)
        session = model_context.session
        filter_names = []
        joins = []
        entity = model_context.admin.entity
        related_admin = model_context.admin
        for field_name in self.attribute.split('.'):
            attributes = related_admin.get_field_attributes(field_name)
            filter_names.append(attributes['name'])
            # @todo: if the filter is not on an attribute of the relation, but on 
            # the relation itselves
            if 'target' in attributes:
                joins.append(getattr(related_admin.entity, field_name))
                related_admin = attributes['admin']

        col = getattr(related_admin.entity, field_name)
        query = session.query(col).select_from(entity).join(*joins)
        query = query.distinct()

        modes = list()

        for value in query:
            if 'to_string' in attributes:
                verbose_name = attributes['to_string'](value[0])
            else:
                verbose_name = value[0]
            if attributes.get('translate_content', False):
                verbose_name = ugettext(verbose_name)
            decorator = self.create_decorator(col, attributes, value[0], joins)
            mode = FilterMode(value=value[0],
                              verbose_name=verbose_name,
                              decorator=decorator,
                              checked=((value[0]==self.default) or (self.exclusive==False)))
        
            # option_name name can be of type ugettext_lazy, convert it to unicode
            # to make it sortable
            modes.append(mode)

        state.verbose_name = self.verbose_name or filter_names[0]
        # sort outside the query to sort on the verbose name of the value
        modes.sort(key=lambda state:state.verbose_name)
        # put all mode first, no mater of its verbose name
        if self.exclusive:
            all_mode = FilterMode(value=All,
                                  verbose_name=ugettext('All'),
                                  decorator=lambda x, _v:x,
                                  checked=(self.default==All))
            modes.insert(0, all_mode)
        else:
            #if attributes.get('nullable', True):
            none_mode = FilterMode(value=None,
                                   verbose_name=ugettext('None'),
                                   decorator=self.create_decorator(col, attributes, None, joins),
                                   checked=True)
            modes.append(none_mode)
        state.modes = modes
        return state

class GroupBoxFilter(Filter):
    """Filter where the items are displayed in a QGroupBox"""

    def __init__(self, attribute, default=All, verbose_name=None, exclusive=True):
        super(GroupBoxFilter, self).__init__(attribute, default, verbose_name)
        self.exclusive = exclusive

    def render(self, gui_context, parent):
        from ...view.controls.filter_widget import FilterWidget
        return FilterWidget(self, gui_context, parent)


class ComboBoxFilter(Filter):
    """Filter where the items are displayed in a QComboBox"""

    def render(self, gui_context, parent):
        from ...view.controls.filter_widget import ComboBoxFilterWidget
        return ComboBoxFilterWidget(self, gui_context, parent)
    
class EditorFilter(Filter):
    """Filter that presents the user with an editor, allowing the user to enter
    a value on which to filter, and at the same time to show 'All' or 'None'
    
    :param field_name: the name fo the field on the class on which to filter
    :param default_operator: a default operator to be used, on of the attributes
        of the python module :mod:`operator`, such as `operator.eq`
    :param default_value_1: a default value for the first editor (in case the
        default operator in unary or binary
    :param default_value_2: a default value for the second editor (in case the
        default operator is binary)
    """

    def __init__( self, 
                  field_name, 
                  verbose_name = None,
                  default_operator = None,
                  default_value_1 = None,
                  default_value_2 = None ):
        super(EditorFilter, self).__init__(field_name, verbose_name=verbose_name)
        self._field_name = field_name
        self._verbose_name = verbose_name
        self._default_operator = default_operator
        self._default_value_1 = default_value_1
        self._default_value_2 = default_value_2

    def render(self, gui_context, parent):
        from ...view.controls.filter_widget import OperatorWidget
        return OperatorWidget(self, gui_context, self._default_value_1,
                              self._default_value_2, parent)

    def gui_run(self, gui_context, value1, value2):
        model = gui_context.item_view.model()
        if model is not None:
            model.set_filter_mode(self, gui_context.mode_name, (value1, value2))

    def get_arity(self, operator):
        """:return: the current operator and its arity"""
        try:
            func_code = six.get_function_code(operator)
        except AttributeError:
            arity = 1 # probably a builtin function, assume arity == 1
        else:
            arity = func_code.co_argcount - 1
        return arity

    def create_decorator(self, column, operator):
        """
        :param query: an sqlalchemy query
        :returns: the input query transformed to take into account the filter of
        this widget
        """
        from camelot.view.field_attributes import order_operators

        def decorator(query, value):
            arity = self.get_arity(operator)
            values = list(value)[:arity]
            none_values = sum( v == None for v in values )
            if (operator in order_operators) and none_values > 0:
                return query
            return query.filter(operator(column, *values))

        return decorator

    def get_state(self, model_context):
        from ...view.utils import operator_names
        state = Action.get_state(self, model_context)
        admin = model_context.admin
        field_attributes = admin.get_field_attributes(self._field_name)
        field_attributes = copy.copy( field_attributes )
        field_attributes['editable'] = True
        state.field_attributes = field_attributes
        state.verbose_name = self.verbose_name or field_attributes['name']

        entity = admin.entity
        field = getattr(entity, self._field_name)

        all_decorator = lambda q,_v:q
        none_decorator = lambda query, _v: query.filter(field==None)
        
        all_mode = FilterMode(All, ugettext('All'), all_decorator,
                              checked=(self.default==All))
        modes = [all_mode,
                 FilterMode(None, ugettext('None'), none_decorator),
                 ]
        
        operators = field_attributes.get('operators', [])
        for operator in operators:
            mode = FilterMode(operator,
                              six.text_type(operator_names[operator]),
                              self.create_decorator(field, operator),
                              checked=(operator==self._default_operator),
                              )
            modes.append(mode)

        state.modes = modes
        return state

class ValidDateFilter(Filter):
    """Filters entities that are valid a certain date.  This filter will present
    a date to the user and filter the entities that have their from date before this
    date and their end date after this date.  If no date is given, all entities will
    be shown"""

    def __init__(self, 
                 from_attribute='from_date',
                 thru_attribute='thru_date',
                 verbose_name=_('Valid at'),
                 default = datetime.date.today ):
        """
        :param from_attribute: the name of the attribute representing the from date
        :param thru_attribute: the name of the attribute representing the thru date
        :param verbose_name: the displayed name of the filter
        :param default: a function returning a default date for the filter
        """
        super(ValidDateFilter, self).__init__(None, default=default)
        self._from_attribute = from_attribute
        self._thru_attribute = thru_attribute
        self._verbose_name = verbose_name
        
    def render(self, gui_context, parent):
        from ...view.controls.filter_widget import DateFilterWidget
        return DateFilterWidget(self, gui_context, parent)
        
    def get_state(self, model_context):
        from sqlalchemy.sql import and_

        state = super(ValidDateFilter, self).get_state(model_context)
        admin = model_context.admin
        
        def query_decorator(query, date):
            e = admin.entity
            if date:
                return query.filter(and_(getattr(e, self._from_attribute)<=date,
                                         getattr(e, self._thru_attribute)>=date))
            return query
        
        mode = FilterMode(verbose_name=None,
                          value = None,
                          decorator = query_decorator)
        state.modes = [mode]
        state.default_mode = mode
        
        return state


