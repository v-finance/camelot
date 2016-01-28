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

from ...core.qt import QtGui, QtCore, QtWidgets, variant_to_py, is_deleted

import six

from ...admin.action import State
from ...admin.action.form_action import FormActionGuiContext
from ...admin.action.list_action import ListActionGuiContext
from ..crud_signals import CrudSignalHandler
from camelot.core.utils import ugettext
from camelot.view.model_thread import post

class AbstractActionWidget( object ):

    def init( self, action, gui_context ):
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
            #gui_context.item_view.model().modelReset.connect(self.model_reset)
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
            # self is not always a QWidget, so QMenu is created without
            # parent
            menu = QtWidgets.QMenu()
            for mode in state.modes:
                mode_action = mode.render(menu)
                mode_action.triggered.connect(self.action_triggered)
                menu.addAction(mode_action)
            self.setMenu( menu )

    # not named triggered to avoid confusion with standard Qt slot
    def action_triggered_by(self, sender):
        """
        action_triggered should be a slot, so it cannot be defined in the
        abstract widget, the slot should get the sender and call
        action_triggered_by
        """
        mode = None
        if isinstance( sender, QtWidgets.QAction ):
            mode = six.text_type( variant_to_py(sender.data()) )
        self.run_action( mode )

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
        AbstractActionWidget.init( self, action, gui_context )

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
        AbstractActionWidget.init( self, action, gui_context )
        if action.shortcut != None:
            self.setShortcut( action.shortcut )

    @QtCore.qt_slot()
    def action_triggered(self):
        self.action_triggered_by(self.sender())

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
        AbstractActionWidget.init( self, action, gui_context )
        self.clicked.connect(self.action_triggered)

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

    @QtCore.qt_slot()
    def action_triggered(self):
        self.action_triggered_by(self.sender())

class ActionToolbutton(QtWidgets.QToolButton, AbstractActionWidget):

    def __init__( self, action, gui_context, parent ):
        """A :class:`QtWidgets.QToolButton` that when pressed, will run an
        action."""
        QtWidgets.QToolButton.__init__( self, parent )
        AbstractActionWidget.init( self, action, gui_context )
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

    @QtCore.qt_slot()
    def action_triggered(self):
        self.action_triggered_by(self.sender())

class AuthenticationWidget(QtWidgets.QFrame, AbstractActionWidget):
    """Widget that displays information on the active user"""

    def __init__(self, action, gui_context, parent):
        QtWidgets.QFrame.__init__(self, parent)
        AbstractActionWidget.init(self, action, gui_context)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        face = QtWidgets.QToolButton()
        face.setObjectName('face')
        face.setAutoRaise(True)
        face.clicked.connect(self.face_clicked)
        face.setToolTip(ugettext('Change avatar'))
        layout.addWidget(face)
        info_layout = QtWidgets.QVBoxLayout()
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
        signal_handler = CrudSignalHandler()
        signal_handler.objects_updated.connect(self.objects_updated)

    @QtCore.qt_slot(object, tuple)
    def objects_updated(self, sender, objects):
        from ...model.authentication import AuthenticationMechanism
        for obj in objects:
            if isinstance(obj, AuthenticationMechanism):
                self.current_row_changed(0)

    @QtCore.qt_slot(bool)
    def face_clicked(self, state):
        self.run_action()

    def set_state(self, state):
        user_name = self.findChild(QtWidgets.QLabel, 'user_name')
        user_name.setText(state.verbose_name)
        groups = self.findChild(QtWidgets.QLabel, 'groups')
        groups.setText(state.tooltip)
        face = self.findChild(QtWidgets.QToolButton, 'face')
        face.setIcon(state.icon.getQIcon())

