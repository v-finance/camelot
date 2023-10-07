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

from dataclasses import dataclass, field
from typing import List, ClassVar, Any
from decimal import Decimal

from ....admin.admin_route import Route
from ....core.item_model import (
    PreviewRole, SuffixRole, PrefixRole, SingleStepRole,
    PrecisionRole, MinimumRole, MaximumRole, FocusPolicyRole
)
from ....core.qt import Qt
from camelot.core.naming import initial_naming_context
from .customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core import constants


@dataclass
class FloatDelegate(CustomDelegate, metaclass=DocumentationMetaclass):
    """Custom delegate for float values"""

    calculator: bool = True
    decimal: bool = False
    action_routes: List[Route] = field(default_factory=list)

    horizontal_align: ClassVar[Any] = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

    @classmethod
    def get_editor_class(cls):
        return editors.FloatEditor

    @classmethod
    def get_standard_item(cls, locale, model_context):
        minimum, maximum = model_context.field_attributes.get('minimum'), model_context.field_attributes.get('maximum')
        minimum = minimum if minimum is not None else constants.camelot_minfloat
        maximum = maximum if maximum is not None else constants.camelot_maxfloat
        item = super().get_standard_item(locale, model_context)
        cls.set_item_editability(model_context, item, False)
        item.roles[FocusPolicyRole] = model_context.field_attributes.get('focus_policy')
        item.roles[SuffixRole] = model_context.field_attributes.get('suffix')
        item.roles[PrefixRole] = model_context.field_attributes.get('prefix')
        single_step = model_context.field_attributes.get('single_step')
        if single_step is not None:
            item.roles[SingleStepRole] = initial_naming_context._bind_object(Decimal(single_step))
        precision = model_context.field_attributes.get('precision', 2)
        item.roles[PrecisionRole] = precision
        item.roles[MinimumRole] = initial_naming_context._bind_object(Decimal(minimum))
        item.roles[MaximumRole] = initial_naming_context._bind_object(Decimal(maximum))
        # Set default precision of 2 when precision is undefined, instead of using the default argument of the dictionary's get method,
        # as that only handles the precision key not being present, not it being explicitly set to None.
        if precision is None:
            precision = 2
        if model_context.value is not None:
            item.roles[Qt.ItemDataRole.EditRole] = initial_naming_context._bind_object(Decimal(model_context.value))
            value_str = str(
                locale.toString(float(model_context.value), 'f', precision)
            )
            if model_context.field_attributes.get('suffix') is not None:
                value_str = value_str + ' ' + model_context.field_attributes.get('suffix')
            if model_context.field_attributes.get('prefix') is not None:
                value_str = model_context.field_attributes.get('prefix') + ' ' + value_str
            item.roles[PreviewRole] = value_str
        else:
            item.roles[PreviewRole] = str()
        return item

    def setEditorData(self, editor, index):
        if index.model() is None:
            return
        self.set_default_editor_data(editor, index)
        suffix = index.data(SuffixRole)
        prefix = index.data(PrefixRole)
        single_step = index.data(SingleStepRole)
        precision = index.data(PrecisionRole)
        minimum = index.data(MinimumRole)
        maximum = index.data(MaximumRole)
        focus_policy = index.data(FocusPolicyRole)
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.set_suffix(suffix)
        editor.set_prefix(prefix)
        editor.set_single_step(single_step)
        editor.set_precision(precision)
        editor.set_minimum(minimum)
        editor.set_maximum(maximum)
        editor.set_focus_policy(focus_policy)
        editor.set_value(value)
        self.update_field_action_states(editor, index)

    def setModelData(self, editor, model, index):
        # convert Decimal to float
        value = editor.get_value()
        value = float(value) if value is not None else value
        model.setData(index, value)


