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

import camelot.types
import datetime
import decimal

from camelot.view import utils
from sqlalchemy import orm, sql

from ...core.utils import ugettext
from ...core.item_model.proxy import AbstractModelFilter
from .base import Action, Mode, RenderHint

class FilterMode(Mode):

    def __init__(self, value, verbose_name, checked=False):
        super(FilterMode, self).__init__(name=value, verbose_name=verbose_name)
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
        self.joins = None
        self.column = None
        self.attributes = None
        self.filter_names = []

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

    render_hint = RenderHint.GROUP_BOX

    def __init__(self, attribute, default=All, verbose_name=None, exclusive=True):
        super(GroupBoxFilter, self).__init__(attribute, default, verbose_name)
        self.exclusive = exclusive


class ComboBoxFilter(Filter):
    """Filter where the items are displayed in a QComboBox"""

    render_hint = RenderHint.COMBO_BOX


class SearchFieldStrategy(object):
    """Abstract class for search field strategies.
       It offers an interface for defining a column-based search clause for a given queryable attribute and search text.
    """

    attribute = None
    python_type = None

    def __init__(self, attribute):
        self.assert_valid_attribute(attribute)
        self.attribute = attribute
    
    @classmethod
    def assert_valid_attribute(cls, attribute):
        assert isinstance(attribute, orm.attributes.QueryableAttribute), 'The given attribute is not a valid QueryableAttribute'
        assert issubclass(attribute.type.python_type, cls.python_type), 'The python_type of the given attribute does not match the python_type of this search strategy'
    
    @classmethod
    def get_clause(cls, search_strategy, text, field_attributes, attribute=None):
        assert search_strategy == cls or isinstance(search_strategy, cls), 'The given search strategy should be a class object or instance of this search field strategy'
        attribute = search_strategy.attribute or attribute
        cls.assert_valid_attribute(attribute)
        return cls.get_type_clause(search_strategy, attribute, text, field_attributes)
    
    @classmethod
    def get_type_clause(cls, search_strategy, c, text, field_attributes):
        """Return the given search strategy's search clause for the given queryable attribute, search text and field_attributes, if applicable."""
        raise NotImplementedError
    
class NoSearch(SearchFieldStrategy):
    
    def __init__(self):
        super().__init__(None)
        
    @classmethod
    def get_clause(cls, search_strategy, column, text, field_attributes):
        return None

class StringSearch(SearchFieldStrategy):
    
    python_type = str
    
    # Flag that configures whether this string search strategy should be performed when the search text only contains digits.
    allow_digits = True
    
    def __init__(self, attribute, allow_digits=True):
        super().__init__(attribute)
        self.allow_digits = allow_digits
        
    @classmethod
    def get_type_clause(cls, search_strategy, c, text, field_attributes):
        if not text.isdigit() or search_strategy.allow_digits:
            return sql.operators.ilike_op(c, '%'+text+'%')
    
class DecimalSearch(SearchFieldStrategy):
    
    python_type = (float, decimal.Decimal)
    
    @classmethod
    def get_type_clause(cls, search_strategy, c, text, field_attributes):
        try:
            float_value = field_attributes.get('from_string', utils.float_from_string)(text)
            precision = c.type.precision
            if isinstance(precision, (tuple)):
                precision = precision[1]
            delta = 0.1**( precision or 0 )
            return sql.and_(c>=float_value-delta, c<=float_value+delta)
        except utils.ParsingError:
            pass       
        
class TimeDeltaSearch(SearchFieldStrategy):
    
    python_type = datetime.timedelta
    
    @classmethod
    def get_type_clause(cls, search_strategy, c, text, field_attributes):
        try:
            days = field_attributes.get('from_string', utils.int_from_string)(text)
            return (c==datetime.timedelta(days=days))
        except utils.ParsingError:
            pass
        
class TimeSearch(SearchFieldStrategy):
    
    python_type = datetime.time
    
    @classmethod
    def get_type_clause(cls, search_strategy, c, text, field_attributes):
        try:
            return (c==field_attributes.get('from_string', utils.time_from_string)(text))
        except utils.ParsingError:
            pass

class DateSearch(SearchFieldStrategy):
    
    python_type = datetime.date
    
    @classmethod
    def get_type_clause(cls, search_strategy, c, text, field_attributes):
        try:
            return (c==field_attributes.get('from_string', utils.date_from_string)(text))
        except utils.ParsingError:
            pass
        
class IntSearch(SearchFieldStrategy):
    
    python_type = int
    
    @classmethod
    def get_type_clause(cls, search_strategy, c, text, field_attributes):
        try:
            return (c==field_attributes.get('from_string', utils.int_from_string)(text))
        except utils.ParsingError:
            pass  

class BoolSearch(SearchFieldStrategy):
    
    python_type = bool
    
    @classmethod
    def get_type_clause(cls, search_strategy, c, text, field_attributes):
        try:
            return (c==field_attributes.get('from_string', utils.bool_from_string)(text))
        except utils.ParsingError:
            pass

class VirtualAddressSearch(SearchFieldStrategy):
    
    python_type = camelot.types.virtual_address
    
    @classmethod
    def get_type_clause(cls, search_strategy, c, text, field_attributes):
        return c.like(camelot.types.virtual_address('%', '%'+text+'%'))
    
class SearchFilter(Action, AbstractModelFilter):

    render_hint = RenderHint.SEARCH_BUTTON

    #shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(QtGui.QKeySequence.Find),
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

    def model_run(self, model_context):
        from camelot.view import action_steps
        value = model_context.mode_name
        if (value is not None) and len(value) == 0:
            value = None
        yield action_steps.SetFilter(self, value)
