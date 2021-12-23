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

#from ...core.qt import Qt, QtGui, QtCore, QtWidgets, QtQuick, variant_to_py, is_deleted
from ...core.qt import QtGui, QtCore, QtWidgets, QtQuick, QtQml, variant_to_py

from ...admin.icon import Icon
from ...admin.action import Mode, State
#from ...admin.action.form_action import FormActionGuiContext
#from ...admin.action.list_action import ListActionGuiContext
#from camelot.view.model_thread import post
from camelot.view.art import from_admin_icon

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
        # REMOVE THIS...
        """
        if isinstance( gui_context, FormActionGuiContext ):
            gui_context.widget_mapper.model().headerDataChanged.connect(self.header_data_changed)
            gui_context.widget_mapper.currentIndexChanged.connect( self.current_row_changed )
        """

    def set_state(self, state):
        self.state = state
        self.setEnabled(state.enabled)
        self.setVisible(state.visible)

    def set_state_v2(self, state):
        self.set_widget_state(self, state)

    @classmethod
    def set_widget_state(cls, widget, state):
        widget.setEnabled(state['enabled'])
        widget.setVisible(state['visible'])

    # REMOVE THIS...
    """
    def current_row_changed( self, current=None, previous=None ):
        #if not isinstance( self.gui_context, ListActionGuiContext ):
        if not isinstance( self.gui_context, (ListActionGuiContext, FormActionGuiContext) ):
            print('Update state:', self.action, ',', self.gui_context)
            post( self.action.get_state,
                  self.set_state,
                  args = (self.gui_context.create_model_context(),) )

    def header_data_changed(self, orientation, first, last):
        if orientation==Qt.Orientation.Horizontal:
            return
        if isinstance(self.gui_context, FormActionGuiContext):
            # the model might emit a dataChanged signal, while the widget mapper
            # has been deleted
            if not is_deleted(self.gui_context.widget_mapper):
                self.current_row_changed(first)
    """

    def run_action( self, mode=None ):
        gui_context = self.gui_context.copy()
        if isinstance(mode, list):
            self.action.gui_run( gui_context, mode )
        else:
            gui_context.mode_name = mode
            self.action.gui_run( gui_context )


    def set_menu(self, state, parent):
        """This method creates a menu for an object with as its menu items
        the different modes in which an action can be triggered.

        :param state: a `camelot.admin.action.State` object
        :param parent: a parent for the menu
        """
        if state.modes:
            # self is not always a QWidget, so QMenu is created without
            # parent
            menu = self.menu()
            if menu is None:
                menu = QtWidgets.QMenu(parent=parent)
                # setMenu does not transfer ownership
                self.setMenu(menu)
            menu.clear()
            for mode in state.modes:
                if mode.modes:
                    mode_menu = mode.render(menu)
                    for submode in mode.modes:
                        submode_action = submode.render(mode_menu)
                        submode_action.triggered.connect(self.action_triggered)
                        mode_menu.addAction(submode_action)
                else:
                    mode_action = mode.render(menu)
                    mode_action.triggered.connect(self.action_triggered)
                    menu.addAction(mode_action)

    def set_menu_v2(self, state, parent):
        """This method creates a menu for an object with as its menu items
        the different modes in which an action can be triggered.

        :param state: a `camelot.admin.action.State` object
        :param parent: a parent for the menu
        """
        if state['modes']:
            # self is not always a QWidget, so QMenu is created without
            # parent
            menu = self.menu()
            if menu is None:
                menu = QtWidgets.QMenu(parent=parent)
                # setMenu does not transfer ownership
                self.setMenu(menu)
            menu.clear()
            for mode_data in state['modes']:
                icon = Icon(mode_data['icon']['name'], mode_data['icon']['pixmap_size'], mode_data['icon']['color']) if mode_data['icon'] is not None else None
                if mode_data['modes']:
                    submodes = []
                    for submode_data in mode_data['modes']:
                        submode_icon = Icon(submode_data['icon']['name'], submode_data['icon']['pixmap_size'], submode_data['icon']['color']) if submode_data['icon'] is not None else None
                        submodes.append(Mode(submode_data['name'], submode_data['verbose_name'], submode_icon))
                    mode = Mode(mode_data['name'], mode_data['verbose_name'], submode_icon, submodes)
                    mode_menu = mode.render(menu)
                    for submode in mode.modes:
                        submode_action = submode.render(mode_menu)
                        submode_action.triggered.connect(self.action_triggered)
                        mode_menu.addAction(submode_action)
                else:
                    mode = Mode(mode_data['name'], mode_data['verbose_name'], icon)
                    mode_action = mode.render(menu)
                    mode_action.triggered.connect(self.action_triggered)
                    menu.addAction(mode_action)

    # not named triggered to avoid confusion with standard Qt slot
    def action_triggered_by(self, sender):
        """
        action_triggered should be a slot, so it cannot be defined in the
        abstract widget, the slot should get the sender and call
        action_triggered_by
        """
        mode = None
        if isinstance(sender, QtGui.QAction):
            mode = str(variant_to_py(sender.data()))
        elif isinstance(sender, QtQuick.QQuickItem):
            data = sender.mode()
            if isinstance(data, QtQml.QJSValue):
                data = data.toVariant()
            mode = variant_to_py(data)
        self.run_action( mode )


class ActionAction( QtGui.QAction, AbstractActionWidget ):

    def __init__( self, action, gui_context, parent ):
        QtGui.QAction.__init__( self, parent )
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
            self.setText( str( state.verbose_name ) )
        else:
            self.setText( '' )
        if state.icon != None:
            self.setIcon( from_admin_icon(state.icon).getQIcon() )
        else:
            self.setIcon( QtGui.QIcon() )
        if state.tooltip != None:
            self.setToolTip( str( state.tooltip ) )
        else:
            self.setToolTip( '' )
        self.setEnabled( state.enabled )
        self.setVisible( state.visible )
        # todo : determine the parent for the menu
        self.set_menu(state, None)

    @QtCore.qt_slot( object )
    def set_state_v2( self, state ):
        if state['verbose_name'] != None:
            self.setText( str( state['verbose_name'] ) )
        else:
            self.setText( '' )
        if state['icon'] != None:
            icon = Icon(state['icon']['name'], state['icon']['pixmap_size'], state['icon']['color'])
            self.setIcon( from_admin_icon(icon).getQIcon() )
        else:
            self.setIcon( QtGui.QIcon() )
        if state['tooltip'] != None:
            self.setToolTip( str( state['tooltip'] ) )
        else:
            self.setToolTip( '' )
        self.setEnabled( state['enabled'] )
        self.setVisible( state['visible'] )
        # todo : determine the parent for the menu
        self.set_menu_v2(state, None)

class ActionPushButton( QtWidgets.QPushButton, AbstractActionWidget ):

    def __init__( self, action, gui_context, parent ):
        """A :class:`QtWidgets.QPushButton` that when pressed, will run an
        action.

        .. image:: /_static/actionwidgets/action_push_botton_application_enabled.png

        """
        QtWidgets.QPushButton.__init__( self, parent )
        AbstractActionWidget.init( self, action, gui_context )
        self.clicked.connect(self.action_triggered)

    # REMOVE THIS...
    """
    @QtCore.qt_slot(Qt.Orientation, int, int)
    def header_data_changed(self, orientation, first, last):
        AbstractActionWidget.header_data_changed(self, orientation, first, last)
    """

    def set_state( self, state ):
        super( ActionPushButton, self ).set_state( state )
        if state.verbose_name != None:
            self.setText( str( state.verbose_name ) )
        if state.icon != None:
            self.setIcon( from_admin_icon(state.icon).getQIcon() )
        else:
            self.setIcon( QtGui.QIcon() )
        if state.tooltip != None:
            self.setToolTip( str( state.tooltip ) )
        else:
            self.setToolTip( '' )            
        self.set_menu(state, self)

    def set_state_v2( self, state ):
        super( ActionPushButton, self ).set_state_v2( state )
        if state['verbose_name'] != None:
            self.setText( str( state['verbose_name'] ) )
        if state['icon'] != None:
            icon = Icon(state['icon']['name'], state['icon']['pixmap_size'], state['icon']['color'])
            self.setIcon( from_admin_icon(icon).getQIcon() )
        else:
            self.setIcon( QtGui.QIcon() )
        if state['tooltip'] != None:
            self.setToolTip( str( state['tooltip'] ) )
        else:
            self.setToolTip( '' )
        self.set_menu_v2(state, self)

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
            self.setText( str( state.verbose_name ) )
        if state.icon != None:
            self.setIcon( from_admin_icon(state.icon).getQIcon() )
        else:
            self.setIcon( QtGui.QIcon() )
        if state.tooltip != None:
            self.setToolTip( str( state.tooltip ) )
        else:
            self.setToolTip( '' )
        self.set_menu(state, self)
        if state.modes:
            self.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

    def set_state_v2( self, state ):
        self.set_menu_v2(state, self)
        self.set_toolbutton_state(self, state)

    @classmethod
    def set_toolbutton_state(cls, toolbutton, state):
        # warning, this method does not set the menu, so does not work for
        # modes.
        cls.set_widget_state(toolbutton, state)
        if state['verbose_name'] != None:
            toolbutton.setText( str( state['verbose_name'] ) )
        if state['icon'] != None:
            icon = Icon(state['icon']['name'], state['icon']['pixmap_size'], state['icon']['color'])
            toolbutton.setIcon( from_admin_icon(icon).getQIcon() )
        else:
            toolbutton.setIcon( QtGui.QIcon() )
        if state['tooltip'] != None:
            toolbutton.setToolTip( str( state['tooltip'] ) )
        else:
            toolbutton.setToolTip( '' )
        if state['modes']:
            toolbutton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)


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

    def set_state_v2(self, state):
        AbstractActionWidget.set_state_v2(self, state)
        self.setText(state.get('verbose_name') or '')
