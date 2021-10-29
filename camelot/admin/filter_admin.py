"""
Admin classes for Filter strategies
"""

import logging

from .action import list_filter
from .action.list_action import FilterValue
from .object_admin import ObjectAdmin

LOGGER = logging.getLogger('camelot.admin.filter_admin')

class FilterValueAdmin(ObjectAdmin):

    def __init__(self, app_admin, entity):
        assert issubclass(entity, FilterValue), '{} is not a FilterValue class'.format(entity)
        super().__init__(app_admin, entity)

    list_display = ['value_1', 'value_2']
