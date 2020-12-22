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

from camelot.admin.action.list_action import ListActionGuiContext
from camelot.view.model_thread import post
from camelot.view.proxy.collection_proxy import CollectionProxy
from ....admin.action.base import RenderHint
from ....core.qt import Qt, QtCore, QtWidgets, variant_to_py
from ....core.item_model import ListModelProxy
from ..action_widget import ActionAction, ActionToolbutton, ActionPushButton
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

    def __init__(self,
                 admin=None,
                 parent=None,
                 create_inline=False,
                 direction='onetomany',
                 field_name='onetomany',
                 column_width=None,
                 columns=[],
                 toolbar_actions=[],
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
        table = AdminTableWidget(admin, self)
        table.setObjectName('table')
        layout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        self.setMinimumHeight((self._font_height + 5) * rows)
        table.verticalHeader().sectionClicked.connect(
            self.trigger_list_action
        )
        model = CollectionProxy(admin)
        model.setParent(self)
        table.setModel(model)
        self.admin = admin
        self.direction = direction
        self.create_inline = create_inline
        layout.addWidget(table)
        self.setLayout(layout)
        self._new_message = None
        self.gui_context = ListActionGuiContext()
        self.gui_context.view = self
        self.gui_context.admin = self.admin
        self.gui_context.item_view = table
        self.set_right_toolbar_actions(toolbar_actions)
        self.set_columns(columns)

    def render_action(self, action, parent):
        if action.render_hint == RenderHint.TOOL_BUTTON:
            return ActionAction(action, self.gui_context, parent)
        elif action.render_hint == RenderHint.PUSH_BUTTON:
            return ActionPushButton(action, self.gui_context, parent)
        elif action.render_hint == RenderHint.COMBO_BOX:
            return ComboBoxFilterWidget(action, self.gui_context, parent)
        raise Exception('Unhandled render hint {} for {}'.format(action.render_hint, type(action)))

    @QtCore.qt_slot(object)
    def set_right_toolbar_actions(self, toolbar_actions):
        if toolbar_actions is not None:
            toolbar = QtWidgets.QToolBar(self)
            toolbar.setIconSize(QtCore.QSize(16, 16))
            toolbar.setOrientation(Qt.Vertical)
            for action in toolbar_actions:
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
        toolbar = self.findChild(QtWidgets.QToolBar)
        if toolbar:
            model_context = self.gui_context.create_model_context()
            for qaction in toolbar.actions() + toolbar.findChildren(ActionToolbutton):
                if isinstance(qaction, (ActionAction, ActionToolbutton)):
                    post(qaction.action.get_state,
                         qaction.set_state,
                         args=(model_context,))

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
            delegate = DelegateManager(columns, parent=self)
            table.setItemDelegate(delegate)
            model = table.model()
            if model is not None:
                list(model.add_columns((fn for fn, _fa in columns)))
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
            model.set_value(collection)
            self.update_action_status()

    @QtCore.qt_slot(int)
    def trigger_list_action(self, index):
        table = self.findChild(QtWidgets.QWidget, 'table')
        # close the editor to prevent certain Qt crashes
        table.close_editor()
        if self.admin.list_action:
            self.admin.list_action.gui_run(self.gui_context)

