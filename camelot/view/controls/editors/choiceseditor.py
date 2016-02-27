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

import six

from ....core.qt import QtGui, QtCore, QtWidgets, Qt, py_to_variant, variant_to_py
from camelot.view.proxy import ValueLoading
from ...art import Icon, ColorScheme
from .customeditor import CustomEditor

LOGGER = logging.getLogger('camelot.view.controls.editors.ChoicesEditor')

class ChoicesEditor(CustomEditor):
    """A ComboBox aka Drop Down box that can be assigned a list of
    keys and values"""

    editingFinished = QtCore.qt_signal()
    valueChanged = QtCore.qt_signal()

    def __init__( self,
                  parent = None,
                  nullable = True,
                  field_name = 'choices',
                  actions = [],
                  **kwargs ):
        super(ChoicesEditor, self).__init__(parent)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
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
        self.set_choices([(None, '')])
        self.setLayout(layout)
        self.add_actions(actions, layout)

    @QtCore.qt_slot(int)
    def _activated(self, _index):
        self.setProperty( 'value', py_to_variant( self.get_value() ) )
        self.valueChanged.emit()
        self.editingFinished.emit()

    @staticmethod
    def append_item( model, data ):
        """Append an item in a combobox model
        :param data: a dictionary mapping roles to values
        """
        model.insertRow(model.rowCount())

        for role, value in six.iteritems(data):
            index = model.index(model.rowCount()-1, 0)
            if isinstance(value, Icon):
                value = value.getQIcon()
            model.setData(index, py_to_variant(value), role)

    def set_choices( self, choices ):
        """
        :param choices: a list of (value,name) tuples or a list of dicts.

        In case a list of tuples is used, name will be displayed in the combobox,
        while value will be used within :meth:`get_value` and :meth:`set_value`.

        In case a list of dicts is used, the keys of the dict are used as the
        roles, and the values as the value for that role, where `Qt.UserRole`
        is the value that is passed through :meth:`get_value`,
        eg : `{Qt.DisplayRole: "Hello", Qt.UserRole: 1}`

        This method changes the items in the combo box while preserving the
        current value, even if this value is not in the new list of choices.
        If there is no item with value `None` in the list of choices, this will
        be added.
        """
        combobox = self.findChild(QtWidgets.QComboBox, 'combobox')
        current_value = self.get_value()
        current_display_role = six.text_type(combobox.itemText(combobox.currentIndex()))
        none_available = False
        # set i to -1 to handle case of no available choices
        i = -1
        for i in range(combobox.count(), 0, -1):
            combobox.removeItem(i-1)
        model = combobox.model()
        for choice in choices:
            if not isinstance(choice, dict):
                (value, name) = choice
                font = QtGui.QFont()
                font.setItalic(True)
                choice = {Qt.DisplayRole: six.text_type(name),
                          Qt.UserRole: value}
            else:
                value = choice[Qt.UserRole]
            self.append_item(model, choice)
            if value is None:
                none_available = True
        if not none_available:
            self.append_item(model, {Qt.DisplayRole: '',
                                     Qt.UserRole: None})
        # to prevent loops in the onetomanychoices editor, only set the value
        # again when it's not valueloading
        if current_value != ValueLoading:
            self.set_value(current_value, current_display_role)

    def set_field_attributes(self, **fa):
        super(ChoicesEditor, self).set_field_attributes(**fa)
        combobox = self.findChild(QtWidgets.QComboBox, 'combobox')
        if fa.get('choices') is not None:
            self.set_choices(fa['choices'])
        combobox.setEnabled(fa.get('editable', True))

    def get_choices(self):
        """
    :rtype: a list of (value,name) tuples
    """
        combobox = self.findChild(QtWidgets.QComboBox, 'combobox')
        return [(variant_to_py(combobox.itemData(i)),
                 six.text_type(combobox.itemText(i))) for i in range(combobox.count())]

    def set_value(self, value, display_role=None):
        """Set the current value of the combobox where value, the name displayed
        is the one that matches the value in the list set with set_choices
        
        :param display_role: this is the name used to display the value in case
            the value is not in the list of choices.  If this is `None`, the string
            representation of the value is used.
        """
        value = super(ChoicesEditor, self).set_value(value)
        self.setProperty( 'value', py_to_variant(value) )
        self.valueChanged.emit()
        if not variant_to_py(self.property('value_loading')) and value != NotImplemented:
            combobox = self.findChild(QtWidgets.QComboBox, 'combobox')
            number_of_items = combobox.count()
            # remove the last item if it was an invalid one
            if variant_to_py(combobox.itemData(number_of_items-1, Qt.UserRole+1))==True:
                combobox.removeItem(number_of_items-1)
                number_of_items -= 1
            for i in range(number_of_items):
                if value == variant_to_py(combobox.itemData(i)):
                    combobox.setCurrentIndex(i)
                    break
            else:
                # it might happen, that when we set the editor data, the set_choices
                # method has not happened yet or the choices don't contain the value
                # set
                if display_role is None:
                    display_role = six.text_type(value)
                self.append_item(combobox.model(),
                                  {Qt.DisplayRole: display_role,
                                   Qt.BackgroundRole: QtGui.QBrush(ColorScheme.VALIDATION_ERROR),
                                   Qt.UserRole: value,
                                   Qt.UserRole+1: True})
                combobox.setCurrentIndex(number_of_items)
        self.update_actions()

    def get_value(self):
        """Get the current value of the combobox"""
        combobox = self.findChild(QtWidgets.QComboBox, 'combobox')
        current_index = combobox.currentIndex()
        if current_index >= 0:
            value = variant_to_py(combobox.itemData(combobox.currentIndex()))
        else:
            value = ValueLoading
        return super(ChoicesEditor, self).get_value() or value

