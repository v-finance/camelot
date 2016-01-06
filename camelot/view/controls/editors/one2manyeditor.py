#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

import logging

from camelot.admin.action.list_action import ListActionGuiContext
from camelot.view.model_thread import object_thread, post
from camelot.view import register
from ....core.qt import Qt, QtCore, QtWidgets, QtGui, variant_to_py
from .wideeditor import WideEditor
from .customeditor import CustomEditor

LOGGER = logging.getLogger('camelot.view.controls.editors.onetomanyeditor')


class One2ManyEditor(CustomEditor, WideEditor):
    """
    :param admin: the Admin interface for the objects on the one side of the
    relation

    :param create_inline: if False, then a new entity will be created within a
    new window, if True, it will be created inline

    :param proxy: the proxy class to use to present the data in the list or
        the query to the table view

    :param column_width: the width of the editor in number of characters

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
                 proxy=None,
                 **kw):
        CustomEditor.__init__(self, parent, column_width=column_width)
        self.setObjectName(field_name)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        #
        # Setup table
        #
        from camelot.view.controls.tableview import AdminTableWidget
        from camelot.view.proxy.collection_proxy import CollectionProxy
        # parent set by layout manager
        table = AdminTableWidget(admin, self)
        table.setObjectName('table')
        layout.setSizeConstraint(QtGui.QLayout.SetNoConstraint)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Expanding)
        self.setMinimumHeight((self._font_height + 5) * 5)
        table.verticalHeader().sectionClicked.connect(
            self.trigger_list_action
        )
        model = (proxy or CollectionProxy)(admin)
        table.setModel(model)
        register.register(model, table)
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
        post(self.admin.get_related_toolbar_actions,
             self.set_right_toolbar_actions,
             args=(Qt.RightToolBarArea, self.direction))
        post(self.get_columns, self.set_columns)

    @QtCore.qt_slot(object)
    def set_right_toolbar_actions(self, toolbar_actions):
        if toolbar_actions is not None:
            toolbar = QtWidgets.QToolBar(self)
            toolbar.setOrientation(Qt.Vertical)
            for action in toolbar_actions:
                qaction = action.render(self.gui_context, toolbar)
                if isinstance(qaction, QtWidgets.QWidget):
                    toolbar.addWidget(qaction)
                else:
                    qaction.triggered.connect(self.action_triggered)
                    toolbar.addAction(qaction)
            self.layout().addWidget(toolbar)
            # set field attributes might have been called before the
            # toolbar was created
            self.update_action_status()

    @QtCore.qt_slot(bool)
    def action_triggered(self, _checked=False):
        action_action = self.sender()
        action_action.action.gui_run(self.gui_context)

    def set_field_attributes(self, **kwargs):
        super(One2ManyEditor, self).set_field_attributes(**kwargs)
        self.gui_context.field_attributes = kwargs
        self.update_action_status()

    def get_columns(self):
        return self.admin.get_columns()

    def update_action_status(self):
        toolbar = self.findChild(QtWidgets.QToolBar)
        if toolbar:
            model_context = self.gui_context.create_model_context()
            for qaction in toolbar.actions():
                post(qaction.action.get_state,
                     qaction.set_state,
                     args=(model_context, ))

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
                model.set_columns(columns)
                for i in range(model.columnCount()):
                    txtwidth = variant_to_py(
                        model.headerData(i, Qt.Horizontal, Qt.SizeHintRole)
                    ).width()
                    table.setColumnWidth(i, txtwidth)

    def set_value(self, collection):
        collection = CustomEditor.set_value(self, collection)
        model = self.get_model()
        if model is not None:
            # even if the collection 'is' the same object as the current
            # one, still need to set it, since the content of the collection
            # might have changed.
            model.set_value(collection)
            model_context = self.gui_context.create_model_context()
            for toolbar in self.findChildren(QtWidgets.QToolBar):
                for qaction in toolbar.actions():
                    post(qaction.action.get_state,
                         qaction.set_state,
                         args=(model_context, ))

    def activate_editor(self, number_of_rows):
        assert object_thread(self)
#        return
# Activating this code can cause segfaults
# see ticket 765 in web issues
#
# The segfault seems no longer there after disabling the
# editor before setting a new model, but the code below
# seems to have no effect.
        table = self.findChild(QtWidgets.QWidget, 'table')
        if table is not None:
            index = table.model().index(max(0, number_of_rows - 1), 0)
            table.scrollToBottom()
            table.setCurrentIndex(index)
            table.edit(index)

    @QtCore.qt_slot(int)
    def trigger_list_action(self, index):
        table = self.findChild(QtWidgets.QWidget, 'table')
        # close the editor to prevent certain Qt crashes
        table.close_editor()
        if self.admin.list_action:
            self.admin.list_action.gui_run(self.gui_context)
