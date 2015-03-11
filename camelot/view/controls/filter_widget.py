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

"""
Widgets that represent Filter Actions
"""

import six

from ...admin.action.list_filter import All
from ...core.qt import QtCore, QtGui, QtWidgets, py_to_variant, variant_to_py
from .action_widget import AbstractActionWidget

class AbstractFilterWidget(AbstractActionWidget):
    """Overwrite some methods to avoid to many state updates"""

    def current_row_changed(self, _current_row):
        pass
        
    def data_changed(self, _index1, _index2):
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


class GroupBoxFilterWidget(QtGui.QGroupBox, AbstractFilterWidget):
    """A box containing a filter that can be applied on a table view, this filter is
    based on the distinct values in a certain column"""

    def __init__(self, action, gui_context, parent):
        QtGui.QGroupBox.__init__(self, parent)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing( 2 )
        layout.setContentsMargins( 2, 2, 2, 2 )
        self.setLayout( layout )
        self.setFlat(True)
        self.modes = None
        group = QtGui.QButtonGroup(self)
        group.setExclusive(action.exclusive)
        # connect to the signal of the group instead of the individual buttons,
        # otherwise 2 signals will be received for a single switch of buttons
        group.buttonClicked[int].connect(self.group_button_clicked)
        if action.exclusive:
            self.button_type = QtGui.QRadioButton
        else:
            self.button_type = QtWidgets.QCheckBox
        AbstractFilterWidget.init(self, action, gui_context)

    @QtCore.qt_slot(int)
    def group_button_clicked(self, index):
        self.run_action()

    def get_value(self):
        values = []
        group = self.findChild(QtGui.QButtonGroup)
        all_checked = True
        for button in self.findChildren(self.button_type):
            if button.isChecked():
                button_id = group.id(button)
                values.append(self.modes[button_id].name)
            else:
                all_checked = False
        # shortcut, to make sure no actual filtering is done when
        # all options are checked
        if all_checked:
            return [All]
        return values

    def set_state(self, state):
        AbstractFilterWidget.set_state(self, state)
        self.setTitle(six.text_type(state.verbose_name))
        group = self.findChild(QtGui.QButtonGroup)
        layout = self.layout()
        button_layout = QtWidgets.QVBoxLayout()
        self.modes = state.modes

        for i, mode in enumerate(state.modes):
            button = self.button_type(six.text_type(mode.verbose_name), self)
            button_layout.addWidget(button)
            group.addButton(button, i)
            if mode.checked:
                button.setChecked(True)

        layout.addLayout(button_layout)
        self.setLayout(layout)

class ComboBoxFilterWidget(QtGui.QGroupBox, AbstractFilterWidget):
    """Flter widget based on a QGroupBox"""

    def __init__(self, action, gui_context, parent):
        QtGui.QGroupBox.__init__(self, parent)
        AbstractFilterWidget.init(self, action, gui_context)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing( 2 )
        layout.setContentsMargins( 2, 2, 2, 2 )
        self.setFlat(True)
        combobox = QtWidgets.QComboBox(self)
        layout.addWidget( combobox )
        self.setLayout(layout)
        combobox.currentIndexChanged.connect(self.group_button_clicked)

    def set_state(self, state):
        AbstractFilterWidget.set_state(self, state)
        self.setTitle(six.text_type(state.verbose_name))
        combobox = self.findChild(QtWidgets.QComboBox)
        if combobox is not None:
            current_index = 0
            for i, mode in enumerate(state.modes):
                if mode.checked == True:
                    current_index = i
                combobox.insertItem(i,
                                    six.text_type(mode.verbose_name),
                                    py_to_variant(mode))
            combobox.setCurrentIndex(current_index)

    def get_value(self):
        combobox = self.findChild(QtWidgets.QComboBox)
        if combobox is not None:
            index = combobox.currentIndex()
            mode = variant_to_py(combobox.itemData(index))
            return [mode.name]

    @QtCore.qt_slot(int)
    def group_button_clicked(self, index):
        self.run_action()

class OperatorFilterWidget(QtGui.QGroupBox, AbstractFilterWidget):
    """Widget that allows applying various filter operators on a field

    :param cls: the class on which the filter will be applied
    :param field_name: the name fo the field on the class on which to filter
    :param field_attributes: a dictionary of field attributes for this filter
    :param default_operator: a default operator to be used, on of the attributes
        of the python module :mod:`operator`, such as `operator.eq`
    :param default_value_1: a default value for the first editor (in case the
        default operator in unary or binary
    :param default_value_2: a default value for the second editor (in case the
        default operator is binary)
    :param parent: the parent :obj:`QtWidgets.QWidget`
    """

    def __init__(self, action, gui_context, default_value_1, default_value_2, parent):
        QtGui.QGroupBox.__init__(self, parent)
        self.setFlat(True)
        self.default_value_1 = default_value_1
        self.default_value_2 = default_value_2
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins( 2, 2, 2, 2 )
        layout.setSpacing( 2 )
        self.setLayout(layout)
        AbstractFilterWidget.init(self, action, gui_context)

    def set_state(self, state):
        layout = self.layout()
        self.setTitle(six.text_type(state.verbose_name))

        combobox = QtWidgets.QComboBox(self)
        layout.addWidget(combobox)
        default_index = 0
        for i, mode in enumerate(state.modes):
            combobox.insertItem(i,
                                six.text_type(mode.verbose_name),
                                py_to_variant(mode))
            if mode.checked == True:
                default_index = i
        combobox.setCurrentIndex( default_index )
        combobox.currentIndexChanged.connect( self.combobox_changed )
        delegate = state.field_attributes['delegate'](** state.field_attributes)
        option = QtGui.QStyleOptionViewItem()
        option.version = 5
        self._editor = delegate.createEditor( self, option, None )
        self._editor2 = delegate.createEditor( self, option, None )
        # explicitely set a value, otherways the current value remains 
        # ValueLoading
        self._editor.set_value(self.default_value_1)
        self._editor2.set_value(self.default_value_2)
        self._editor.editingFinished.connect(self.run_action)
        self._editor2.editingFinished.connect(self.run_action)
        layout.addWidget(self._editor)
        layout.addWidget(self._editor2)
        layout.addStretch()
        self._editor.setEnabled(False)
        self._editor2.setEnabled(False)
        self._editor.hide()
        self._editor2.hide()
        self._index = default_index
        self.update_editors()

    def update_editors(self):
        """Show or hide the editors according to the operator
        arity"""
        if self._index >= 2:
            mode = self.get_mode()
            arity = self.action.get_arity(mode.name)
            self._editor.setEnabled(True)
            if arity > 0:
                self._editor.setEnabled(True)
                self._editor.show()
            else:
                self._editor.setEnabled(False)
                self._editor.hide()
            if arity > 1:
                self._editor2.setEnabled(True)
                self._editor2.show()
            else:
                self._editor2.setEnabled(False)
                self._editor2.hide()
        else:
            self._editor.setEnabled(False)
            self._editor.hide()
            self._editor2.setEnabled(False)
            self._editor2.hide()
        
    @QtCore.qt_slot(int)
    def combobox_changed(self, index):
        """Whenever the combobox changes, show or hide the
        appropriate editors and emit the filter_changed signal """
        self._index = index
        self.update_editors()
        self.run_action()

    def get_mode(self):
        combobox = self.findChild(QtWidgets.QComboBox)
        index = combobox.currentIndex()
        mode = variant_to_py(combobox.itemData(index))
        return mode

    def get_value(self):
        mode = self.get_mode()
        return (mode.name, self._editor.get_value(), self._editor2.get_value())

