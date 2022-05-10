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

"""
Widgets that represent Filter Actions
"""



from ...admin.action.list_filter import All
from ...core.utils import ugettext
from ...core.qt import QtCore, QtWidgets, py_to_variant, variant_to_py
from .action_widget import AbstractActionWidget

class AbstractFilterWidget(AbstractActionWidget):
    """Overwrite some methods to avoid to many state updates"""

    def current_row_changed(self, _current_row):
        pass

    def header_data_changed(self, _orientation, _first, _last):
        pass

    def set_menu(self, _state):
        pass

    def get_value(self):
        """:return: a list of selected values"""
        raise NotImplementedError()

    def run_action(self):
        gui_context = self.gui_context.copy()
        value = self.get_value()
        self.action.gui_run(gui_context, value)


class GroupBoxFilterWidget(QtWidgets.QGroupBox, AbstractFilterWidget):
    """A box containing a filter that can be applied on a table view, this filter is
    based on the distinct values in a certain column"""

    def __init__(self, action, gui_context, parent):
        QtWidgets.QGroupBox.__init__(self, parent)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing( 2 )
        layout.setContentsMargins( 2, 2, 2, 2 )
        self.setLayout( layout )
        self.setFlat(True)
        self.values = None
        group = QtWidgets.QButtonGroup(self)
        group.setExclusive(action.exclusive)
        # connect to the signal of the group instead of the individual buttons,
        # otherwise 2 signals will be received for a single switch of buttons
        group.idClicked.connect(self.group_button_clicked)
        if action.exclusive == True:
            self.button_type = QtWidgets.QRadioButton
        else:
            self.button_type = QtWidgets.QCheckBox
            all_button = self.button_type(ugettext('All'), self)
            all_button.setObjectName('all_button')
            all_button.toggled.connect(self.all_button_toggled)
            layout.addWidget(all_button)
        AbstractFilterWidget.init(self, action, gui_context)

    @QtCore.qt_slot(bool)
    def all_button_toggled(self, checked):
        for button in self.findChildren(self.button_type):
            button.setChecked(checked)
        self.group_button_clicked(0)

    @QtCore.qt_slot(int)
    def group_button_clicked(self, index):
        value = self.get_value()
        all_button = self.findChild(QtWidgets.QAbstractButton, 'all_button')
        if all_button is not None:
            all_button.blockSignals(True)
            all_button.setChecked(All in value)
            all_button.blockSignals(False)
        self.run_action()

    def get_value(self):
        values = []
        group = self.findChild(QtWidgets.QButtonGroup)
        all_checked = True
        for button in self.findChildren(self.button_type):
            if button.objectName() != 'all_button':
                if button.isChecked():
                    button_id = group.id(button)
                    values.append(self.values[button_id])
                else:
                    all_checked = False
        # shortcut, to make sure no actual filtering is done when
        # all options are checked
        if all_checked:
            return [All]
        return values

    def set_state(self, state):
        AbstractFilterWidget.set_state(self, state)
        self.setTitle(str(state.verbose_name))
        group = self.findChild(QtWidgets.QButtonGroup)
        layout = self.layout()
        button_layout = QtWidgets.QVBoxLayout()
        self.values = [mode.value for mode in state.modes]

        for i, mode in enumerate(state.modes):
            button = self.button_type(str(mode.verbose_name), self)
            button_layout.addWidget(button)
            group.addButton(button, i)
            if mode.checked:
                button.setChecked(True)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def set_state_v2(self, state):
        AbstractFilterWidget.set_state_v2(self, state)
        self.setTitle(state['verbose_name'])
        group = self.findChild(QtWidgets.QButtonGroup)
        layout = self.layout()
        button_layout = QtWidgets.QVBoxLayout()
        self.values = [mode['value'] for mode in state['modes']]

        for i, mode in enumerate(state['modes']):
            button = self.button_type(str(mode['verbose_name']), self)
            button_layout.addWidget(button)
            group.addButton(button, i)
            if mode['checked']:
                button.setChecked(True)

        layout.addLayout(button_layout)
        self.setLayout(layout)
        # run the filter action to apply the initial filter on the list
        self.run_action()

class ComboBoxFilterWidget(QtWidgets.QGroupBox, AbstractFilterWidget):
    """Flter widget based on a QGroupBox"""

    def __init__(self, action, gui_context, parent):
        QtWidgets.QGroupBox.__init__(self, parent)
        AbstractFilterWidget.init(self, action, gui_context)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing( 2 )
        layout.setContentsMargins( 2, 2, 2, 2 )
        self.setFlat(True)
        combobox = QtWidgets.QComboBox(self)
        layout.addWidget( combobox )
        self.setLayout(layout)
        combobox.activated.connect(self.group_button_clicked)

    def set_state(self, state):
        AbstractFilterWidget.set_state(self, state)
        self.setTitle(str(state.verbose_name))
        combobox = self.findChild(QtWidgets.QComboBox)
        if combobox is not None:
            current_index = 0
            for i, mode in enumerate(state.modes):
                if mode.checked == True:
                    current_index = i
                combobox.insertItem(i,
                                    str(mode.verbose_name),
                                    py_to_variant(mode.value))
            # setting the current index will trigger the run of the action to
            # apply the initial filter
            combobox.setCurrentIndex(current_index)

    def set_state_v2(self, state):
        AbstractFilterWidget.set_state_v2(self, state)
        self.setTitle(state['verbose_name'])
        combobox = self.findChild(QtWidgets.QComboBox)
        if combobox is not None:
            self._set_state_v2(combobox)

    @classmethod
    def _set_state_v2(cls, widget, state):
        cls.set_widget_state(widget, state)
        widget.clear()
        current_index = 0
        for i, mode in enumerate(state['modes']):
            if mode['checked'] == True:
                current_index = i
            widget.insertItem(i,
                              mode['verbose_name'],
                              mode['value'])
        # setting the current index will trigger the run of the action to
        # apply the initial filter
        widget.setCurrentIndex(current_index)

    def get_value(self):
        combobox = self.findChild(QtWidgets.QComboBox)
        if combobox is not None:
            index = combobox.currentIndex()
            mode_name = variant_to_py(combobox.itemData(index))
            return [mode_name]

    @QtCore.qt_slot(int)
    def group_button_clicked(self, index):
        self.run_action()
