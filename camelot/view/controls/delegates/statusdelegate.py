import logging
from dataclasses import dataclass

logger = logging.getLogger('camelot.view.controls.delegates.statusdelegate')

from .customdelegate import CustomDelegate, DocumentationMetaclass

from ....core.item_model import PreviewRole


@dataclass
class StatusDelegate(CustomDelegate, metaclass=DocumentationMetaclass):

    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super().get_standard_item(locale, model_context)
        choices = model_context.field_attributes.get('choices', [])
        for key, verbose in choices:
            if key == model_context.value:
                item.roles[PreviewRole] = str(verbose)
                break
        else:
            assert False
        return item
