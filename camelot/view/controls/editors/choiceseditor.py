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

import logging

from ....core.naming import initial_naming_context
from ....core.qt import (
    QtGui, QtCore, QtWidgets, Qt, is_deleted
)
from ....admin.icon import CompletionValue
from ...art import ColorScheme, FontIcon
from .customeditor import CustomEditor

LOGGER = logging.getLogger('camelot.view.controls.editors.ChoicesEditor')

# since this is gui code, we assume all names are lists,
# as the original tuple has been serialized/deserialized

none_name = list(initial_naming_context._bind_object(None))
none_item = CompletionValue(none_name, verbose_name=' ')._to_dict()

class ChoicesEditor(CustomEditor):
    """A ComboBox aka Drop Down box that can be assigned a list of
    keys and values"""

    def __init__( self,
                  parent = None,
                  action_routes = [],
                  field_name = 'choices' ):
        super(ChoicesEditor, self).__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        combobox = QtWidgets.QComboBox()
        combobox.setObjectName('combobox')
        combobox.activated.connect(self._activated)
        layout.addWidget(combobox)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setObjectName( field_name )
        # make sure None is in the list of choices
        self.set_choices([none_item])
        self.setLayout(layout)
        self.add_actions(action_routes, layout)

    @QtCore.qt_slot(int)
    def _activated(self, _index):
        self.setProperty( 'value', self.get_value() )
        self.valueChanged.emit()
        self.editingFinished.emit()

    @staticmethod
    def append_item(model, data):
        """Append an item in a combobox model

        :param data: a `CompletionValue` dict
        """
        item = QtGui.QStandardItem()
        for role, value in data.items():
            if value is not None:
                if role == 'verbose_name':
                    item.setText(str(value))
                elif role == 'value':
                    item.setData(value, Qt.ItemDataRole.UserRole)
                elif role == 'tooltip':
                    item.setToolTip(str(value))
                elif role == 'foreground':
                    item.setForeground(QtGui.QBrush(QtGui.QColor(value)))
                elif role == 'icon':
                    item.setIcon(FontIcon(**value).getQIcon())
                elif role == 'virtual':
                    item.setData(value, Qt.ItemDataRole.UserRole+1)
                elif role == 'background':
                    item.setBackground(QtGui.QBrush(QtGui.QColor(value)))
                else:
                    LOGGER.error('Unhandled role in item : {}'.format(role))
        model.appendRow(item)

    @classmethod
    def append_choices(cls, model, choices):
        """
        append all choices to a combobox model
        """
        none_available = False
        for choice in choices:
            cls.append_item(model, choice)
            if choice['value'] == none_name:
                none_available = True
        if not none_available:
            cls.append_item(model, none_item)
        
    @classmethod
    def value_at_row(cls, model, row):
        if row >= 0:
            return model.data(model.index(row, 0), Qt.ItemDataRole.UserRole)
        else:
            return None

    @classmethod
    def row_with_value(cls, model, value, display_role):
        rows = model.rowCount()
        for i in range(rows):
            if value == model.data(model.index(i, 0), Qt.ItemDataRole.UserRole):
                return i
        else:
            # it might happen, that when we set the editor data, the set_choices
            # method has not happened yet or the choices don't contain the value
            # set
            if display_role is None:
                display_role = str(value[-1]) if value is not None else ''
            cls.append_item(model, CompletionValue.asdict(CompletionValue(
                value = value, verbose_name=display_role,
                background = ColorScheme.VALIDATION_ERROR.name(),
                virtual = True
            )))
            return rows
            
    def set_choices( self, choices ):
        """
        :param choices: a list of (value,name) tuples or a list of dicts.

        In case a list of tuples is used, name will be displayed in the combobox,
        while value will be used within :meth:`get_value` and :meth:`set_value`.

        In case a list of dicts is used, the keys of the dict are used as the
        roles, and the values as the value for that role, where `Qt.ItemDataRole.UserRole`
        is the value that is passed through :meth:`get_value`,
        eg : `{Qt.ItemDataRole.DisplayRole: "Hello", Qt.ItemDataRole.UserRole: 1}`

        This method changes the items in the combo box while preserving the
        current value, even if this value is not in the new list of choices.
        If there is no item with value `None` in the list of choices, this will
        be added.
        """
        combobox = self.findChild(QtWidgets.QComboBox, 'combobox')
        current_value = self.get_value()
        current_display_role = str(combobox.itemText(combobox.currentIndex()))
        # set i to -1 to handle case of no available choices
        i = -1
        for i in range(combobox.count(), 0, -1):
            combobox.removeItem(i-1)
        model = combobox.model()
        # the model of the combobox is owned by C++, so it might be
        # deleted before the combobox is deleted
        if is_deleted(model):
            return
        if choices is not None:
            self.append_choices(model, choices)
        self.set_value(current_value, current_display_role)

    def set_tooltip(self, tooltip):
        super().set_tooltip(tooltip)
        combobox = self.findChild(QtWidgets.QComboBox, 'combobox')
        combobox.setToolTip(str(tooltip or ''))

    def set_editable(self, editable):
        combobox = self.findChild(QtWidgets.QComboBox, 'combobox')
        combobox.setEnabled(editable)

    def get_choices(self):
        """This method is only useful for unittest purpose, as it does not
        return an exact copy of the set_choices values.
        """
        combobox = self.findChild(QtWidgets.QComboBox, 'combobox')
        model = combobox.model()
        choices = []
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            choices.append({
                'value': model.data(index, Qt.ItemDataRole.UserRole),
                'verbose_name': model.data(index, Qt.ItemDataRole.DisplayRole),
                'tooltip': model.data(index, Qt.ItemDataRole.ToolTipRole),
                'icon': model.data(index, Qt.ItemDataRole.DecorationRole),
                'foreground': model.data(index, Qt.ItemDataRole.ForegroundRole),
                'background': None,
                'virtual': None,
            })
        return choices

    def set_value(self, value, display_role=None):
        """Set the current value of the combobox where value, the name displayed
        is the one that matches the value in the list set with set_choices

        :param display_role: this is the name used to display the value in case
            the value is not in the list of choices.  If this is `None`, the string
            representation of the value is used.
        """
        value = list(value if value is not None else none_name)
        self.setProperty( 'value', value )
        self.valueChanged.emit()
        combobox = self.findChild(QtWidgets.QComboBox, 'combobox')
        row = self.row_with_value(combobox.model(), value, display_role)
        combobox.setCurrentIndex(row)

    def get_value(self):
        """Get the current value of the combobox"""
        combobox = self.findChild(QtWidgets.QComboBox, 'combobox')
        value = self.value_at_row(combobox.model(), combobox.currentIndex())
        return value

