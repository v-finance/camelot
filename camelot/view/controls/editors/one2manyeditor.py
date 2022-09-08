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

from camelot.admin.action.list_action import ListActionGuiContext
from camelot.view.proxy.collection_proxy import CollectionProxy
from ....core.qt import Qt, QtCore, QtWidgets, variant_to_py
from ..view import ViewWithActionsMixin
from ..tableview import TableWidget
from .wideeditor import WideEditor
from .customeditor import CustomEditor

LOGGER = logging.getLogger('camelot.view.controls.editors.onetomanyeditor')


class One2ManyEditor(CustomEditor, WideEditor, ViewWithActionsMixin):
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

    def __init__(self,
                 admin_route=None,
                 parent=None,
                 create_inline=False,
                 direction='onetomany',
                 field_name='onetomany',
                 column_width=None,
                 columns=[],
                 rows=5,
                 action_routes=[],
                 list_actions=[],
                 list_action=None,
                 **kw):
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
        model = CollectionProxy(admin_route)
        model.action_state_changed_cpp_signal.connect(self.action_state_changed)
        model.setParent(self)
        table.setModel(model)
        self.admin_route = admin_route
        self.direction = direction
        self.create_inline = create_inline
        layout.addWidget(table)
        toolbar = QtWidgets.QToolBar(self)
        toolbar.setIconSize(QtCore.QSize(16, 16))
        toolbar.setOrientation(Qt.Orientation.Vertical)
        layout.addWidget(toolbar)
        self.setLayout(layout)
        self._new_message = None
        self.list_gui_context = ListActionGuiContext()
        self.list_gui_context.view = self
        self.list_gui_context.admin_route = self.admin_route
        self.list_gui_context.item_view = table
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

    @QtCore.qt_slot(int)
    def combobox_activated(self, index):
        combobox = self.sender()
        mode = [combobox.itemData(index)]
        self.run_action(combobox, self.list_gui_context, mode)

    @QtCore.qt_slot(bool)
    def button_clicked(self, checked):
        table = self.findChild(QtWidgets.QWidget, 'table')
        # close the editor to prevent certain Qt crashes
        table.close_editor()
        self.run_action(self.sender(), self.list_gui_context, None)

    @QtCore.qt_slot(object)
    def set_right_toolbar_actions(self, action_routes, toolbar):
        if action_routes is not None:
            for route_with_render_hint in action_routes:
                action_route = route_with_render_hint.route
                self.list_gui_context.item_view.model().add_action_route(action_route)
                qaction = self.render_action(
                    route_with_render_hint.render_hint, action_route,
                    self.list_gui_context, toolbar
                )
                qaction.action_route = action_route
                if isinstance(qaction, QtWidgets.QWidget):
                    toolbar.addWidget(qaction)
                else:
                    toolbar.addAction(qaction)
            # set field attributes might have been called before the
            # toolbar was created
            self.update_list_action_states()

    def set_field_attributes(self, **kwargs):
        super(One2ManyEditor, self).set_field_attributes(**kwargs)
        self.list_gui_context.field_attributes = kwargs
        self.update_list_action_states()

    def update_list_action_states(self):
        table = self.list_gui_context.item_view
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
                        model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.SizeHintRole)
                    ).width()
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
            model.set_value(value)
            self.update_list_action_states()

    def get_value(self):
        model = self.get_model()
        if model is not None:
            return model.get_value()

    @QtCore.qt_slot(int)
    def trigger_list_action(self, index):
        table = self.findChild(QtWidgets.QWidget, 'table')
        # close the editor to prevent certain Qt crashes
        table.close_editor()
        self.run_action(self, self.list_gui_context, None)

    @QtCore.qt_slot()
    def menu_triggered(self):
        qaction = self.sender()
        self.run_action(qaction, self.list_gui_context, qaction.data())
