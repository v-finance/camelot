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

class AbstractSearchStrategy(object):
    """
    Abstract interface for defining a search clause as part of an entity admin's search query for a certain search text.
    """
    
    def __init__(self, where=None):
        """
        :param where: an optional additional condition that should be met for the search clause to apply.
        """
        self.where = where
    
    def get_clause(self, text, admin, session):
        """
        Return a search clause for the given search text.
        :param admin: The entity admin that will use the resulting search clause as part of its search query.
        :param session: The session in which the search query takes place.
        """
        raise NotImplementedError

class FieldSearch(AbstractSearchStrategy):
    """
    Abstract interface for defining a column-based search clause on a queryable attribute of an entity, as part of that entity admin's search query.
    Implementations of this interface should define it's python type, which will be asserted to match with that of the set attribute.
    """
    
    attribute = None
    python_type = None

    def __init__(self, attribute, where=None):
        """
        :param attribute: a queryable attribute for on which this field search should be applied on.
        """        
        super().__init__(where)
        self.assert_valid_attribute(attribute)
        self.attribute = attribute
    
    @classmethod
    def assert_valid_attribute(cls, attribute):
        assert isinstance(attribute, orm.attributes.QueryableAttribute), 'The given attribute is not a valid QueryableAttribute'
        assert issubclass(attribute.type.python_type, cls.python_type), 'The python_type of the given attribute does not match the python_type of this search strategy'
    
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

class RelatedSearch(AbstractSearchStrategy):
    """
    Search strategy for defining a search clause as part of an entity admin's search query on fields of one of its related entities.
    """

    def __init__(self, *field_searches, joins, where=None):
        """
        :param field_searches: field search strategies for the search fields on which this related search should apply.
        :param joins: join definition between the entity on which the search query this related search is part of takes place,
                      and the related entity of the given field searches.
        """
        super().__init__(where)
        assert isinstance(joins, list) and len(joins) > 0   
        for field_search in field_searches:
            assert isinstance(field_search, FieldSearch)
        self.field_searches = field_searches
        self.joins = joins

    def get_clause(self, text, admin, session):
        """
        Return a search clause consisting of a check on the admin's entity's id being present in a related search subquery.
        The subquery will use this related search strategy's joins to join the entity with the related entity on which the set search fields are defined.
        where the search clauses of each.
        The subquery is composed based on this related search strategy's joins and where condition,
        """        
        related_search_query = session.query(admin.entity.id)

        for join in self.joins:
            related_search_query = related_search_query.join(join)

        if self.where is not None:
            related_search_query.filter(self.where)

        field_search_clauses = []
        for field_search in self.field_searches:
            related_admin = admin.get_related_admin(field_search.attribute.class_)
            field_search_clause = field_search.get_clause(text, related_admin, session)
            if field_search_clause is not None:
                field_search_clauses.append(field_search_clause)
                
        if field_search_clauses:
            related_search_query = related_search_query.filter(sql.or_(*field_search_clauses))
            related_search_query = related_search_query.subquery()
            search_clause = admin.entity.id.in_(related_search_query)
            return search_clause

class NoSearch(FieldSearch):
    
    @classmethod
    def assert_valid_attribute(cls, attribute):
        pass
    
    def get_clause(self, text, admin, session):
        return None

class StringSearch(FieldSearch):
    
    python_type = str
    
    # Flag that configures whether this string search strategy should be performed when the search text only contains digits.
    allow_digits = True
    
    def __init__(self, attribute, allow_digits=True):
        super().__init__(attribute)
        self.allow_digits = allow_digits
        
    def get_type_clause(self, text, field_attributes):
        if not text.isdigit() or self.allow_digits:
            return sql.operators.ilike_op(self.attribute, '%'+text+'%')
    
class DecimalSearch(FieldSearch):
    
    python_type = (float, decimal.Decimal)
    
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
        
class TimeDeltaSearch(FieldSearch):
    
    python_type = datetime.timedelta
    
    def get_type_clause(self, text, field_attributes):
        try:
            days = field_attributes.get('from_string', utils.int_from_string)(text)
            return (self.attribute==datetime.timedelta(days=days))
        except utils.ParsingError:
            pass
        
class TimeSearch(FieldSearch):
    
    python_type = datetime.time
    
    def get_type_clause(self, text, field_attributes):
        try:
            return (self.attribute==field_attributes.get('from_string', utils.time_from_string)(text))
        except utils.ParsingError:
            pass

class DateSearch(FieldSearch):
    
    python_type = datetime.date
    
    def get_type_clause(self, text, field_attributes):
        try:
            return (self.attribute==field_attributes.get('from_string', utils.date_from_string)(text))
        except utils.ParsingError:
            pass
        
class IntSearch(FieldSearch):
    
    python_type = int
    
    def get_type_clause(self, text, field_attributes):
        try:
            return (self.attribute==field_attributes.get('from_string', utils.int_from_string)(text))
        except utils.ParsingError:
            pass  

class BoolSearch(FieldSearch):
    
    python_type = bool
    
    def get_type_clause(self, text, field_attributes):
        try:
            return (self.attribute==field_attributes.get('from_string', utils.bool_from_string)(text))
        except utils.ParsingError:
            pass

class VirtualAddressSearch(FieldSearch):
    
    python_type = camelot.types.virtual_address
    
    def get_type_clause(self, text, field_attributes):
        return self.attribute.like(camelot.types.virtual_address('%', '%'+text+'%'))
    
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
