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
import collections
import datetime
import decimal
import enum
import functools
import operator

from camelot.core.orm import Entity
from camelot.core.sql import ilike_op, in_op, is_none, is_not_none
from camelot.view import utils

from dataclasses import dataclass

from sqlalchemy import orm, sql
from sqlalchemy.sql.operators import between_op

from ...core.utils import ugettext, ugettext_lazy as _
from ...core.item_model.proxy import AbstractModelFilter
from ...core.qt import QtGui
from ...core.utils import Arity

from .base import Action, Mode, RenderHint

class PriorityLevel(enum.Enum):

    HIGH = 1
    MEDIUM = 2

filter_operator = collections.namedtuple(
    'filter_operator',
    ('operator', 'arity', 'verbose_name', 'prefix', 'infix', 'pre_condition'))

class Operator(enum.Enum):
    """
    Enum that keeps track of the operator functions that are available for filtering,
    together with some related information like
      * arity : the number of operands the operator takes.
      * verbose name : short verbose description of the operator to display in the GUI.
      * prefix : custom verbose prefix to display between the 1st operand (filtered attribute) and 2nd operand (1st filter value). Defaults to the verbose_name.
      * infix : In case of a ternary operator (arity 3), an optional verbose infix part to display between the 2nd and 3rd operand (1st and 2nd filter value).
      * pre_condition : an optional additional unary condition that should be met for the operator to apply or pre-filter for optimalization. E.g. the is not None check.
    """
    #name                         operator      arity            verbose_name           prefix   infix   pre_condition
    eq =           filter_operator(operator.eq, Arity.binary,   _('='),                 None,    None,   is_not_none)
    ne =           filter_operator(operator.ne, Arity.binary,   _('!='),                None,    None,   is_not_none)
    lt =           filter_operator(operator.lt, Arity.binary,   _('<'),                 None,    None,   is_not_none)
    le =           filter_operator(operator.le, Arity.binary,   _('<='),                None,    None,   is_not_none)
    gt =           filter_operator(operator.gt, Arity.binary,   _('>'),                 None,    None,   is_not_none)
    ge =           filter_operator(operator.ge, Arity.binary,   _('>='),                None,    None,   is_not_none)
    like =         filter_operator(ilike_op,    Arity.binary,   _('like'),              None,    None,   is_not_none)
    between =      filter_operator(between_op,  Arity.ternary,  _('between'),           None,  _('and'), is_not_none)
    is_empty =     filter_operator(is_none,     Arity.unary,    _('is not filled out'), None,    None,   None)
    is_not_empty = filter_operator(is_not_none, Arity.unary,    _('is filled out'),     None,    None,   None)
    in_ =          filter_operator(in_op,       Arity.multiary, _('selection'),         None,    None,   is_not_none)
    and_ =         filter_operator(sql.and_,    Arity.multiary, _('conjunction'),       None,  _('and'), None)
    or_ =          filter_operator(sql.or_,     Arity.multiary, _('disjunction'),       None,  _('or'),  None)

    @property
    def operator(self):
        return self._value_.operator

    @property
    def arity(self):
        return self._value_.arity

    @property
    def verbose_name(self):
        return self._value_.verbose_name

    @property
    def prefix(self):
        return self._value_.prefix or self.verbose_name

    @property
    def infix(self):
        return self._value_.infix

    @property
    def pre_condition(self):
        return self._value_.pre_condition

    @classmethod
    def numerical_operators(cls):
        return (cls.eq, cls.ne, cls.lt, cls.le, cls.gt, cls.ge, cls.between, cls.is_empty, cls.is_not_empty)

    @classmethod
    def text_operators(cls):
        return (cls.eq, cls.ne, cls.like, cls.is_empty, cls.is_not_empty)

class AbstractFilterStrategy(object):
    """
    Abstract interface for defining filter clauses as part of an entity admin's query.
    :attribute name: string that uniquely identifies this filter strategy class.
    :attribute operators: complete list of operators that are available for this filter strategy class.
    """

    name = None    
    operators = []

    class AssertionMessage(enum.Enum):

        no_attributes =                  'No attributes given'
        no_queryable_attribute =         'The given attribute is not a valid QueryableAttribute'
        python_type_mismatch =           'The python_type of the given attribute does not match the python_type of this filter strategy'
        nr_operands_arity_mismatch =     'The provided number of operands ({}) does not correspond with the arity of the given operator, which expects min {} and max {} operands.'
        invalid_relationship_attribute = 'The given attribute is not a valid RelationshipProperty attribute'
        invalid_many2one_relationship_attribute = 'The given attribute is not a valid Many2One RelationshipProperty attribute'
        invalid_target_entity_instance = "Argument is not an instance of this One2ManyFilter's target entity"
        insufficient_join_arguments =    'A related filter strategy requires at least one join argument'
        invalid_field_filters =          'The provided field filters should be instances of :class: `camelot.admin.action.list_filter.FieldFilter`'

    @classmethod
    def assert_operands(cls, operator, *operands):
        min_operands = operator.arity.minimum - 1
        max_operands = operator.arity.maximum - 1 if operator.arity.maximum is not None else len(operands)
        assert min_operands <= len(operands) <= max_operands, cls.AssertionMessage.nr_operands_arity_mismatch.value.format(len(operands), min_operands, max_operands)

    def __init__(self, key, where=None, verbose_name=None, priority_level=PriorityLevel.MEDIUM, **field_attributes):
        """
        :param key: string that identifies this filter strategy instance within the context of an admin/entity.
        :param where: an optional additional condition that should be met for the filter clause to apply.
        :param verbose_name: optional verbose name to override the default verbose name behaviour based on this strategy's key.
        :param priority_level: indicates the level of priority of this filter strategy e.g. to seperate the set of frequently used ones from others.
        """
        assert isinstance(key, str)
        assert isinstance(priority_level, PriorityLevel)
        self._key = key
        self.where = where
        self._verbose_name = verbose_name or field_attributes.get('name')
        self.priority_level = priority_level

    def get_clause(self, query, operator, *operands):
        """
        Construct a filter clause for the given query based on the given filter operator and operands, if applicable for this strategy.

        :param query: the query the filter clause should be constructed for (and could be applied on if desired).
        :param operator: a `camelot.admin.action.list_filter.Operator` instance that defines which operator to use in the column based expression(s) of the resulting filter clause.
        :param operands: the filter values that are used as the operands for the given operator to filter by.
        """
        raise NotImplementedError

    def get_search_clause(self, query, text):
        """
        Construct a search filter clause for the given query based on the given search text, if the search is applicable for this strategy.
        This method is a shortcut for (and equivalent to using) the get_clause method with this strategy's search operator,
        and the corresponding operand converted from the given search text.
        If the from-string-conversion for this strategy fails, the resulting clause will be undefined.

        :param query: the query the filter clause should be constructed for (and could be applied on if desired).
        :param text: the search text operand on which the resulting search clause should filter on.
        """
        try:
            operand = self.from_string(query, text)
        except utils.ParsingError:
            return
        return self.get_clause(query, self.get_search_operator(), operand)

    def from_string(self, query, operand):
        """
        Turn the given stringified operand into its original value.
        By default, the conversion of stringified None values is supported.
        """
        if operand in ('None', 'none'):
            return None
        return operand

    def get_operators(self):
        """
        Return the list of operators that are available for this filter strategy instance.
        By default, this returns the ´operators´ class attribute, but this may be customized on an filter strategy instance basis.
        """
        return self.operators

    def get_search_operator(self):
        """
        Return the operator used for constructing a filter clause meant for searching based on a search text.
        """
        raise NotImplementedError

    def get_field_strategy(self):
        """
        Return the acting filter strategy for this filter strategy's (first) field.
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
    Abstract interface for defining a column-based filter clause on one or more queryable attributes of an entity, as part of that entity admin's query.
    Implementations of this interface should define it's python type, which will be asserted to match with that of the set attributes.
    :attribute search_operator: The default operator that this strategy will use when constructing a filter clause
                                meant for searching based on a search text. By default the `Operator.eq` is used.
    """

    search_operator = Operator.eq
    _default_from_string = functools.partial(utils.pyvalue_from_string, str)

    def __init__(self, *attributes, where=None, key=None, verbose_name=None, priority_level=PriorityLevel.MEDIUM, connective_operator = Operator.or_, **field_attributes):
        """
        :param attributes: queryable attributes for which this field filter should be applied. The first attribute's key will be used as this field filter's key.
        :param key: Optional string to use as this strategy's key. By default the first attribute's key will be used.
        :attr connective_operator: A logical multiary sql operator (AND or OR) to connect the attribute clauses of this field filter's. Defaults to `sqlalchemy.sql.or_`.
        """
        assert len(attributes) >= 1, self.AssertionMessage.no_attributes.value
        for attribute in attributes:
            self.assert_valid_attribute(attribute)
        key = key or attributes[0].key
        super().__init__(key, where, verbose_name, priority_level, **field_attributes)
        self.attributes = attributes
        self.connective_operator = connective_operator
        nullable = field_attributes.get('nullable')
        self.nullable = nullable if isinstance(nullable, bool) else True
        self._from_string = field_attributes.get('from_string')

    @property
    def attribute(self):
        for attribute in self.attributes:
            return attribute

    @classmethod
    def get_attribute_python_type(cls, attribute):
        assert isinstance(attribute, orm.attributes.QueryableAttribute), cls.AssertionMessage.no_queryable_attribute.value
        if isinstance(attribute, orm.attributes.InstrumentedAttribute):
            if isinstance(attribute.prop, orm.RelationshipProperty):
                python_type = Entity
            else:
                python_type = attribute.type.python_type
        else:
            expression =  attribute.expression
            if isinstance(expression, sql.selectable.Select):
                expression = expression.as_scalar()
            python_type = expression.type.python_type
        return python_type

    def assert_valid_attribute(self, attribute):
        python_type = self.get_attribute_python_type(attribute)
        assert issubclass(python_type, self.python_type), self.AssertionMessage.python_type_mismatch.value

    def get_field_strategy(self):
        return self

    def get_operators(self):
        operators = super().get_operators()
        if not self.nullable:
            return [op for op in operators if op not in (Operator.is_empty, Operator.is_not_empty)]
        return operators

    def get_search_operator(self):
        """
        Return the operator used for constructing a filter clause meant for searching based on a search text.
        By default the `search_operator` class attribute is used.
        """
        return self.search_operator

    def get_clause(self, query, operator, *operands):
        """
        Construct a filter clause for the given query based on the filter operator and operand.
        The resulting clause will consists of a connective between field type clauses for each of this field strategy's attributes,
        expanded with conditions on the attributes being set (None check) and the optionally set where conditions.
        :raises: An AssertionError in case number of provided operands does not correspond with the arity of the given operator.
        """
        self.assert_operands(operator, *operands)
        attribute_clauses = []
        for attribute in self.attributes:
            attribute_clause = self.get_attribute_clause(attribute, operator, *operands)
            if attribute_clause is not None:
                where_conditions = []
                if operator.pre_condition is not None:
                    where_conditions.append(operator.pre_condition(attribute))
                if self.where is not None:
                    where_conditions.append(self.where)
                if where_conditions:
                    attribute_clauses.append(sql.and_(*where_conditions, attribute_clause))
                else:
                    attribute_clauses.append(attribute_clause)
        if attribute_clauses:
            return self.connective_operator.operator(*attribute_clauses).self_group()

    def get_attribute_clause(self, attribute, operator, *operands):
        """
        Return a column-based expression filter clause for the given attribute with the given filter operator and operands.
        :param attribute: the instrumented attribute to construct the clause for.
        :param operands: the filter values that are used as the operands for the given operator to filter by.
        """
        assert attribute in self.attributes
        return operator.operator(attribute, *operands)

    def from_string(self, query, operand):
        if isinstance(operand, self.python_type):
            return operand
        operand = super().from_string(query, operand)
        return (self._from_string or self.__class__._default_from_string)(operand)

class RelatedFilter(AbstractFilterStrategy):
    """
    Filter strategy for defining a filter clause as part of an entity admin's query on fields of one of its related entities.
    :attr connective_operator: A logical multiary sql operator (AND or OR) to connect the resulting clauses of this related filter's underlying field strategies. Defaults to `sqlalchemy.sql.and_`.
    """

    name = 'related_filter'
    connective_operator = Operator.and_

    def __init__(self, *field_filters, joins, where=None, key=None, verbose_name=None, priority_level=PriorityLevel.MEDIUM, **field_attributes):
        """
        :param field_filters: field filter strategies for the fields on which this related filter should apply.
        :param joins: join definition between the entity on which the query this related filter is part of takes place,
                      and the related entity of the given field filters.
        :param key: Optional string to use as this strategy's key. By default the key of this related filter's first field filter will be used.
        """
        assert isinstance(joins, list) and len(joins) > 0, self.AssertionMessage.insufficient_join_arguments.value
        for field_search in field_filters:
            assert isinstance(field_search, FieldFilter), self.AssertionMessage.invalid_field_filters.value
        key = key or field_filters[0].key
        super().__init__(key, where, verbose_name, priority_level, **field_attributes)
        self.field_filters = field_filters
        self.joins = joins

    def get_field_strategy(self):
        for field_strategy in self.field_filters:
            return field_strategy

    def get_operators(self):
        for field_strategy in self.field_filters:
            return field_strategy.get_operators()

    def get_search_operator(self):
        for field_strategy in self.field_filters:
            return field_strategy.get_search_operator()

    def get_related_query(self, query, field_filter_clauses=[]):
        session = query.session
        entity = query._mapper_zero().entity
        related_query = session.query(entity.id)
        for join in self.joins:
            related_query = related_query.join(join)
        if self.where is not None:
            related_query = related_query.filter(self.where)
        if field_filter_clauses:
            related_query = related_query.filter(self.connective_operator.operator(*field_filter_clauses))
        related_query = related_query.subquery()
        return related_query

    def get_clause(self, query, operator, *operands):
        """
        Construct a filter clause for the given query based on a provided filter operator and operands.
        The resulting clause will consists of a check on the query base entity's id being present in a related subquery.
        That subquery will use the this strategy's joins to join the entity with the related entity on which the set field filters are defined.
        The subquery is composed based on this related filter strategy's joins and where condition.
        :raises: An AssertionError in case number of provided operands does not correspond with the arity of the given operator.
        """
        self.assert_operands(operator, *operands)
        entity = query._mapper_zero().entity

        field_filter_clauses = []
        for field_strategy in self.field_filters:
            field_operands = []
            for operand in operands:
                field_operand = self.field_operand(field_strategy, operand)
                field_operands.append(field_operand)
            field_filter_clause = field_strategy.get_clause(query, operator, *field_operands)
            if field_filter_clause is not None:
                field_filter_clauses.append(field_filter_clause)

        if field_filter_clauses:
            related_query = self.get_related_query(query, field_filter_clauses)
            return entity.id.in_(related_query)

    def get_search_clause(self, query, text):
        entity = query._mapper_zero().entity

        field_filter_clauses = []
        for field_strategy in self.field_filters:
            field_filter_clause = field_strategy.get_search_clause(query, text)
            if field_filter_clause is not None:
                field_filter_clauses.append(field_filter_clause)

        if field_filter_clauses:
            related_query = self.get_related_query(query, field_filter_clauses)
            return entity.id.in_(related_query)

    def field_operand(self, field_strategy, operand):
        """
        Turn a operand value for this related filter strategy into the appropriate field operand value
        for the given field strategy.
        By default, no conversion is done, and the operand is shared between all underlying field strategies.
        """
        return operand

class RelatedSearch(RelatedFilter):
    """
    RelatedFilter strategy for defining a filter clause as part of an entity admin's search query on fields of one of its related entities.
    As this strategy is meant for decorating a search query, the operators used by this RelatedFilter strategy are configured as such:
      * search operator:  as the field operands are text-based subsets of the values to be matched, the search operator is set to be the `Operator.like` operator.
      * connective operator: as it concerns a search query, the logical connective operator for connecting the underlying field strategies' clauses is set to be the `Operator.or_` operator.
    """
    connective_operator = Operator.or_

class NoFilter(FieldFilter):

    name = 'no_filter'

    def __init__(self, *attributes, where=None, key=None, verbose_name=None, priority_level=PriorityLevel.MEDIUM, **field_attributes):
        super().__init__(*attributes, where=where, key=key or str(attributes[0]), verbose_name=verbose_name, priority_level=priority_level, **field_attributes)

    @classmethod
    def assert_valid_attribute(cls, attribute):
        pass

    def get_clause(self, query, operator, *operands):
        return None

    def get_verbose_name(self):
        return None

    def from_string(self, query, operand):
        return operand

class StringFilter(FieldFilter):

    name = 'string_filter'
    python_type = str
    operators = Operator.text_operators()
    search_operator = Operator.like

    # Flag that configures whether this string search strategy should be performed when the search text only contains digits.
    allow_digits = True

    def __init__(self, *attributes, allow_digits=True, where=None, key=None, verbose_name=None, priority_level=PriorityLevel.MEDIUM, **kwargs):
        super().__init__(*attributes, where=where, key=key, verbose_name=verbose_name, priority_level=priority_level, **kwargs)
        self.allow_digits = allow_digits

    def get_attribute_clause(self, attribute, operator, *operands):
        filter_clause = super().get_attribute_clause(attribute, operator, *operands)
        if operator == Operator.is_empty:
            return sql.or_(super().get_attribute_clause(attribute, Operator.eq, ''), filter_clause)
        elif operator == Operator.is_not_empty:
            return sql.and_(super().get_attribute_clause(attribute, Operator.ne, ''), filter_clause)
        elif not all([operand.isdigit() for operand in operands]) or self.allow_digits:
            return filter_clause

class DecimalFilter(FieldFilter):
    
    name = 'decimal_filter'
    python_type = (float, decimal.Decimal)
    operators = Operator.numerical_operators()
    _default_from_string = utils.float_from_string

    def __init__(self, attribute, where=None, key=None, verbose_name=None, priority_level=PriorityLevel.MEDIUM, **field_attributes):
        super().__init__(attribute, where=where, key=key, verbose_name=verbose_name, priority_level=priority_level, **field_attributes)
        self.precision = field_attributes.get('precision')

    def get_attribute_clause(self, attribute, operator, *float_operands):
        precision = attribute.type.precision
        if isinstance(precision, (tuple)):
            precision = precision[1]
        delta = 0.1**( precision or 0 )

        if operator == Operator.eq and float_operands[0] is not None:
            return sql.and_(attribute>=float_operands[0]-delta, attribute<=float_operands[0]+delta)

        if operator == Operator.ne and float_operands[0] is not None:
            return sql.or_(attribute<float_operands[0]-delta, attribute>float_operands[0]+delta) 

        elif operator in (Operator.lt, Operator.le) and float_operands[0] is not None:
            return super().get_attribute_clause(attribute, operator, float_operands[0]-delta)

        elif operator in (Operator.gt, Operator.ge) and float_operands[0] is not None:
            return super().get_attribute_clause(attribute, operator, float_operands[0]+delta)

        elif operator == Operator.between and None not in (float_operands[0], float_operands[1]):
            return super().get_attribute_clause(attribute, operator, float_operands[0]-delta, float_operands[1]+delta)

class DateFilter(FieldFilter):

    name = 'date_filter'
    python_type = datetime.date
    operators = Operator.numerical_operators()
    _default_from_string = utils.date_from_string
    
class IntFilter(FieldFilter):

    name = 'int_filter'
    python_type = (int, *DecimalFilter.python_type)
    operators = Operator.numerical_operators()
    _default_from_string = utils.int_from_string

class BoolFilter(FieldFilter):

    name = 'bool_filter'
    python_type = bool
    operators = (Operator.eq,)
    _default_from_string = utils.bool_from_string

class ChoicesFilter(FieldFilter):

    name = 'choices_filter'
    python_type = str
    operators = (Operator.eq, Operator.ne)

    def __init__(self, *attributes, where=None, key=None, verbose_name=None, priority_level=PriorityLevel.MEDIUM, **field_attributes):
        # Overrule the python type at the instance level to that of the first attribute,
        # as a choices filter can be defined on attributes of various python types.
        if attributes:
            self.python_type = self.get_attribute_python_type(attributes[0])
        super().__init__(*attributes, where=where, key=key, verbose_name=verbose_name, priority_level=priority_level)
        self.choices = field_attributes.get('choices')

class MonthsFilter(IntFilter):

    name = 'months_filter'

class Many2OneFilter(IntFilter):
    """
    Specialized IntFilter strategy that expects a many2one relationship attribute from which the
    local foreign key attribute is used to instantiate this strategy with.
    """

    name = 'many2one_filter'
    python_type = int
    operators = (Operator.in_, Operator.is_empty, Operator.is_not_empty)

    def __init__(self, attribute, where=None, key=None, verbose_name=None, priority_level=PriorityLevel.MEDIUM, **field_attributes):
        assert isinstance(attribute, orm.attributes.InstrumentedAttribute) and \
               isinstance(attribute.prop, orm.RelationshipProperty) and \
               attribute.prop.direction == orm.interfaces.MANYTOONE, self.AssertionMessage.invalid_many2one_relationship_attribute.value
        assert len(attribute.prop.local_columns) == 1
        entity_mapper = orm.class_mapper(attribute.class_)
        foreign_key_col = list(attribute.prop.local_columns)[0]
        foreign_key_attribute = entity_mapper.get_property_by_column(foreign_key_col).class_attribute
        super().__init__(foreign_key_attribute, where=where, key=(key or attribute.key), verbose_name=(verbose_name or field_attributes.get('name')), priority_level=priority_level, **field_attributes)
        self.entity = attribute.prop.entity.entity
        self.admin = field_attributes.get('admin')

    def get_clause(self, query, operator, *operands):
        # Both primary key integer operands as entity instances are supported.
        if not all([isinstance(operand, self.python_type) for operand in operands]):
            # In case the operands are not all integers, they should be entities that need converting to their primary keys:
            assert all([isinstance(operand, self.entity) for operand in operands]), self.AssertionMessage.invalid_target_entity_instance.value.format(self.entity)
            operands = [op.id for op in operands]
        return super().get_clause(query, operator, *operands)

class One2ManyFilter(RelatedFilter):
    """
    Specialized RelatedFilter strategy that expects a one2many relationship attribute which
    entity's primary key attribute is used to construct a IntFilter field filter strategy
    to instantiate this related filter with by default.
    Custom field filter strategies can be provided to overrule this default behaviour.
    """

    name = 'one2many_filter'
    operators = (Operator.in_, Operator.is_empty, Operator.is_not_empty)

    def __init__(self, attribute, joins=[], field_filters=[], where=None, key=None, verbose_name=None, priority_level=PriorityLevel.MEDIUM, **field_attributes):
        assert isinstance(attribute, orm.attributes.InstrumentedAttribute) and \
               isinstance(attribute.prop, orm.RelationshipProperty), self.AssertionMessage.invalid_relationship_attribute.value
        self.entity = attribute.prop.entity.entity
        self.admin = None
        entity_mapper = orm.class_mapper(self.entity)
        self.primary_key_attributes = [entity_mapper.get_property_by_column(pk).class_attribute for pk in entity_mapper.primary_key]
        field_filters = field_filters or [IntFilter(primary_key_attribute) for primary_key_attribute in self.primary_key_attributes]
        super().__init__(*field_filters, joins=joins+[attribute], where=where, key=key or attribute.key,
                         verbose_name=(verbose_name or field_attributes.get('name')),
                         priority_level=priority_level,
                         **field_attributes)

    def from_string(self, query, operand):
        """
        Convert the given stringified primary key operand value to query and return the corresponding entity instance.
        This will allow the field operand extraction to get the appropriate field filter operands.
        """
        if isinstance(operand, self.entity):
            return operand
        session = query.session
        return session.query(self.entity).get(operand)

    def field_operand(self, field_strategy, operand):
        """
        Turn the given entity instance operand into the appropriate field operand value
        for the given field strategy using its instrumented attribute.
        """
        assert isinstance(operand, self.entity), self.AssertionMessage.invalid_target_entity_instance.value.format(self.entity)
        return field_strategy.attribute.__get__(operand, None)

    def get_clause(self, query, operator, *operands):
        # Explicity support for the is_empty and is_not_empty operators on the one2many relation.
        # In this case, the underlying field filters are not needed and the related query's join is enough.
        # So it suffices for the resulting clause to check if the entity's id is in the related query (or not).
        if operator in (Operator.is_empty, Operator.is_not_empty):
            entity = query._mapper_zero().entity
            related_query = self.get_related_query(query)
            if operator == Operator.is_empty:
                return entity.id.notin_(related_query)
            else:
                return entity.id.in_(related_query)
        return super().get_clause(query, operator, *operands)

    def get_field_strategy(self):
        return self

    def get_operators(self):
        return self.operators

class SearchFilter(Action, AbstractModelFilter):

    render_hint = RenderHint.SEARCH_BUTTON
    name = 'search_filter'
    shortcut = QtGui.QKeySequence.StandardKey.Find
    _order_by_decorator = lambda x,text:x

    def get_state(self, model_context):
        state = Action.get_state(self, model_context)
        current_value = model_context.proxy.get_filter(self)
        if current_value is not None:
            search_text = current_value[0]
            state.modes = [FilterMode(
                search_text, search_text, checked=True
            )]
        return state

    @classmethod
    def decorate_query(cls, query, value, **kwargs):
        if value is not None:
            search_text, *search_strategies = value
            if search_text is not None and len(search_text.strip()) > 0:
                clauses = []
                for search_strategy in search_strategies:
                    filter_clause = search_strategy.get_search_clause(query, search_text)
                    if filter_clause is not None:
                        clauses.append(filter_clause)
                query = query.filter(sql.or_(*clauses))

                # If a search order is configured in the entity's entity_args,
                # sort the query based on the corresponding search strategies order by clauses.
                entity = query._mapper_zero().entity
                order_search_by = entity.get_order_search_by()
                if order_search_by is not None:
                    order_search_by = order_search_by if isinstance(order_search_by, tuple) else (order_search_by,)
                    # Reset any default ordering for the configured search order to take effect.
                    query = query.order_by(None)
                    order_by_clauses = [cls._order_by_decorator(order_by, search_text) for order_by in order_search_by]
                    if len(order_by_clauses) > 1:
                        from vfinance import sql as vf_sql
                        query = query.order_by(vf_sql.least(*order_by_clauses))
                    else:
                        query = query.order_by(*order_by_clauses)
        return query

    def gui_run(self, gui_context_name):
        # overload the action gui run to avoid a progress dialog
        # popping up while searching
        super(SearchFilter, self).gui_run(gui_context_name)

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        search_text = mode
        old_value = model_context.proxy.get_filter(self)
        value = None
        if search_text is not None and len(search_text) > 0:
            search_strategies = list(model_context.admin._get_search_fields(search_text))
            value = (search_text, *search_strategies)
        if old_value != value:
            model_context.proxy.filter(self, value)
            yield action_steps.RefreshItemView()

search_filter = SearchFilter()


@dataclass
class FilterMode(Mode):

    checked: bool = False

    def __init__(self, value, verbose_name, checked=False):
        super(FilterMode, self).__init__(value=value, verbose_name=verbose_name)
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
    filter_strategy = ChoicesFilter

    def __init__(self, *attributes, default=All, verbose_name=None, joins=[], where=None):
        """
        :param attribute: the attribute on which to filter, this attribute
            may contain dots to indicate relationships that need to be followed, 
            eg.  'person.name'

        :param default: the default value to filter on when the view opens,
            defaults to showing all records.
        
        :param verbose_name: the name of the filter as shown to the user, defaults
            to the name of the field on which to filter.
        """
        self.joins = joins
        self.where = where
        self.filter_strategy = self.get_strategy(*attributes)
        self.attribute = attributes[0]
        self.default = default
        self.verbose_name = verbose_name
        self.exclusive = True
        self.filter_names = []

    def get_strategy(self, *attributes):
        field_filter_strategy = self.filter_strategy(*attributes, where=self.where)
        if self.joins:
            return RelatedFilter(field_filter_strategy, joins=self.joins, where=self.where)
        return field_filter_strategy

    def get_name(self):
        return '{}_{}'.format(self.name, self.attribute.key)

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        new_value = mode
        old_value = model_context.proxy.get_filter(self)
        if old_value != new_value:
            model_context.proxy.filter(self, new_value)
            yield action_steps.RefreshItemView()

    def get_operator(self, values):
        return Operator.in_ if values else Operator.is_empty

    def get_operands(self, query, values):
        return values

    def decorate_query(self, query, values):
        if All in values:
            return query
        operator = self.get_operator(values)
        operands = self.get_operands(query, values)
        filter_clause = self.filter_strategy.get_clause(query, operator, *operands)
        return query.filter(filter_clause)

    def get_state(self, model_context):
        """
        :return:  a :class:`filter_data` object
        """
        state = super(Filter, self).get_state(model_context)
        session = model_context.session
        entity = model_context.admin.entity
        attributes = model_context.admin.get_field_attributes(self.attribute.key)
        self.filter_names.append(attributes['name'])
        query = session.query(self.attribute).select_from(entity)
        query = query.distinct()

        modes = list()
        for value in query:
            if 'to_string' in attributes:
                verbose_name = attributes['to_string'](value[0])
            else:
                verbose_name = value[0]
            if attributes.get('translate_content', False):
                verbose_name = ugettext(verbose_name)
            mode = FilterMode(value=value[0],
                              verbose_name=verbose_name,
                              checked=((value[0]==self.default) or (self.exclusive==False)))
        
            # option_name name can be of type ugettext_lazy, convert it to unicode
            # to make it sortable
            modes.append(mode)

        state.verbose_name = self.verbose_name or self.filter_names[0]
        # sort outside the query to sort on the verbose name of the value
        modes.sort(key=lambda state:str(state.verbose_name))
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

    def __init__(self, *attributes, default=All, verbose_name=None, exclusive=True, joins=[], where=None):
        super().__init__(*attributes, default=default, verbose_name=verbose_name, joins=joins, where=where)
        self.exclusive = exclusive
        self.render_hint = RenderHint.EXCLUSIVE_GROUP_BOX if exclusive else RenderHint.NON_EXCLUSIVE_GROUP_BOX

class ComboBoxFilter(Filter):
    """Filter where the items are displayed in a QComboBox"""

    render_hint = RenderHint.COMBO_BOX
    name = 'combo_box_filter'
