import logging
from dataclasses import dataclass
from typing import Optional

from .customdelegate import CustomDelegate
from ....core.item_model import PreviewRole

logger = logging.getLogger(__name__)


@dataclass
class StatusDelegate(CustomDelegate):

    @classmethod
    def get_editor_class(cls):
        return None

    @classmethod
    def value_to_string(cls, value, locale, field_attributes) -> Optional[str]:
        choices = field_attributes.get('choices', [])
        for key, verbose in choices:
            if key == value:
                return str(verbose)
        else:
            assert (value is None) or False        

    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super().get_standard_item(locale, model_context)
        cls.set_item_editability(model_context, item, False)
        if model_context.value is not None:
            item.roles[PreviewRole] = cls.value_to_string(model_context.value, locale, model_context.field_attributes)
        return item

    def setEditorData(self, editor, index):
        if index.model() is None:
            return
        value = index.model().data(index, PreviewRole)
        editor.set_value(value)
