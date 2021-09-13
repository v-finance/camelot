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
from typing import Any, Union, List, Tuple
import json

from ...admin.admin_route import Route, AdminRoute
from ...admin.action.application_action import UpdateActions
from ...admin.action.base import ActionStep, RenderHint, State
from ...admin.action.list_action import ListActionModelContext, ListActionGuiContext, ApplicationActionGuiContext
from ...admin.action.list_filter import Filter, All
from ...core.qt import Qt, QtCore
from ...core.utils import ugettext_lazy
from ...core.item_model import ProxyRegistry, AbstractModelFilter
from ...core.serializable import DataclassSerializable
from ..controls.action_widget import ActionAction
from ..item_view import ItemViewProxy
from ..workspace import show_top_level
from ..proxy.collection_proxy import (
    CollectionProxy, RowCount, RowData, SetColumns
)

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
        if gui_context.item_view != None:
            model = gui_context.item_view.model()
            model.sort( step["column"], step["order"] )

@dataclass
class SetFilter( ActionStep ):
    """Filter the items in the item view

            :param list_filter: the `AbstractModelFilter` to apply
            :param value: the value on which to filter
    """
    list_filter: AbstractModelFilter
    value: Any

    blocking = False
    cancelable = False

    def gui_run( self, gui_context ):
        if gui_context.item_view is not None:
            model = gui_context.item_view.model()
            model.set_filter(self.list_filter, self.value)

row_count_instance = RowCount()
set_columns_instance = SetColumns()
row_data_instance = RowData()

@dataclass
class CrudActions(DataclassSerializable):
    """
    A data class which contains the routes to crud actions available
    to the gui to invoke.
    """

    admin: InitVar
    row_count: Route = field(init=False)
    set_columns: Route = field(init=False)
    row_data: Route = field(init=False)

    def __post_init__(self, admin):
        self.row_count = admin._register_action_route(
            admin.get_admin_route(), row_count_instance
        )
        self.row_data = admin._register_action_route(
            admin.get_admin_route(), row_data_instance
        )
        self.set_columns = admin._register_action_route(
            admin.get_admin_route(), set_columns_instance
        )

@dataclass
class UpdateTableView( ActionStep, DataclassSerializable ):
    """Change the admin and or value of an existing table view
    
    :param admin: an `camelot.admin.object_admin.ObjectAdmin` instance
    :param value: a list of objects or a query
    
    """

    admin: InitVar
    value: InitVar
    search_text: Union[str, None] = field(init=False)
    title: Union[str, ugettext_lazy] = field(init=False)
    columns: List[str] = field(init=False)
    list_action: Route = field(init=False)
    proxy_route: Route = field(init=False)
    actions: List[Tuple[Route, RenderHint]] = field(init=False)
    action_states: List[Tuple[Route, State]] = field(default_factory=list)
    crud_actions: CrudActions = field(init=False)

    def __post_init__( self, admin, value ):
        self.value = value
        self.search_text = None
        self.title = admin.get_verbose_name_plural()
        self.actions = admin.get_list_actions().copy()
        self.actions.extend(admin.get_filters())
        self.actions.extend(admin.get_list_toolbar_actions())
        self.columns = admin.get_columns()
        self.list_action = admin.get_list_action()
        proxy = admin.get_proxy(value)
        self.proxy_route = ProxyRegistry.register(proxy)
        self._add_action_states(admin, proxy, self.actions, self.action_states)
        self.crud_actions = CrudActions(admin)

    @staticmethod
    def _add_action_states(admin, proxy, actions, action_states):
        model_context = ListActionModelContext()
        model_context.admin = admin
        model_context.proxy = proxy
        for action_route in actions:
            action = AdminRoute.action_for(action_route.route)
            state = action.get_state(model_context)
            action_states.append((action_route.route, state))

    @staticmethod
    def set_filters(action_states, model):
        for action_state in action_states:
            route = tuple(action_state[0])
            action = AdminRoute.action_for(route)
            if not isinstance(action, Filter):
                continue
            state = action_state[1]
            values = [mode['name'] for mode in state['modes'] if mode['checked']]
            # if all modes are checked, replace with [All]
            if len(values) == len(state['modes']):
                values = [All]
            model.set_filter(action, values)

    @classmethod
    def update_table_view(cls, table_view, step):
        from camelot.view.controls.search import SimpleSearchControl
        table_view.set_admin()
        model = table_view.get_model()
        list(model.add_columns(step['columns']))
        # filters can have default values, so they need to be set before
        # the value is set
        cls.set_filters(step['action_states'], model)

        table_view.set_value(step['proxy_route'])
        table_view.list_action = AdminRoute.action_for(tuple(step['list_action']))
        table_view.set_actions(step['actions'], step['action_states'])
        if step['search_text'] is not None:
            search_control = table_view.findChild(SimpleSearchControl)
            search_control.setText(step['search_text'])
            search_control.start_search()

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

    def __post_init__( self, admin, value ):
        super(OpenTableView, self).__post_init__(admin, value)
        self.admin_route = admin.get_admin_route()

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
        table_view.setFocus(Qt.PopupFocusReason)


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

    def __init__(self, admin, value):
        super().__init__(admin, value)
        self.list_action = admin.get_list_action()

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        step = json.loads(serialized_step)
        quick_view = gui_context.workspace.quick_view
        tab_view = quick_view.findChild(QtCore.QObject, "qml_tab_view")
        assert tab_view

        header_model = QtCore.QStringListModel(parent=quick_view)
        header_model.setStringList(step['columns'])
        header_model.setParent(quick_view)
        new_model = CollectionProxy(tuple(step['admin_route']))

        # filters can have default values, so they need to be set before
        # the value is set
        cls.set_filters(step['action_states'], new_model)

        new_model.setParent(quick_view)
        list(new_model.add_columns(step['columns']))
        new_model.set_value(step['proxy_route'])
        view = tab_view.addTabFromUrl(
            step['title'],
            QtCore.QUrl("qrc:/qml/common/TablePage.qml"),
            { 'model': new_model, 'headerModel': header_model }
        )
        table = view.findChild(QtCore.QObject, "qml_table")
        item_view = ItemViewProxy(table)

        class QmlListActionGuiContext(ListActionGuiContext):

            def get_progress_dialog(self):
                return ApplicationActionGuiContext.get_progress_dialog(self)

        list_gui_context = gui_context.copy(QmlListActionGuiContext)
        list_gui_context.item_view = item_view
        list_gui_context.admin_route = tuple(step['admin_route'])
        list_gui_context.view = view

        list_action = AdminRoute.action_for(tuple(step['list_action']))
        qt_action = ActionAction(list_action, list_gui_context, quick_view)
        table.activated.connect(qt_action.action_triggered, type=Qt.QueuedConnection)
        for i, action_route in enumerate(step['actions']):
            action = AdminRoute.action_for(tuple(action_route['route']))
            qt_action = ActionAction(action, list_gui_context, table)
            state = None
            for action_state in step['action_states']:
                if action_state[0] == action_route['route']:
                    state = action_state[1]
                    break
            assert state is not None

            rendered_action = item_view._qml_item.addAction(
                action.render_hint.value, state, qt_action
            )
            rendered_action.triggered.connect(qt_action.action_triggered, type=Qt.QueuedConnection)
            rendered_action.setObjectName('action_{}'.format(i))
            list_gui_context.action_routes[action] = rendered_action.objectName()
        UpdateActions().gui_run(list_gui_context)

@dataclass
class ClearSelection(ActionStep, DataclassSerializable):
    """Deselect all selected items."""

    def gui_run(self, gui_context):
        if gui_context.item_view is not None:
            gui_context.item_view.clearSelection()

@dataclass
class RefreshItemView(ActionStep, DataclassSerializable):
    """
    Refresh only the current item view
    """

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        if gui_context.item_view is not None:
            model = gui_context.item_view.model()
            if model is not None:
                model.refresh()
                # this should reset the sort, since a refresh might cause
                # new row to appear, and so the proxy needs to be reindexed
                # this sorting of reset is not implemented, therefor, we simply
                # sort on the first column to force reindexing
                model.sort(0, Qt.AscendingOrder)
