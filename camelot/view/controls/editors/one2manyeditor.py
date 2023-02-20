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

import json
import logging

from ....admin.action.base import GuiContext
from ....admin.admin_route import RouteWithRenderHint
from ....core.qt import Qt, QtCore, QtWidgets, is_deleted
from ....core.item_model import ActionModeRole
from ... import gui_naming_context
from ..view import ViewWithActionsMixin
from camelot.view.qml_view import get_qml_root_backend
from camelot.view.utils import get_settings_group
from ..tableview import TableWidget
from .wideeditor import WideEditor
from .customeditor import CustomEditor

LOGGER = logging.getLogger('camelot.view.controls.editors.onetomanyeditor')


class One2ManyEditor(CustomEditor, WideEditor, ViewWithActionsMixin, GuiContext):
    """
    :param admin: the Admin interface for the objects on the one side of the
    relation

    :param column_width: the width of the editor in number of characters

    :param rows: minimum number of rows visible

    after creating the editor, set_value needs to be called to set the
    actual data to the editor
    """

    def __init__(self,
                 parent=None,
                 admin_route=None,
                 column_width=None,
                 columns=[],
                 rows=5,
                 action_routes=[],
                 list_actions=[],
                 list_action=None,
                 field_name='onetomany'):
        CustomEditor.__init__(self, parent, column_width=column_width)
        self.setObjectName(field_name)
        self.setProperty('action_route', list_action)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        #
        # Setup table
        #
        # parent set by layout manager
        table = TableWidget(parent=self)
        table.setObjectName('table')
        layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetNoConstraint)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)
        self.setMinimumHeight((self._font_height + 5) * rows)
        table.verticalHeader().sectionClicked.connect(
            self.trigger_list_action
        )
        self.action_routes = dict()
        model = get_qml_root_backend().createModel(get_settings_group(admin_route), table)
        model.actionStateChanged.connect(self.action_state_changed)
        table.setModel(model)
        self.admin_route = admin_route
        layout.addWidget(table)
        toolbar = QtWidgets.QToolBar(self)
        toolbar.setIconSize(QtCore.QSize(16, 16))
        toolbar.setOrientation(Qt.Orientation.Vertical)
        layout.addWidget(toolbar)
        self.setLayout(layout)
        self._new_message = None
        self.list_gui_context_name = gui_naming_context.bind(
            ('transient', str(id(self))), self
        )
        self.add_actions(action_routes, toolbar)
        self.set_right_toolbar_actions(list_actions, toolbar)
        self.set_columns(columns)

        selection_model = table.selectionModel()
        if selection_model is not None:
            # a queued connection, since the selection of the selection model
            # might not be up to date at the time the currentRowChanged
            # signal is emitted
            selection_model.currentRowChanged.connect(
                self.current_row_changed, type=Qt.ConnectionType.QueuedConnection
            )

    @property
    def item_view(self):
        return self.findChild(QtWidgets.QWidget, 'table')

    @property
    def view(self):
        return self

    def get_window(self):
        return self.window()

    def _run_list_context_action(self, action_widget, mode):
        table = self.findChild(QtWidgets.QWidget, 'table')
        model = table.model()
        self.run_action(
            action_widget, self.list_gui_context_name, model.value(), mode
        )

    @QtCore.qt_slot(int)
    def combobox_activated(self, index):
        combobox = self.sender()
        mode = [combobox.itemData(index)]
        self._run_list_context_action(combobox, mode)

    @QtCore.qt_slot(bool)
    def button_clicked(self, checked):
        table = self.findChild(QtWidgets.QWidget, 'table')
        # close the editor to prevent certain Qt crashes
        table.close_editor()
        self._run_list_context_action(self.sender(), None)

    @QtCore.qt_slot(object)
    def set_right_toolbar_actions(self, action_routes, toolbar):
        if action_routes is not None:
            for route_with_render_hint in action_routes:
                if not isinstance(route_with_render_hint, RouteWithRenderHint):
                    route_with_render_hint = RouteWithRenderHint.from_dict(route_with_render_hint)
                action_route = route_with_render_hint.route
                self.item_view.model().add_action_route(action_route)
                qaction = self.render_action(
                    route_with_render_hint.render_hint, action_route,
                    self, toolbar
                )
                qaction.action_route = action_route
                if isinstance(qaction, QtWidgets.QWidget):
                    toolbar.addWidget(qaction)
                else:
                    toolbar.addAction(qaction)
            # set field attributes might have been called before the
            # toolbar was created
            self.update_list_action_states()

    def update_list_action_states(self):
        table = self.item_view
        selection_model = table.selectionModel()
        current_index = table.currentIndex()
        table.model().change_selection(selection_model, current_index)

    def current_row_changed(self, current=None, previous=None):
        self.update_list_action_states()

    @QtCore.qt_slot('QStringList', QtCore.QByteArray)
    def action_state_changed(self, action_route, serialized_state):
        action_state = json.loads(serialized_state.data())
        self.set_action_state(self, tuple(action_route), action_state)

    def get_model(self):
        """
        :return: a :class:`QtGui.QAbstractItemModel` or `None`
        """
        table = self.findChild(QtWidgets.QWidget, 'table')
        if table is not None:
            return table.model()

    @QtCore.qt_slot(list, object)
    def editorActionTriggered(self, route, mode):
        table = self.findChild(QtWidgets.QWidget, 'table')
        if table is not None:
            model = table.model()
            if model is None:
                return
            if is_deleted(model):
                return
            index = table.currentIndex()
            model.setData(index, json.dumps([route, mode]), ActionModeRole)

    @QtCore.qt_slot(object)
    def set_columns(self, columns):
        from ..delegates.delegatemanager import DelegateManager
        table = self.findChild(QtWidgets.QWidget, 'table')
        if table is not None:
            delegate = DelegateManager(parent=self)
            delegate.actionTriggered.connect(self.editorActionTriggered)
            table.setItemDelegate(delegate)
            model = table.model()
            if model is not None:
                model.setColumns(columns)
                # this code should be useless, since at this point, the
                # column count is still 0 ??
                for i in range(model.columnCount()):
                    txtwidth = model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.SizeHintRole).width()
                    table.setColumnWidth(i, txtwidth)

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        #if collection is None:
            #collection = ListModelProxy([])
        model = self.get_model()
        if model is not None:
            # even if the collection 'is' the same object as the current
            # one, still need to set it, since the content of the collection
            # might have changed.
            if value is not None:
                model.setValue(tuple(value))
            self.update_list_action_states()

    def get_value(self):
        model = self.get_model()
        if model is not None:
            return model.value()

    @QtCore.qt_slot(int)
    def trigger_list_action(self, index):
        table = self.findChild(QtWidgets.QWidget, 'table')
        # close the editor to prevent certain Qt crashes
        table.close_editor()
        # make sure ChangeSelection action is executed before list action
        table.model().onTimeout()
        self._run_list_context_action(self, None)

    @QtCore.qt_slot()
    def menu_triggered(self):
        qaction = self.sender()
        self._run_list_context_action(qaction, qaction.data())
