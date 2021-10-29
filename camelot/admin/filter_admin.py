"""
Admin classes for Filter strategies
"""

import logging

from .action import list_filter
from .action.list_action import FilterValue
from .object_admin import ObjectAdmin
from ..view.controls import delegates

LOGGER = logging.getLogger('camelot.admin.filter_admin')

class FilterValueAdmin(ObjectAdmin):

    list_display = ['value_1', 'value_2']

    def __init__(self, app_admin, entity):
        assert issubclass(entity, FilterValue), '{} is not a FilterValue class'.format(entity)
        super().__init__(app_admin, entity)

    def get_name(self):
        return self.entity.filter_strategy.name

# Create and register filter value classes and related admins for each filter strategy
# that has not got one registered already.
for strategy_cls, delegate in [
    (list_filter.StringFilter,  delegates.PlainTextDelegate),
    (list_filter.BoolFilter,    delegates.BoolDelegate),
    (list_filter.DateFilter,    delegates.DateDelegate),
    (list_filter.DecimalFilter, delegates.FloatDelegate),
    (list_filter.IntFilter,     delegates.IntegerDelegate),
    (list_filter.TimeFilter,    delegates.TimeDelegate),
    #(list_filter.RelatedFilter, delegates.PlainTextDelegate),
    ]:

    try:
        FilterValue.get_filter_value(strategy_cls)
    except Exception:
        cls_name = "%sValue" % strategy_cls.__name__
        new_value_cls = type(cls_name, (FilterValue,), {})
        new_value_cls.filter_strategy = strategy_cls
        FilterValue.register(strategy_cls, new_value_cls)

        class Admin(FilterValueAdmin):

            field_attributes = {
                'value_1': {'delegate': delegate},
                'value_2': {'delegate': delegate},
            }

        new_value_cls.Admin = Admin
