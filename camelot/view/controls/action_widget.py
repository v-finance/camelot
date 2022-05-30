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

from ...core.qt import QtGui, QtWidgets

from ...admin.icon import Icon
from ...admin.action import Mode, State
from camelot.view.art import from_admin_icon

class AbstractActionWidget( object ):

    def init(self, action_name, gui_context):
        """Helper class to construct widget that when triggered run an action.
        This class exists as a base class for custom ActionButton
        implementations.
        
        The model is assumed to update its vertical header every time the object
        in a row changes.  So listening to the vertical header changes should
        be enough to update the state of the action.
        """
        assert isinstance(action_name, (tuple, list))
        self.action_name = action_name
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

    @classmethod
    def set_label_state(cls, label, state):
        cls.set_widget_state(label, state)
        label.setText(state.get('verbose_name') or '')

    @classmethod
    def set_toolbutton_state(cls, toolbutton, state, slot):
        # warning, this method does not set the menu, so does not work for
        # modes.
        cls.set_widget_state(toolbutton, state)
        cls._set_menu(toolbutton, state, toolbutton, slot)
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

    @classmethod
    def set_pushbutton_state(cls, push_button, state, parent, slot):
        cls.set_widget_state(push_button, state)
        if state['verbose_name'] != None:
            push_button.setText( str( state['verbose_name'] ) )
        if state['icon'] != None:
            icon = Icon(state['icon']['name'], state['icon']['pixmap_size'], state['icon']['color'])
            push_button.setIcon( from_admin_icon(icon).getQIcon() )
        else:
            push_button.setIcon( QtGui.QIcon() )
        if state['tooltip'] != None:
            push_button.setToolTip( str( state['tooltip'] ) )
        else:
            push_button.setToolTip( '' )
        cls._set_menu(push_button, state, parent, slot)

    @classmethod
    def set_combobox_state(cls, combobox, state):
        cls.set_widget_state(combobox, state)
        combobox.clear()
        current_index = 0
        for i, mode in enumerate(state['modes']):
            if mode['checked'] == True:
                current_index = i
            combobox.insertItem(
                i, mode['verbose_name'], mode['value']
            )
        # setting the current index will trigger the run of the action to
        # apply the initial filter
        combobox.setCurrentIndex(current_index)

    @classmethod
    def _set_menu(cls, widget, state, parent, slot):
        """
        slot can be None for use in unittests where the action wont be
        triggered
        """
        if state['modes']:
            # widget is not always a QWidget, so QMenu is created without
            # parent
            menu = widget.menu()
            if menu is None:
                menu = QtWidgets.QMenu(parent=parent)
                # setMenu does not transfer ownership
                widget.setMenu(menu)
            menu.clear()
            for mode_data in state['modes']:
                icon = Icon(mode_data['icon']['name'], mode_data['icon']['pixmap_size'], mode_data['icon']['color']) if mode_data['icon'] is not None else None
                if mode_data['modes']:
                    submodes = []
                    for submode_data in mode_data['modes']:
                        submode_icon = Icon(submode_data['icon']['name'], submode_data['icon']['pixmap_size'], submode_data['icon']['color']) if submode_data['icon'] is not None else None
                        submodes.append(Mode(submode_data['value'], submode_data['verbose_name'], submode_icon))
                    mode = Mode(mode_data['value'], mode_data['verbose_name'], submode_icon, submodes)
                    mode_menu = mode.render(menu)
                    for submode in mode.modes:
                        submode_action = submode.render(mode_menu)
                        if slot is not None:
                            submode_action.triggered.connect(slot)
                        submode_action.setProperty('action_route', widget.property('action_route'))
                        mode_menu.addAction(submode_action)
                else:
                    mode = Mode(mode_data['value'], mode_data['verbose_name'], icon)
                    mode_action = mode.render(menu)
                    if slot is not None:
                        mode_action.triggered.connect(slot)
                    mode_action.setProperty('action_route', widget.property('action_route'))
                    menu.addAction(mode_action)

