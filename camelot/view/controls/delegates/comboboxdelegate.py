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
from typing import List, Optional

logger = logging.getLogger('camelot.view.controls.delegates.comboboxdelegate')

from .customdelegate import CustomDelegate, DocumentationMetaclass

from ....core.item_model import PreviewRole, ChoicesRole
from ....core.naming import initial_naming_context
from ....core.qt import Qt
from ....admin.icon import CompletionValue
from ....admin.admin_route import Route
from ...art import ColorScheme



none_name = list(initial_naming_context._bind_object(None))
none_item = CompletionValue(none_name, verbose_name=' ')._to_dict()

@dataclass
class ComboBoxDelegate(CustomDelegate, metaclass=DocumentationMetaclass):

    action_routes: List[Route] = field(default_factory=list)
    # choices can be static, so they are not required to go in the standard item
    choices: Optional[List[CompletionValue]] = field(default_factory=list)

    @classmethod
    def get_editor_class(cls):
        return None

    @classmethod
    def value_to_string(cls, value, locale, field_attributes) -> Optional[str]:
        choices = field_attributes.get('choices', [])
        for key, verbose in choices:
            if key == value:
                return str(verbose)
        if value is None:
            return ' '
        # the model has a value that is not in the list of choices,
        # still try to display it
        return str(value)

    @classmethod
    def get_choices_data(cls, choices) -> List[CompletionValue]:
        none_available = False
        choicesData = []
        for obj, verbose_name in choices:
            if obj is None:
                none_available = True
            choicesData.append(CompletionValue(
                value=initial_naming_context._bind_object(obj),
                verbose_name=verbose_name
                )._to_dict())
        if not none_available:
            choicesData.append(none_item)
        return choicesData

    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super().get_standard_item(locale, model_context)
        value_name = list(initial_naming_context._bind_object(model_context.value))
        # eventually, all values should be names, so this should happen in the
        # custom delegate class
        item.roles[Qt.ItemDataRole.EditRole] = value_name
        cls.set_item_editability(model_context, item, True)
        item.roles[PreviewRole] = cls.value_to_string(model_context.value, locale, model_context.field_attributes)
        choices = model_context.field_attributes.get('choices')
        if choices is not None:
            choicesData = cls.get_choices_data(choices)
            if value_name not in (completion['value'] for completion in choicesData):
                choicesData = choicesData + [CompletionValue(
                    value=initial_naming_context._bind_object(model_context.value),
                    verbose_name=str(model_context.value),
                    background = ColorScheme.VALIDATION_ERROR.name(),
                    virtual = True
                    )._to_dict()]
            item.roles[ChoicesRole] = choicesData
        return item

    def setEditorData(self, editor, index):
        if index.model() is None:
            return
        self.set_default_editor_data(editor, index)
        choices = index.data(ChoicesRole)
        value = index.data(Qt.ItemDataRole.EditRole)
        editor.set_choices(choices)
        editor.set_value(value)
        # update actions
        self.update_field_action_states(editor, index)

@dataclass
class EnumDelegate(ComboBoxDelegate):
    """
    An enum delegate is a specialized combobox delegate that uses the fact that
    the set out of which the choices are made is fixed.  That is, the set of choices
    itself might change, but each choice is a member of a fixed set of values.
    """

    @classmethod
    def value_to_string(cls, value, locale, field_attributes) -> Optional[str]:
        if value is None:
            return ' '
        return field_attributes['types'].get_verbose_name(value)
