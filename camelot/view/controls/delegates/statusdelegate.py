import logging
from dataclasses import dataclass

logger = logging.getLogger('camelot.view.controls.delegates.statusdelegate')

from .customdelegate import CustomDelegate
from .. import editors
from ....core.item_model import PreviewRole


@dataclass
class StatusDelegate(CustomDelegate):

    @classmethod
    def get_editor_class(cls):
        return editors.LabelEditor

    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super().get_standard_item(locale, model_context)
        cls.set_item_editability(model_context, item, False)
        choices = model_context.field_attributes.get('choices', [])
        for key, verbose in choices:
            if key == model_context.value:
                item.roles[PreviewRole] = str(verbose)
                break
        else:
            assert (model_context.value is None) or False
        return item

    def setEditorData(self, editor, index):
        if index.model() is None:
            return
        value = index.model().data(index, PreviewRole)
        editor.set_value(value)
