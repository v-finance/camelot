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

from ...core.qt import QtCore, QtGui, py_to_variant, variant_to_py
from .action_widget import AbstractActionWidget
from .editors import DateEditor

class FilterWidget(QtGui.QGroupBox, AbstractActionWidget):
    """A box containing a filter that can be applied on a table view, this filter is
    based on the distinct values in a certain column"""

    def __init__(self, action, gui_context, parent):
        QtGui.QGroupBox.__init__(self, parent)
        layout = QtGui.QHBoxLayout()
        layout.setSpacing( 2 )
        layout.setContentsMargins( 2, 2, 2, 2 )
        self.setLayout( layout )
        self.setFlat(True)
        self.modes = None
        group = QtGui.QButtonGroup(self)
        # connect to the signal of the group instead of the individual buttons,
        # otherwise 2 signals will be received for a single switch of buttons
        group.buttonClicked[int].connect(self.group_button_clicked)
        AbstractActionWidget.__init__(self, action, gui_context)

    def current_row_changed(self, _current_row):
        pass
        
    def data_changed(self, _index1, _index2):
        pass

    def set_menu(self, _state):
        pass

    @QtCore.qt_slot(int)
    def group_button_clicked(self, index):
        mode = self.modes[index]
        self.run_action(mode=mode)

    def set_state(self, state):
        AbstractActionWidget.set_state(self, state)
        self.setTitle(six.text_type(state.verbose_name))
        group = self.findChild(QtGui.QButtonGroup)
        layout = self.layout()
        button_layout = QtGui.QVBoxLayout()
        self.modes = state.modes

        for i, mode in enumerate(state.modes):
            button = QtGui.QRadioButton(six.text_type(mode.verbose_name), self)
            button_layout.addWidget(button)
            group.addButton(button, i)
            if mode.name == state.default_mode.name:
                button.setChecked(True)

        layout.addLayout(button_layout)
        self.setLayout(layout)


class DateFilterWidget(QtGui.QGroupBox, AbstractActionWidget):
    """Filter widget based on a DateEditor"""

    def __init__(self, action, gui_context, parent):
        QtGui.QGroupBox.__init__(self, parent)
        AbstractActionWidget.__init__(self, action, gui_context)
        layout = QtGui.QVBoxLayout()
        layout.setSpacing( 2 )
        self.setFlat(True)
        self.date_editor = DateEditor(parent=self, nullable=True)
        layout.addWidget( self.date_editor )
        self.setLayout( layout )
        self.date_editor.editingFinished.connect(self.editing_finished)

    def set_state(self, state):
        AbstractActionWidget.set_state(self, state)
        self.setTitle(six.text_type(state.verbose_name))
        if state.default_mode is None:
            self.date_editor.set_value(None)
        else:
            self.date_editor.set_value(state.default_mode.name)

    def current_row_changed(self, _current_row):
        pass
        
    def data_changed(self, _index1, _index2):
        pass

    def set_menu(self, _state):
        pass

    @QtCore.qt_slot()
    def editing_finished(self):
        self.run_action()
        
    def decorate_query(self, query):
        return self.query_decorator(query, self.date_editor.get_value())

class GroupBoxFilterWidget(QtGui.QGroupBox, AbstractActionWidget):
    """Flter widget based on a QGroupBox"""

    def __init__(self, action, gui_context, parent):
        QtGui.QGroupBox.__init__(self, parent)
        AbstractActionWidget.__init__(self, action, gui_context)
        layout = QtGui.QVBoxLayout()
        layout.setSpacing( 2 )
        layout.setContentsMargins( 2, 2, 2, 2 )
        self.setFlat(True)
        combobox = QtGui.QComboBox(self)
        layout.addWidget( combobox )
        self.setLayout(layout)
        combobox.currentIndexChanged.connect(self.group_button_clicked)

    def set_state(self, state):
        AbstractActionWidget.set_state(self, state)
        self.setTitle(six.text_type(state.verbose_name))
        combobox = self.findChild(QtGui.QComboBox)
        if combobox is not None:
            current_index = 0
            for i, mode in enumerate(state.modes):
                if mode.name == state.default_mode.name:
                    current_index = i
                combobox.insertItem(i,
                                    six.text_type(mode.verbose_name),
                                    py_to_variant(mode))
            combobox.setCurrentIndex(current_index)

    def current_row_changed(self, _current_row):
        pass
        
    def data_changed(self, _index1, _index2):
        pass

    def set_menu(self, _state):
        pass

    @QtCore.qt_slot(int)
    def group_button_clicked(self, index):
        combobox = self.findChild(QtGui.QComboBox)
        if combobox is not None:
            item_data = variant_to_py(combobox.itemData(index))
            self.run_action(mode=item_data)
        
    def decorate_query(self, query):
        if self.current_index>=0:
            return self.filter_data.options[self.current_index].decorator( query )
        return query

class OperatorWidget(QtGui.QGroupBox, AbstractActionWidget):
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
    :param parent: the parent :obj:`QtGui.QWidget`
    """

    def __init__(self, action, gui_context, default_value_1, default_value_2, parent):
        QtGui.QGroupBox.__init__(self, parent)
        self.setFlat(True)
        self.default_value_1 = default_value_1
        self.default_value_2 = default_value_2
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins( 2, 2, 2, 2 )
        layout.setSpacing( 2 )
        self.setLayout(layout)
        AbstractActionWidget.__init__(self, action, gui_context)

    def set_state(self, state):
        layout = self.layout()
        self.setTitle(six.text_type(state.verbose_name))

        combobox = QtGui.QComboBox(self)
        layout.addWidget(combobox)
        default_index = 0
        for i, mode in enumerate(state.modes):
            combobox.insertItem(i,
                                six.text_type(mode.verbose_name),
                                py_to_variant(mode))
            if mode.name == state.default_mode.name:
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
        editing_finished_slot = self.editor_editing_finished
        self._editor.editingFinished.connect( editing_finished_slot )
        self._editor2.editingFinished.connect( editing_finished_slot )
        layout.addWidget(self._editor)
        layout.addWidget(self._editor2)
        layout.addStretch()
        self._editor.setEnabled(False)
        self._editor2.setEnabled(False)
        self._editor.hide()
        self._editor2.hide()
        self._index = default_index
        self._value = self.default_value_1
        self._value2 = self.default_value_2
        self.update_editors()

    def update_editors(self):
        """Show or hide the editors according to the operator
        arity"""
        if self._index >= 2:
            _, arity = self.get_operator_and_arity()
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
        self.filter_changed_signal.emit()
        
    def editor_editing_finished(self):
        """Whenever one of the editors their value changes, emit
        the filters changed signal"""
        self._value = self._editor.get_value()
        self._value2 = self._editor2.get_value()
        self.filter_changed_signal.emit()

    def get_operator_and_arity(self):
        """:return: the current operator and its arity"""
        combobox = self.findChild(QtGui.QComboBox)
        mode = variant_to_py(combobox.itemData(self._index))
        operator = mode.name
        try:
            func_code = six.get_function_code(operator)
        except AttributeError:
            arity = 1 # probably a builtin function, assume arity == 1
        else:
            arity = func_code.co_argcount - 1
        return operator, arity

    def current_row_changed(self, _current_row):
        pass
        
    def data_changed(self, _index1, _index2):
        pass

    def set_menu(self, _state):
        pass