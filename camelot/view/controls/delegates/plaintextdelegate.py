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

import logging
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger('camelot.view.controls.delegates.plaintextdelegate')


from ....admin.admin_route import Route
from ....core.item_model import PreviewRole, ValidatorStateRole, CompleterStateRole
from ....core.qt import Qt
from .customdelegate import CustomDelegate

from camelot.view.controls import editors
from camelot.view.validator import AbstractValidator

DEFAULT_COLUMN_WIDTH = 20

@dataclass
class PlainTextDelegate(CustomDelegate):
    """Custom delegate for simple string values"""

    length: int = DEFAULT_COLUMN_WIDTH
    echo_mode: Optional[int] = None
    column_width: Optional[int] = None
    action_routes: List[Route] = field(default_factory=list)
    validator_type: Optional[str] = None
    completer_type: Optional[str] = None

    def __post_init__(self, parent):
        super().__post_init__(parent)
        char_width = self._font_metrics.averageCharWidth()
        self._width = char_width * min( DEFAULT_COLUMN_WIDTH, self.length or DEFAULT_COLUMN_WIDTH )

    @classmethod
    def get_editor_class(cls):
        return editors.TextLineEditor

    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super().get_standard_item(locale, model_context)
        cls.set_item_editability(model_context, item, False)
        item.roles[ValidatorStateRole] = model_context.field_attributes.get('validator_state')
        item.roles[CompleterStateRole] = model_context.field_attributes.get('completer_state')
        if model_context.value is not None:
            value = str(model_context.value)
            # If a validator is defined, use it to format the model value:
            validator = AbstractValidator.get_validator(model_context.field_attributes.get('validator_type'))
            if validator is not None:
                validator.set_state(model_context.field_attributes.get('validator_state'))
                value = validator.format_value(value)
            item.roles[PreviewRole] = value
            # Set EditRole to possible reformatted value, to apply programatically triggered changes.
            item.roles[Qt.ItemDataRole.EditRole] = value
        return item

    def setEditorData(self, editor, index):
        if index.model() is None:
            return
        self.set_default_editor_data(editor, index)
        completer_state = index.data(CompleterStateRole)
        validator_state = index.data(ValidatorStateRole)
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.set_completer_state(completer_state)
        editor.set_validator_state(validator_state)
        editor.set_value(value)
        self.update_field_action_states(editor, index)
