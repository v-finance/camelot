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
Various ``ActionStep`` subclasses to create and manipulate a form view in the
context of the `Qt` model-view-delegate framework.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional

from .item_view import AbstractCrudView
from ..forms import AbstractForm
from ...admin.action.base import ActionStep
from ...admin.admin_route import Route, AdminRoute
from ...core.item_model import AbstractModelProxy
from ...core.naming import initial_naming_context
from ...core.serializable import DataclassSerializable

from vfinance.view.controls.delegates.richtextdelegate import RichTextDelegate

@dataclass
class OpenFormView(AbstractCrudView):
    """Open the form view for a list of objects, in a non blocking way.

    :param object: the object to display in the form view.
    :param proxy: a model proxy that represents the underlying collection where the given object is part of.
    :param admin: the admin class to use to display the form

    .. attribute:: row

        Which object to display when opening the form, defaults to the first
        object, so row is 0 by default

    .. attribute:: actions

        A list of `camelot.admin.action.base.Action` objects to be displayed
        at the side of the form, this defaults to the ones returned by the
        admin

    .. attribute:: top_toolbar_actions

        A list of `camelot.admin.action.base.Action` objects to be displayed
        at the top toolbar of the form, this defaults to the ones returned by the
        admin

    """

    fields: Dict[str, dict] = field(init=False)
    form: AbstractForm = field(init=False)
    admin_route: AdminRoute = field(init=False)
    row: int = field(init=False)
    form_state: str = field(init=False)
    blocking: bool = False
    qml: bool = False
    auto_update: bool = True

    def __post_init__(self, value, admin, proxy):
        assert value is not None
        assert (proxy is None) or (isinstance(proxy, AbstractModelProxy))
        self.fields = [[f, {
            'hide_title':fa.get('hide_title', False),
            'verbose_name':str(fa['name']),
            'column_span': fa.get('column_span', 1),
            'minimum_columns': self._minimum_columns(admin, fa),
            }] for f, fa in admin.get_fields()]
        self.form = admin.get_form_display()
        self.admin_route = admin.get_admin_route()
        self.qml = admin.qml_form
        if proxy is None:
            proxy = admin.get_proxy([value])
            self.row = 0
        else:
            self.row = proxy.index(value)
        self.close_route = AdminRoute._register_action_route(
            self.admin_route, admin.form_close_action
        )
        self.title = admin.get_verbose_identifier(value)
        self.form_state = admin.form_state
        self._add_actions(admin, self.actions)
        super().__post_init__(value, admin, proxy)
        model_context = initial_naming_context.resolve(self.model_context_name)
        model_context.current_row = self.row
        model_context.selection_count = 1

    def _minimum_columns(self, admin, fa):
        # Make rich text fields span 4 columns minimum
        if fa.get('delegate', None) == RichTextDelegate:
           return 4
        # Use # of columns for One2Many fields
        target = fa.get('target', None)
        if target is not None:
            related_admin = fa.get('admin', admin.get_related_admin(target))
            direction = fa.get('direction', 'onetomany')
            python_type = fa.get('python_type')
            if direction.endswith('many') and python_type == list and related_admin:
                num_columns = 0
                for field in related_admin.get_columns():
                    num_columns += related_admin.get_field_attributes(field).get('column_span', 1)
                return num_columns

    @staticmethod
    def _add_actions(admin, actions):
        actions.extend(admin.get_form_actions(None))
        actions.extend(admin.get_form_toolbar_actions())

    def get_admin(self):
        """Use this method to get access to the admin in unit tests"""
        return initial_naming_context.resolve(self.admin_route)

@dataclass
class HighlightField(DataclassSerializable):

    label: str = None # The label of the field to search for
    action_route: Optional[Route] = None # Field action to highlight
    action_mode: Optional[str] = None # The mode of the action to highlight

@dataclass
class HighlightForm(ActionStep, DataclassSerializable):

    tab: Optional[str] = None # The form tab
    label: Optional[HighlightField] = None # A field label to highlight
    label_delegate: bool = False # Highlight delegate associated with label
    label_delegate_focus: bool = False # Focus delegate associated with label
    table_label: Optional[str] = None # Label of the table for table_row and table_column
    table_row: Optional[int] = None # Table row to highlight
    table_column: Optional[str] = None # Table column to highlight
    action_route: Optional[Route] = None # Action to highlight
    action_menu_route: Optional[Route] = None # Menu to open
    action_menu_mode: Optional[str] = None # Menu mode (verbose name) to highlight
    select_all: bool = False
    select_row: Optional[int] = None

    #action_cls_state: Optional[?] = None
    #group_box: Optional[?] = None
    form_state: Optional[str] = None
    field_name: Optional[str] = None

@dataclass
class CloseMenu(ActionStep, DataclassSerializable):

    action_menu_route: Optional[Route] = None # Menu to close
