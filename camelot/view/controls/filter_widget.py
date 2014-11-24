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