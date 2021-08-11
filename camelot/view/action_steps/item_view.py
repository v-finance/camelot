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
from ...admin.action.base import ActionStep, RenderHint
from ...admin.action.list_action import ListActionGuiContext, ApplicationActionGuiContext
from ...core.qt import Qt, QtCore
from ...core.utils import ugettext_lazy
from ...core.item_model import ProxyRegistry, AbstractModelFilter
from ...core.serializable import DataclassSerializable
from ..controls.action_widget import ActionAction
from ..item_view import ItemViewProxy
from ..workspace import show_top_level
from ..proxy.collection_proxy import CollectionProxy

@dataclass
class Sort( ActionStep ):
    """Sort the items in the item view ( list, table or tree )

            :param column: the index of the column on which to sort
            :param order: a :class:`Qt.SortOrder`
    """
    column: int
    order: Qt = Qt.SortOrder

    def gui_run( self, gui_context ):
        if gui_context.item_view != None:
            model = gui_context.item_view.model()
            model.sort( self.column, self.order )

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

    def __post_init__( self, admin, value ):
        self.admin_route = admin.get_admin_route()
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

    @staticmethod
    def update_table_view(table_view, step):
        from camelot.view.controls.search import SimpleSearchControl
        table_view.set_admin()
        model = table_view.get_model()
        list(model.add_columns(step['columns']))
        # filters can have default values, so they need to be set before
        # the value is set
        table_view.set_filters([AdminRoute.action_for(tuple(action['route'])) for action in step['actions'] if action['render_hint'] in [RenderHint.COMBO_BOX.value, RenderHint.GROUP_BOX.value]])
        table_view.set_value(step['proxy_route'])
        table_view.set_list_actions([AdminRoute.action_for(tuple(action['route'])) for action in step['actions'] if action['render_hint'] == RenderHint.PUSH_BUTTON.value])
        table_view.list_action = AdminRoute.action_for(tuple(step['list_action']))
        table_view.set_toolbar_actions(
            Qt.TopToolBarArea,
            [AdminRoute.action_for(tuple(action['route'])) for action in step['actions'] if action['render_hint'] in [RenderHint.TOOL_BUTTON.value, RenderHint.SEARCH_BUTTON.value, RenderHint.LABEL.value]]
        )
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
    admin: InitVar
    value: InitVar
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
        view = gui_context.workspace.active_view()
        quick_view = view.quick_view
        views = quick_view.findChild(QtCore.QObject, "qml_views")
        header_model = QtCore.QStringListModel(parent=quick_view)
        header_model.setStringList(step['columns'])
        header_model.setParent(quick_view)
        new_model = CollectionProxy(tuple(step['admin_route']))
        new_model.setParent(quick_view)
        list(new_model.add_columns(step['columns']))
        new_model.set_value(step['proxy_route'])
        view = views.addView(new_model, header_model)
        table = view.findChild(QtCore.QObject, "qml_table")
        item_view = ItemViewProxy(table)

        class QmlListActionGuiContext(ListActionGuiContext):

            def get_progress_dialog(self):
                return ApplicationActionGuiContext.get_progress_dialog(self)

        list_gui_context = gui_context.copy(QmlListActionGuiContext)
        list_gui_context.item_view = item_view
        list_gui_context.admin_route = tuple(step['admin_route'])
        list_gui_context.view = table

        list_action = AdminRoute.action_for(tuple(step['list_action']))
        qt_action = ActionAction(list_action, list_gui_context, quick_view)
        table.activated.connect(qt_action.action_triggered, type=Qt.QueuedConnection)
        for i, action_route in enumerate(step['actions']):
            action = AdminRoute.action_for(tuple(action_route['route']))
            icon_name = None
            if action.icon is not None:
                icon_name = action.icon.name
            qt_action = ActionAction(action, list_gui_context, table)
            rendered_action = item_view._qml_item.addAction(
                action.render_hint.value, str(action.verbose_name or 'Unknown'), icon_name,
                qt_action,
            )
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
class RefreshItemView(ActionStep):
    """
    Refresh only the current item view
    """

    def gui_run(self, gui_context):
        if gui_context.item_view is not None:
            model = gui_context.item_view.model()
            if model is not None:
                model.refresh()
                # this should reset the sort, since a refresh might cause
                # new row to appear, and so the proxy needs to be reindexed
                # this sorting of reset is not implemented, therefor, we simply
                # sort on the first column to force reindexing
                model.sort(0, Qt.AscendingOrder)
