"""
Admin classes for Filter strategies
"""
import copy
import logging

from camelot.core.utils import ugettext_lazy as _

from .action import list_filter
from .action.list_action import FilterValue
from .object_admin import ObjectAdmin
from ..view.controls import delegates
from ..view import forms

LOGGER = logging.getLogger('camelot.admin.filter_admin')

class FilterValueAdmin(ObjectAdmin):

    verbose_name = _('Filter')

    form_display = forms.Form([
        forms.GridForm([ ['operator_prefix', 'value_1'],
                         ['operator_infix',  'value_2']]),
        forms.Stretch()])

    field_attributes = {
        'operator_prefix': {'editable': False, 'delegate': delegates.LabelDelegate},
        'value_1': {'editable': True, 'nullable': False},
        # 2nd filter value (i.e. 3rd operand) and operator infix should only be visible in case of a ternary operator (min arity >= 3):
        'operator_infix': {'editable': False, 'delegate': delegates.LabelDelegate, 'visible': lambda o: o.operator.arity.minimum > 2},
        'value_2': {'editable': True, 'visible': lambda o: o.operator.arity.minimum > 2, 'nullable': lambda o: o.operator.arity.minimum <= 2},
    }

    def __init__(self, app_admin, entity):
        assert issubclass(entity, FilterValue), '{} is not a FilterValue class'.format(entity)
        super().__init__(app_admin, entity)

    def get_name(self):
        return self.entity.filter_strategy.name

# Create and register filter value classes and related admins for each filter strategy
# that has not got one registered already.
for strategy_cls, delegate in [
    (list_filter.StringFilter,   delegates.PlainTextDelegate),
    (list_filter.BoolFilter,     delegates.BoolDelegate),
    (list_filter.DateFilter,     delegates.DateDelegate),
    (list_filter.DecimalFilter,  delegates.FloatDelegate),
    (list_filter.IntFilter,      delegates.IntegerDelegate),
    (list_filter.RelatedFilter,  delegates.PlainTextDelegate),
    (list_filter.ChoicesFilter,  delegates.ComboBoxDelegate),
    (list_filter.MonthsFilter,   delegates.MonthsDelegate),
    (list_filter.Many2OneFilter, delegates.Many2OneDelegate),
    (list_filter.One2ManyFilter, delegates.Many2OneDelegate),
    ]:
    try:
        FilterValue.for_strategy(strategy_cls)
    except Exception:
        cls_name = "%sValue" % strategy_cls.__name__
        new_value_cls = type(cls_name, (FilterValue,), {})
        new_value_cls.filter_strategy = strategy_cls
        FilterValue.register(strategy_cls, new_value_cls)

        class Admin(FilterValueAdmin):

            field_attributes = {h:copy.copy(v) for h,v in FilterValueAdmin.field_attributes.items()}
            attributes_dict = {
                    'value_1': {'delegate': delegate},
                    'value_2': {'delegate': delegate},
                }
            for field_name, attributes in attributes_dict.items():
                field_attributes.setdefault(field_name, {}).update(attributes)

        if strategy_cls == list_filter.ChoicesFilter:
            Admin.field_attributes['value_1'].update({'choices': lambda o: o.strategy.choices})
        if strategy_cls == list_filter.DecimalFilter:
            Admin.field_attributes['value_1'].update({'precision': lambda o: (o.strategy.precision if not isinstance(o.strategy.precision, tuple) else o.strategy.precision[1]) or 2})
            Admin.field_attributes['value_2'].update({'precision': lambda o: (o.strategy.precision if not isinstance(o.strategy.precision, tuple) else o.strategy.precision[1]) or 2})

        new_value_cls.Admin = Admin
