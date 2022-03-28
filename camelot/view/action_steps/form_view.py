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
from typing import List, Any, Tuple, Optional, Dict, Union, Type
from dataclasses import dataclass, InitVar, field

from camelot.core.serializable import DataclassSerializable
from ..controls.delegates import ComboBoxDelegate
from ..proxy.collection_proxy import CollectionProxy
from ..workspace import show_top_level
from ...admin.action.base import ActionStep, Action, State
from ...admin.action.form_action import FormActionModelContext
from ...admin.admin_route import AdminRoute, Route
from ...admin.object_admin import ObjectAdmin
from ...core.item_model import AbstractModelProxy, ProxyRegistry
from ...core.naming import initial_naming_context
from ...core.qt import is_deleted


@dataclass
class OpenFormView(ActionStep):
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

    .. attribute:: top_level

       Display the form view top-level, or as a tab in the workspace,
       defaults to `True`.

    """
    obj: InitVar[Any]
    proxy: AbstractModelProxy
    admin: ObjectAdmin

    admin_name: str = field(init=False)
    actions: List[Action] = field(init=False)
    action_states: List[Tuple[Route, State]] = field(default_factory=list)
    top_toolbar_actions: List[Action] = field(init=False)
    _columns: List[Tuple[Optional[Any], Dict[str, Union[Type[ComboBoxDelegate]]]]] = field(init=False)
    _form_display: bytes = field(init=False)
    admin_route: AdminRoute = field(init=False)
    objects: List[Any] = field(init=False)
    row: int = field(init=False)

    def __post_init__(self, obj):
        assert obj is not None
        assert isinstance(self.proxy, AbstractModelProxy)
        self.admin_name = self.admin.get_name()
        self.actions = self.admin.get_form_actions(None)
        get_form_toolbar_actions = self.admin.get_form_toolbar_actions
        self.top_toolbar_actions = get_form_toolbar_actions()
        self._columns = self.admin.get_fields()
        self._form_display = self.admin.get_form_display()._to_bytes()
        self.admin_route = self.admin.get_admin_route()
        self._add_action_states(self.admin, self.proxy, self.actions + self.top_toolbar_actions, self.action_states)

        self.objects = [obj]
        self.row = self.proxy.index(obj)
        self.proxy = ProxyRegistry.register(self.proxy)

        self.top_level = True
        self.title = u' '

    @staticmethod
    def _add_action_states(admin, proxy, actions, action_states):
        model_context = FormActionModelContext()
        model_context.admin = admin
        model_context.proxy = proxy
        for action_route in actions:
            action = initial_naming_context.resolve(action_route.route)
            state = action.get_state(model_context)
            action_states.append((action_route.route, state))

    def get_objects(self):
        """Use this method to get access to the objects to change in unit tests

        :return: the list of objects to display in the form view
        """
        return self.objects

    def render(self, gui_context):
        from camelot.view.controls.formview import FormView

        model = CollectionProxy(self.admin_route)
        list(model.add_columns((fn for fn, fa in self._columns)))
        model.set_value(self.proxy)

        form = FormView(title=self.title, admin=self.admin, model=model,
                        columns=self._columns, form_display=self._form_display,
                        index=self.row)
        form.set_actions([action.route for action in self.actions], self.action_states)
        form.set_toolbar_actions([action.route for action in self.top_toolbar_actions], self.action_states)
        return form

    def gui_run( self, gui_context ):
        window = gui_context.get_window()
        formview = self.render(gui_context)
        if formview is not None:
            if self.top_level == True:
                formview.setObjectName('form.{}.{}'.format(
                    self.admin_name, id(formview)
                ))
                show_top_level(formview, window, self.admin.form_state)
            else:
                gui_context.workspace.set_view(formview)


@dataclass
class ChangeFormIndex(ActionStep, DataclassSerializable):

    def gui_run( self, gui_context ):
        # a pending request might change the number of rows, and therefor
        # the new index
        # submit all pending requests to the model thread
        if is_deleted(gui_context.widget_mapper):
            return
        gui_context.widget_mapper.model().timeout_slot()
        # wait until they are handled
        super(ChangeFormIndex, self).gui_run(gui_context)

class ToFirstForm(ChangeFormIndex):
    """
    Show the first object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToFirstForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toFirst()

class ToNextForm(ChangeFormIndex):
    """
    Show the next object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToNextForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toNext()
        
class ToLastForm(ChangeFormIndex):
    """
    Show the last object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToLastForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toLast()
        
class ToPreviousForm(ChangeFormIndex):
    """
    Show the previous object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToPreviousForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toPrevious()

