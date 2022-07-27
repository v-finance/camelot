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
Various ``ActionStep`` subclasses that manipulate the `item_view` of 
the `ListActionGuiContext`.
"""

from dataclasses import dataclass, InitVar, field
from typing import Union, List, Tuple, Any
import json
import logging

from ...admin.admin_route import Route, RouteWithRenderHint
from ...admin.action.base import ActionStep, State
from ...admin.action.list_action import ListActionModelContext
from ...admin.action.list_filter import SearchFilter, Filter, All
from ...admin.action.application_action import model_context_naming, model_context_counter
from ...admin.object_admin import ObjectAdmin
from ...core.item_model import AbstractModelProxy, ProxyRegistry
from ...core.naming import initial_naming_context
from ...core.qt import Qt
from ...core.serializable import DataclassSerializable
from ...core.utils import ugettext_lazy
from ..workspace import show_top_level
from ..proxy.collection_proxy import (
    rowcount_name, rowdata_name, setcolumns_name, RowModelContext
)
from ..qml_view import qml_action_step, is_cpp_gui_context

LOGGER = logging.getLogger(__name__)

@dataclass
class Sort( ActionStep, DataclassSerializable ):
    """Sort the items in the item view ( list, table or tree )

            :param column: the index of the column on which to sort
            :param order: a :class:`Qt.SortOrder`
    """
    column: int
    order: Qt.SortOrder = Qt.SortOrder.AscendingOrder

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        step = json.loads(serialized_step)
        model = gui_context.get_item_model()
        if model is not None:
            model.sort( step["column"], step["order"] )

@dataclass
class CrudActions(DataclassSerializable):
    """
    A data class which contains the routes to crud actions available
    to the gui to invoke.
    """

    admin: InitVar
    row_count: Route = field(init=False, default=rowcount_name)
    set_columns: Route = field(init=False, default=setcolumns_name)
    row_data: Route = field(init=False, default=rowdata_name)

@dataclass
class AbstractCrudView(ActionStep, DataclassSerializable):
    """Abstract action step to define attributes common to all item view
    based action steps
    """

    value: InitVar[Any]
    admin: InitVar[ObjectAdmin]
    proxy: InitVar[AbstractModelProxy] = None

    title: Union[str, ugettext_lazy] = field(init=False)
    proxy_route: Route = field(init=False)
    actions: List[RouteWithRenderHint] = field(init=False, default_factory=list)
    action_states: List[Tuple[Route, State]] = field(default_factory=list)
    crud_actions: CrudActions = field(init=False)
    close_route: Route = field(init=False)

    def __post_init__(self, value, admin, proxy):
        assert value is not None
        assert isinstance(proxy, AbstractModelProxy)
        self.crud_actions = CrudActions(admin)
        self.proxy_route = ProxyRegistry.register(proxy)
        self._add_action_states(admin, proxy, self.actions, self.action_states)

    @staticmethod
    def _add_action_states(admin, proxy, actions, action_states):
        model_context = ListActionModelContext()
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
        return ProxyRegistry.get(self.proxy_route).get_model()

@dataclass
class UpdateTableView(AbstractCrudView):
    """Change the admin and or value of an existing table view
    
    :param admin: an `camelot.admin.object_admin.ObjectAdmin` instance
    :param value: a list of objects or a query
    
    """

    search_text: InitVar[Union[str, None]] = None

    columns: List[str] = field(init=False)
    list_action: Union[Route, None] = field(init=False)

    def __post_init__(self, value, admin, proxy, search_text):
        assert (search_text is None) or isinstance(search_text, str)
        self.title = admin.get_verbose_name_plural()
        self._add_actions(admin, self.actions)
        self.columns = admin.get_columns()
        self.list_action = admin.get_list_action()
        self.close_route = None
        if proxy is None:
            proxy = admin.get_proxy(value)
        if search_text is not None:
            for action_route in self.actions:
                action = initial_naming_context.resolve(action_route.route)
                if isinstance(action, SearchFilter):
                    search_strategies = list(admin._get_search_fields(search_text))
                    search_value = (search_text, *search_strategies)
                    proxy.filter(action, search_value)
                    break
            else:
                LOGGER.warn('No SearchFilter found to apply search text')
        self.set_filters(self.action_states, proxy)
        super().__post_init__(value, admin, proxy)

    @staticmethod
    def _add_actions(admin, actions):
        actions.extend(admin.get_list_actions())
        actions.extend(admin.get_filters())
        actions.extend(admin.get_list_toolbar_actions())

    @staticmethod
    def set_filters(action_states, model):
        for action_state in action_states:
            route = tuple(action_state[0])
            action = initial_naming_context.resolve(route)
            if not isinstance(action, Filter):
                continue
            state = action_state[1]
            values = [mode.value for mode in state.modes if mode.checked]
            # if all modes are checked, replace with [All]
            if len(values) == len(state.modes):
                values = [All]
            model.filter(action, values)

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        step = json.loads(serialized_step)
        cls.update_table_view(gui_context.view, step)
        gui_context.view.change_title(step['title'])

        gui_context.view.findChild(Qt)


@dataclass
class OpenTableView( UpdateTableView ):
    """Open a new table view in the workspace.
    
    :param admin: an `camelot.admin.object_admin.ObjectAdmin` instance
    :param value: a list of objects or a query

    .. attribute:: title
        the title of the the new view
        
    .. attribute:: subclasses
        a tree of subclasses to be displayed on the left of the

    .. attribute:: new_tab
        open the view in a new tab instead of the current tab
        
    """
    new_tab: bool = False
    admin_route: Route = field(init=False)
    model_context_name: Route = field(init=False)

    def __post_init__(self, value, admin, proxy, search_text):
        super().__post_init__(value, admin, proxy, search_text)
        self.admin_route = admin.get_admin_route()
        # Create the model_context for the table view
        model_context = RowModelContext()
        model_context.admin = admin
        model_context.proxy = admin.get_proxy(value)
        # todo : remove the concept of a validator (taken from CollectionProxy)
        model_context.validator = admin.get_validator()
        self.model_context_name = model_context_naming.bind(str(next(model_context_counter)), model_context)

    @classmethod
    def render(cls, gui_context, step):
        from camelot.view.controls.tableview import TableView
        table_view = TableView(gui_context, tuple(step['admin_route']))
        cls.update_table_view(table_view, step)
        return table_view
        
    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        step = json.loads(serialized_step)
        table_view = cls.render(gui_context, step)
        if gui_context.workspace is not None:
            if step['new_tab'] == True:
                gui_context.workspace.add_view(table_view)
            else:
                gui_context.workspace.set_view(table_view)
        else:
            table_view.setObjectName('table.{}.{}'.format(
                step['admin_name'], id(table_view)
            ))
            show_top_level(table_view, None)
        table_view.change_title(step['title'])
        table_view.setFocus(Qt.FocusReason.PopupFocusReason)



@dataclass
class OpenQmlTableView(OpenTableView):
    """Open a new table view in the workspace.
    
    :param admin: an `camelot.admin.object_admin.ObjectAdmin` instance
    :param value: a list of objects or a query

    .. attribute:: title
        the title of the the new view

    .. attribute:: new_tab
        open the view in a new tab instead of the current tab
        
    """

    @classmethod
    def render(cls, gui_context, action_step_name, serialized_step):
        response = qml_action_step(gui_context, action_step_name,
                serialized_step)
        return response, None

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        cls.render(gui_context, 'OpenTableView', serialized_step)

@dataclass
class ToFirstRow(ActionStep, DataclassSerializable):
    """Move to the first row in a table"""

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        if is_cpp_gui_context(gui_context):
            qml_action_step(gui_context, 'ToFirstRow')
        else:
            gui_context.item_view.selectRow( 0 )


@dataclass
class ToLastRow(ActionStep, DataclassSerializable):
    """Move to the last row in a table"""

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        if is_cpp_gui_context(gui_context):
            qml_action_step(gui_context, 'ToLastRow')
        else:
            item_view = gui_context.item_view
            item_view.selectRow( item_view.model().rowCount() - 1 )


@dataclass
class ClearSelection(ActionStep, DataclassSerializable):
    """Deselect all selected items."""

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        if is_cpp_gui_context(gui_context):
            qml_action_step(gui_context, 'ClearSelection', serialized_step)
        else:
            gui_context.item_view.clearSelection()


@dataclass
class SetSelection(ActionStep, DataclassSerializable):
    """Set selection."""

    rows: List[int] = field(default_factory=list)


@dataclass
class RefreshItemView(ActionStep, DataclassSerializable):
    """
    Refresh only the current item view
    """

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        if is_cpp_gui_context(gui_context):
            qml_action_step(gui_context, 'RefreshItemView', serialized_step)
        else:
            model = gui_context.get_item_model()
            if model is not None:
                model.refresh()
