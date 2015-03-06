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

from ...core.qt import QtGui, QtCore, QtWidgets, variant_to_py, is_deleted

import six

from ...admin.action import State
from ...admin.action.form_action import FormActionGuiContext
from ...admin.action.list_action import ListActionGuiContext
from camelot.core.utils import ugettext
from camelot.view.model_thread import post

class AbstractActionWidget( object ):

    def __init__( self, action, gui_context ):
        """Helper class to construct widget that when triggered run an action.
        This class exists as a base class for custom ActionButton implementations.
        """
        self.action = action
        self.gui_context = gui_context
        self.state = State()
        if isinstance( gui_context, FormActionGuiContext ):
            gui_context.widget_mapper.model().dataChanged.connect( self.data_changed )
            gui_context.widget_mapper.currentIndexChanged.connect( self.current_row_changed )
        if isinstance( gui_context, ListActionGuiContext ):
            gui_context.item_view.model().dataChanged.connect(self.data_changed)
            selection_model = gui_context.item_view.selectionModel()
            if selection_model is not None:
                selection_model.currentRowChanged.connect(self.current_row_changed)
        post( action.get_state, self.set_state, args = (self.gui_context.create_model_context(),) )

    def set_state(self, state):
        self.state = state
        self.setEnabled(state.enabled)
        self.setVisible(state.visible)

    def current_row_changed( self, index1=None, index2=None ):
        post( self.action.get_state,
              self.set_state,
              args = (self.gui_context.create_model_context(),) )

    def data_changed(self, index1, index2):
        if isinstance(self.gui_context, FormActionGuiContext):
            # the model might emit a dataChanged signal, while the widget mapper
            # has been deleted
            if not is_deleted(self.gui_context.widget_mapper):
                self.current_row_changed( index1.row() )
        if isinstance(self.gui_context, ListActionGuiContext):
            if not is_deleted(self.gui_context.item_view):
                selection_model = self.gui_context.item_view.selectionModel()
                if (selection_model is not None) and selection_model.hasSelection():
                    parent = QtCore.QModelIndex()
                    for row in six.moves.range(index1.row(), index2.row()+1):
                        if selection_model.rowIntersectsSelection(row, parent):
                            self.current_row_changed(row)
                            return

    def run_action( self, mode=None ):
        gui_context = self.gui_context.copy()
        gui_context.mode_name = mode
        self.action.gui_run( gui_context )

    def set_menu( self, state ):
        """This method creates a menu for an object with as its menu items
        the different modes in which an action can be triggered.

        :param state: a `camelot.admin.action.State` object
        """
        if state.modes:
            menu = QtGui.QMenu()
            for mode in state.modes:
                mode_action = mode.render( menu )
                mode_action.triggered.connect( self.triggered )
                menu.addAction( mode_action )
            self.setMenu( menu )

HOVER_ANIMATION_DISTANCE = 20
NOTIFICATION_ANIMATION_DISTANCE = 8

class ActionLabel( QtWidgets.QLabel, AbstractActionWidget ):

    entered = QtCore.qt_signal()
    left = QtCore.qt_signal()

    """
    A custom interactive desktop button for the desktop. Each 'button' is
    actually an animated label.
    """
    def __init__( self, action, gui_context, parent ):
        QtWidgets.QLabel.__init__( self, parent )
        AbstractActionWidget.__init__( self, action, gui_context )

        self.setObjectName('ActionButton')
        self.setMouseTracking(True)

        # This property holds if this button reacts to mouse events.
        self.interactive = False

        # This property is used to store the original position of this label
        # so it can be visually reset when the user leaves before the ongoing
        # animation has finished.
        self.originalPosition = None
        self.setMaximumHeight(160)


    def set_state( self, state ):
        AbstractActionWidget.set_state( self, state )
        if state.icon:
            self.setPixmap( state.icon.getQPixmap() )
            self.resize( self.pixmap().width(), self.pixmap().height() )
        self.resetLayout()

    def resetLayout(self):
        if self.sender() and self.originalPosition:
            self.move(self.originalPosition)
        self.setScaledContents(False)
        if self.pixmap():
            self.resize(self.pixmap().width(), self.pixmap().height())

    def setInteractive(self, interactive):
        self.interactive = interactive
        self.originalPosition = self.mapToParent(QtCore.QPoint(0, 0))# + QtCore.QPoint(NOTIFICATION_ANIMATION_DISTANCE, HOVER_ANIMATION_DISTANCE)

    def enterEvent(self, event):
        if self.interactive:
            self.entered.emit()
        event.ignore()

    def leaveEvent(self, event):
        if self.interactive:
            self.left.emit()
        event.ignore()

    def onContainerMousePressEvent(self, event):
        self.run_action()
        event.ignore()

class ActionAction( QtWidgets.QAction, AbstractActionWidget ):

    def __init__( self, action, gui_context, parent ):
        QtWidgets.QAction.__init__( self, parent )
        AbstractActionWidget.__init__( self, action, gui_context )
        if action.shortcut != None:
            self.setShortcut( action.shortcut )

    @QtCore.qt_slot( object )
    def set_state( self, state ):
        if state.verbose_name != None:
            self.setText( six.text_type( state.verbose_name ) )
        else:
            self.setText( '' )
        if state.icon != None:
            self.setIcon( state.icon.getQIcon() )
        else:
            self.setIcon( QtGui.QIcon() )
        if state.tooltip != None:
            self.setToolTip( six.text_type( state.tooltip ) )
        else:
            self.setToolTip( '' )
        self.setEnabled( state.enabled )
        self.setVisible( state.visible )
        self.set_menu( state )

class ActionPushButton( QtWidgets.QPushButton, AbstractActionWidget ):

    def __init__( self, action, gui_context, parent ):
        """A :class:`QtWidgets.QPushButton` that when pressed, will run an
        action.

        .. image:: /_static/actionwidgets/action_push_botton_application_enabled.png

        """
        QtWidgets.QPushButton.__init__( self, parent )
        AbstractActionWidget.__init__( self, action, gui_context )
        self.clicked.connect( self.triggered )

    @QtCore.qt_slot()
    def triggered(self):
        sender = self.sender()
        mode = None
        if isinstance( sender, QtWidgets.QAction ):
            mode = six.text_type( variant_to_py(sender.data()) )
        self.run_action( mode )

    @QtCore.qt_slot( QtCore.QModelIndex, QtCore.QModelIndex )
    def data_changed( self, index1, index2 ):
        AbstractActionWidget.data_changed( self, index1, index2 )

    def set_state( self, state ):
        super( ActionPushButton, self ).set_state( state )
        if state.verbose_name != None:
            self.setText( six.text_type( state.verbose_name ) )
        if state.icon != None:
            self.setIcon( state.icon.getQIcon() )
        else:
            self.setIcon( QtGui.QIcon() )
        self.set_menu( state )

class ActionToolbutton(QtGui.QToolButton, AbstractActionWidget):

    def __init__( self, action, gui_context, parent ):
        """A :class:`QtGui.QToolButton` that when pressed, will run an
        action."""
        QtGui.QToolButton.__init__( self, parent )
        AbstractActionWidget.__init__( self, action, gui_context )
        self.clicked.connect(self.run_action)

    def set_state( self, state ):
        AbstractActionWidget.set_state(self, state)
        if state.verbose_name != None:
            self.setText( six.text_type( state.verbose_name ) )
        if state.icon != None:
            self.setIcon( state.icon.getQIcon() )
        else:
            self.setIcon( QtGui.QIcon() )
        if state.tooltip != None:
            self.setToolTip( six.text_type( state.tooltip ) )
        else:
            self.setToolTip( '' )
        self.set_menu( state )

class AuthenticationWidget(QtGui.QFrame, AbstractActionWidget):
    """Widget that displays information on the active user"""

    def __init__(self, action, gui_context, parent):
        from ..remote_signals import get_signal_handler
        QtGui.QFrame.__init__(self, parent)
        AbstractActionWidget.__init__(self, action, gui_context)
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        face = QtGui.QToolButton()
        face.setObjectName('face')
        face.setAutoRaise(True)
        face.clicked.connect(self.face_clicked)
        face.setToolTip(ugettext('Change avatar'))
        layout.addWidget(face)
        info_layout = QtGui.QVBoxLayout()
        user_name = QtWidgets.QLabel()
        font = user_name.font()
        font.setBold(True)
        font.setPointSize(10)
        user_name.setFont(font)
        user_name.setObjectName('user_name')
        info_layout.addWidget(user_name)
        groups = QtWidgets.QLabel()
        font = groups.font()
        font.setPointSize(8)
        groups.setFont(font)
        groups.setObjectName('groups')
        info_layout.addWidget(groups)
        info_layout.setSpacing(0)
        info_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(info_layout)
        self.setLayout(layout)
        signal_handler = get_signal_handler()
        signal_handler.entity_update_signal.connect(self.entity_update)

    @QtCore.qt_slot(object, object)
    def entity_update(self, sender, entity):
        from ...model.authentication import AuthenticationMechanism
        if isinstance(entity, AuthenticationMechanism):
            self.current_row_changed(0)

    @QtCore.qt_slot(bool)
    def face_clicked(self, state):
        self.run_action()

    def set_state(self, state):
        user_name = self.findChild(QtWidgets.QLabel, 'user_name')
        user_name.setText(state.verbose_name)
        groups = self.findChild(QtWidgets.QLabel, 'groups')
        groups.setText(state.tooltip)
        face = self.findChild(QtGui.QToolButton, 'face')
        face.setIcon(state.icon.getQIcon())
