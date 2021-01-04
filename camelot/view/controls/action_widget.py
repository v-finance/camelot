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

from ...core.qt import Qt, QtGui, QtCore, QtWidgets, QtQuick, variant_to_py, is_deleted

import six

from ...admin.action import State
from ...admin.action.form_action import FormActionGuiContext
from ...admin.action.list_action import ListActionGuiContext
from camelot.view.model_thread import post

class AbstractActionWidget( object ):

    def init( self, action, gui_context ):
        """Helper class to construct widget that when triggered run an action.
        This class exists as a base class for custom ActionButton
        implementations.
        
        The model is assumed to update its vertical header every time the object
        in a row changes.  So listening to the vertical header changes should
        be enough to update the state of the action.
        """
        self.action = action
        self.gui_context = gui_context
        self.state = State()
        if isinstance( gui_context, FormActionGuiContext ):
            gui_context.widget_mapper.model().headerDataChanged.connect(self.header_data_changed)
            gui_context.widget_mapper.currentIndexChanged.connect( self.current_row_changed )
        if isinstance( gui_context, ListActionGuiContext ):
            gui_context.item_view.model().headerDataChanged.connect(self.header_data_changed)
            #gui_context.item_view.model().modelReset.connect(self.model_reset)
            selection_model = gui_context.item_view.selectionModel()
            if selection_model is not None:
                # a queued connection, since the selection of the selection model
                # might not be up to date at the time the currentRowChanged
                # signal is emitted
                selection_model.currentRowChanged.connect(
                    self.current_row_changed, type=Qt.QueuedConnection
                )
        post( action.get_state, self.set_state, args = (self.gui_context.create_model_context(),) )

    def set_state(self, state):
        self.state = state
        self.setEnabled(state.enabled)
        self.setVisible(state.visible)

    def current_row_changed( self, index1=None, index2=None ):
        post( self.action.get_state,
              self.set_state,
              args = (self.gui_context.create_model_context(),) )

    def header_data_changed(self, orientation, first, last):
        if orientation==Qt.Horizontal:
            return
        if isinstance(self.gui_context, FormActionGuiContext):
            # the model might emit a dataChanged signal, while the widget mapper
            # has been deleted
            if not is_deleted(self.gui_context.widget_mapper):
                self.current_row_changed(first)
        if isinstance(self.gui_context, ListActionGuiContext):
            if not is_deleted(self.gui_context.item_view):
                selection_model = self.gui_context.item_view.selectionModel()
                if (selection_model is not None) and selection_model.hasSelection():
                    parent = QtCore.QModelIndex()
                    for row in six.moves.range(first, last+1):
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
        if isinstance(sender, (QtWidgets.QAction, QtQuick.QQuickItem)):
            mode = str(variant_to_py(sender.data()))
        self.run_action( mode )


class ActionAction( QtWidgets.QAction, AbstractActionWidget ):

    def __init__( self, action, gui_context, parent ):
        QtWidgets.QAction.__init__( self, parent )
        AbstractActionWidget.init( self, action, gui_context )
        if action.shortcut != None:
            self.setShortcut( action.shortcut )
        self.triggered.connect(self.action_triggered)

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

    @QtCore.qt_slot(Qt.Orientation, int, int)
    def header_data_changed(self, orientation, first, last):
        AbstractActionWidget.header_data_changed(self, orientation, first, last)

    def set_state( self, state ):
        super( ActionPushButton, self ).set_state( state )
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
        if state.modes:
            self.setPopupMode(QtWidgets.QToolButton.InstantPopup)

    @QtCore.qt_slot()
    def action_triggered(self):
        self.action_triggered_by(self.sender())

class ActionLabel(QtWidgets.QLabel, AbstractActionWidget):

    def __init__( self, action, gui_context, parent ):
        """A :class:`QtWidgets.QLabel` that only displays the state
        of an action and alows no user interaction"""
        QtWidgets.QLabel.__init__(self, parent)
        AbstractActionWidget.init(self, action, gui_context)
        font = self.font()
        font.setBold(True)
        self.setFont(font)

    def set_state(self, state):
        AbstractActionWidget.set_state(self, state)
        self.setText(state.verbose_name or '')
