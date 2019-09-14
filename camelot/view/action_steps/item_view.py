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

from ...admin.action.base import ActionStep
from ...core.qt import Qt
from ..workspace import show_top_level


class Sort( ActionStep ):
    
    def __init__( self, column, order = Qt.AscendingOrder ):
        """Sort the items in the item view ( list, table or tree )
        
        :param column: the index of the column on which to sort
        :param order: a :class:`Qt.SortOrder`
        """
        self.column = column
        self.order = order
        
    def gui_run( self, gui_context ):
        if gui_context.item_view != None:
            model = gui_context.item_view.model()
            model.sort( self.column, self.order )

class SetFilter( ActionStep ):

    def __init__( self, list_filter, value ):
        """Filter the items in the item view
        
        :param list_filter: the `AbstractModelFilter` to apply
        :param value: the value on which to filter
        """
        self.list_filter = list_filter
        self.value = value

    def gui_run( self, gui_context ):
        if gui_context.item_view is not None:
            model = gui_context.item_view.model()
            model.set_filter(self.list_filter, self.value)

class SwitchExpandedSearch( ActionStep ):

    def __init__( self, filters):
        self.filters = filters

    def gui_run( self, gui_context ):
        if gui_context.item_view is not None:
            gui_context.item_view.switch_expanded_search(self.filters)


class UpdateTableView( ActionStep ):
    """Change the admin and or value of an existing table view
    
    :param admin: an `camelot.admin.object_admin.ObjectAdmin` instance
    :param value: a list of objects or a query
    
    """

    def __init__( self, admin, value ):
        self.admin = admin
        self.value = value
        self.search_text = None
        self.title = admin.get_verbose_name_plural()
        self.filters = admin.get_filters()
        self.list_actions = admin.get_list_actions()
        self.columns = self.admin.get_columns()
        self.left_toolbar_actions = admin.get_list_toolbar_actions(Qt.LeftToolBarArea)
        self.right_toolbar_actions = admin.get_list_toolbar_actions(Qt.RightToolBarArea)
        self.top_toolbar_actions = admin.get_list_toolbar_actions(Qt.TopToolBarArea)
        self.bottom_toolbar_actions = admin.get_list_toolbar_actions(Qt.BottomToolBarArea)
    
    def update_table_view(self, table_view):
        from camelot.view.controls.search import SimpleSearchControl
        table_view.set_admin(self.admin)
        model = table_view.get_model()
        list(model.add_columns((fn for fn, _fa in self.columns)))
        table_view.set_columns(self.columns)
        # filters can have default values, so they need to be set before
        # the value is set
        table_view.set_filters(self.filters)
        table_view.set_value(self.admin.get_proxy(self.value))
        table_view.set_list_actions(self.list_actions)
        table_view.set_toolbar_actions(
            Qt.LeftToolBarArea, self.left_toolbar_actions
        )
        table_view.set_toolbar_actions(
            Qt.RightToolBarArea, self.right_toolbar_actions
        )
        table_view.set_toolbar_actions(
            Qt.TopToolBarArea, self.top_toolbar_actions
        )
        table_view.set_toolbar_actions(
            Qt.BottomToolBarArea, self.bottom_toolbar_actions
        )
        if self.search_text is not None:
            search_control = table_view.findChild(SimpleSearchControl)
            search_control.setText(self.search_text)
            search_control.start_search()

    def gui_run(self, gui_context):
        self.update_table_view(gui_context.view)
        gui_context.view.change_title(self.title)

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
    
    def __init__( self, admin, value ):
        super(OpenTableView, self).__init__(admin, value)
        self.subclasses = admin.get_subclass_tree()
        self.new_tab = False

    def render(self, gui_context):
        from camelot.view.controls.tableview import TableView
        table_view = TableView(gui_context, self.admin)
        table_view.set_subclass_tree(self.subclasses)
        self.update_table_view(table_view)
        return table_view
        
    def gui_run( self, gui_context ):
        table_view = self.render(gui_context)
        if gui_context.workspace is not None:
            if self.new_tab == True:
                gui_context.workspace.add_view(table_view)
            else:
                gui_context.workspace.set_view(table_view)
        else:
            show_top_level(table_view, None)
        table_view.change_title(self.title)
        table_view.setFocus(Qt.PopupFocusReason)


class ClearSelection(ActionStep):
    """Deselect all selected items."""

    def gui_run(self, gui_context):
        if gui_context.item_view is not None:
            gui_context.item_view.clearSelection()

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