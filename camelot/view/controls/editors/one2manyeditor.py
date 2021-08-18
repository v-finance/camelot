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
import itertools

from camelot.admin.action.list_action import ListActionGuiContext
from camelot.view.model_thread import post
from camelot.view.proxy.collection_proxy import CollectionProxy
from ....admin.admin_route import AdminRoute
from ....admin.action.base import State, RenderHint
from ....core.qt import Qt, QtCore, QtWidgets, variant_to_py
from ....core.item_model import ListModelProxy, ProxyRegistry
from ..action_widget import AbstractActionWidget, ActionAction, ActionToolbutton, ActionPushButton
from ..filter_widget import ComboBoxFilterWidget
from .wideeditor import WideEditor
from .customeditor import CustomEditor

LOGGER = logging.getLogger('camelot.view.controls.editors.onetomanyeditor')


class One2ManyEditor(CustomEditor, WideEditor):
    """
    :param admin: the Admin interface for the objects on the one side of the
    relation

    :param create_inline: if False, then a new entity will be created within a
    new window, if True, it will be created inline

    :param column_width: the width of the editor in number of characters

    :param rows: minimum number of rows visible

    after creating the editor, set_value needs to be called to set the
    actual data to the editor
    """

    _rendered_action_counter = itertools.count()

    def __init__(self,
                 admin_route=None,
                 parent=None,
                 create_inline=False,
                 direction='onetomany',
                 field_name='onetomany',
                 column_width=None,
                 columns=[],
                 rows=5,
                 **kw):
        CustomEditor.__init__(self, parent, column_width=column_width)
        self.setObjectName(field_name)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        #
        # Setup table
        #
        from camelot.view.controls.tableview import AdminTableWidget
        # parent set by layout manager
        table = AdminTableWidget(self)
        table.setObjectName('table')
        layout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        self.setMinimumHeight((self._font_height + 5) * rows)
        table.verticalHeader().sectionClicked.connect(
            self.trigger_list_action
        )
        model = CollectionProxy(admin_route)
        model.action_state_changed_signal.connect(self.action_state_changed)
        model.setParent(self)
        table.setModel(model)
        self.admin_route = admin_route
        self.direction = direction
        self.create_inline = create_inline
        layout.addWidget(table)
        self.setLayout(layout)
        self._new_message = None
        self.gui_context = ListActionGuiContext()
        self.gui_context.view = self
        self.gui_context.admin_route = self.admin_route
        self.gui_context.item_view = table
        self.set_right_toolbar_actions(kw['action_routes'])
        self.set_columns(columns)

        selection_model = table.selectionModel()
        if selection_model is not None:
            # a queued connection, since the selection of the selection model
            # might not be up to date at the time the currentRowChanged
            # signal is emitted
            selection_model.currentRowChanged.connect(
                self.current_row_changed, type=Qt.QueuedConnection
            )

    @classmethod
    def _register_rendered_action(cls, qobject):
        next_rendered_action = cls._rendered_action_counter.__next__()
        rendered_action_name = 'rendered_action_{}'.format(next_rendered_action)
        qobject.setObjectName(rendered_action_name)
        return rendered_action_name

    def render_action(self, action, parent):
        if action.render_hint == RenderHint.TOOL_BUTTON:
            # Use tool button, because this one sets the popup mode
            # to instant if there are modes in the state
            qobject = ActionToolbutton(action, self.gui_context, parent)
        elif action.render_hint == RenderHint.PUSH_BUTTON:
            qobject = ActionPushButton(action, self.gui_context, parent)
        elif action.render_hint == RenderHint.COMBO_BOX:
            qobject = ComboBoxFilterWidget(action, self.gui_context, parent)
        else:
            raise Exception('Unhandled render hint {} for {}'.format(action.render_hint, type(action)))
        rendered_action_name = self._register_rendered_action(qobject)
        self.gui_context.action_routes[action] = rendered_action_name
        return qobject

    @QtCore.qt_slot(object)
    def set_right_toolbar_actions(self, action_routes):
        if action_routes is not None:
            self.gui_context.item_view.model().set_action_routes(action_routes)
            toolbar = QtWidgets.QToolBar(self)
            toolbar.setIconSize(QtCore.QSize(16, 16))
            toolbar.setOrientation(Qt.Vertical)
            for action_route in action_routes:
                action = AdminRoute.action_for(action_route)
                qaction = self.render_action(action, toolbar)
                if isinstance(qaction, QtWidgets.QWidget):
                    toolbar.addWidget(qaction)
                else:
                    toolbar.addAction(qaction)
            self.layout().addWidget(toolbar)
            # set field attributes might have been called before the
            # toolbar was created
            self.update_action_status()

    def set_field_attributes(self, **kwargs):
        super(One2ManyEditor, self).set_field_attributes(**kwargs)
        self.gui_context.field_attributes = kwargs
        self.update_action_status()

    def update_action_status(self):
        table = self.gui_context.item_view
        selection_model = table.selectionModel()
        current_index = table.currentIndex()
        table.model().change_selection(selection_model, current_index)

    def current_row_changed(self, current=None, previous=None):
        self.update_action_status()

    @QtCore.qt_slot(tuple, State)
    def action_state_changed(self, route, state):
        action = AdminRoute.action_for(route)
        action_name = self.gui_context.action_routes[action]
        action_widget = self.findChild(AbstractActionWidget, action_name)
        if isinstance(action_widget, (ActionAction, ActionToolbutton, ActionPushButton)):
            action_widget.set_state(state)

    def get_model(self):
        """
        :return: a :class:`QtGui.QAbstractItemModel` or `None`
        """
        table = self.findChild(QtWidgets.QWidget, 'table')
        if table is not None:
            return table.model()

    @QtCore.qt_slot(object)
    def set_columns(self, columns):
        from ..delegates.delegatemanager import DelegateManager
        table = self.findChild(QtWidgets.QWidget, 'table')
        if table is not None:
            delegate = DelegateManager(parent=self)
            table.setItemDelegate(delegate)
            model = table.model()
            if model is not None:
                list(model.add_columns(columns))
                # this code should be useless, since at this point, the
                # column count is still 0 ??
                for i in range(model.columnCount()):
                    txtwidth = variant_to_py(
                        model.headerData(i, Qt.Horizontal, Qt.SizeHintRole)
                    ).width()
                    table.setColumnWidth(i, txtwidth)

    def set_value(self, collection):
        collection = CustomEditor.set_value(self, collection)
        if collection is None:
            collection = ListModelProxy([])
        model = self.get_model()
        if model is not None:
            # even if the collection 'is' the same object as the current
            # one, still need to set it, since the content of the collection
            # might have changed.
            model.set_value(ProxyRegistry.register(collection))
            self.update_action_status()

    @QtCore.qt_slot(int)
    def trigger_list_action(self, index):
        table = self.findChild(QtWidgets.QWidget, 'table')
        # close the editor to prevent certain Qt crashes
        table.close_editor()
        admin = AdminRoute.admin_for(self.admin_route)
        if admin.list_action:
            admin.list_action.gui_run(self.gui_context)

