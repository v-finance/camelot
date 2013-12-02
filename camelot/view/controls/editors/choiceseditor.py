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

import logging

import six
from PyQt4.QtCore import Qt

from ....core.qt import QtGui, QtCore, py_to_variant, variant_to_py
from camelot.view.proxy import ValueLoading
from ...art import Icon
from .customeditor import CustomEditor

LOGGER = logging.getLogger('camelot.view.controls.editors.ChoicesEditor')

class ChoicesEditor(CustomEditor):
    """A ComboBox aka Drop Down box that can be assigned a list of
    keys and values"""

    editingFinished = QtCore.pyqtSignal()
    valueChanged = QtCore.pyqtSignal()

    def __init__( self,
                  parent = None,
                  nullable = True,
                  field_name = 'choices',
                  actions = [],
                  **kwargs ):
        super(ChoicesEditor, self).__init__(parent)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        combobox = QtGui.QComboBox()
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

    @QtCore.pyqtSlot(int)
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
            model.setData(index, variant_to_py(value), role)

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
        combobox = self.findChild(QtGui.QComboBox, 'combobox')
        current_index = combobox.currentIndex()
        if current_index >= 0:
            current_name = six.text_type(combobox.itemText(current_index))
        current_value = self.get_value()
        current_value_available = False
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
            if value == current_value:
                current_value_available = True
            if value is None:
                none_available = True
        if not current_value_available and current_index > 0:
            if current_value is None:
                none_available = True
            self.append_item(model, {Qt.DisplayRole: current_name,
                                     Qt.UserRole: current_value})
        if not none_available:
            self.append_item(model, {Qt.DisplayRole: '',
                                     Qt.UserRole: None})
        # to prevent loops in the onetomanychoices editor, only set the value
        # again when it's not valueloading
        if current_value != ValueLoading:
            self.set_value( current_value )

    def set_field_attributes(self, **fa):
        self.field_attributes = fa
        combobox = self.findChild(QtGui.QComboBox, 'combobox')
        if fa.get('choices') is not None:
            self.set_choices(fa['choices'])
        combobox.setEnabled(fa.get('editable', True))

    def get_choices(self):
        """
    :rtype: a list of (value,name) tuples
    """
        combobox = self.findChild(QtGui.QComboBox, 'combobox')
        return [(variant_to_py(combobox.itemData(i)),
                 six.text_type(combobox.itemText(i))) for i in range(combobox.count())]

    def set_value(self, value):
        """Set the current value of the combobox where value, the name displayed
        is the one that matches the value in the list set with set_choices"""
        value = super(ChoicesEditor, self).set_value(value)
        self.setProperty( 'value', py_to_variant(value) )
        self.valueChanged.emit()
        if not variant_to_py(self.property('value_loading')) and value != NotImplemented:
            combobox = self.findChild(QtGui.QComboBox, 'combobox')
            for i in range(combobox.count()):
                if value == variant_to_py(combobox.itemData(i)):
                    combobox.setCurrentIndex(i)
                    self.update_actions()
                    return
            # it might happen, that when we set the editor data, the set_choices
            # method has not happened yet or the choices don't contain the value
            # set
            combobox.setCurrentIndex( -1 )
            LOGGER.error( u'Could not set value %s in field %s because it is not in the list of choices'%( six.text_type( value ),
                                                                                                           six.text_type( self.objectName() ) ) )
        self.update_actions()

    def get_value(self):
        """Get the current value of the combobox"""
        combobox = self.findChild(QtGui.QComboBox, 'combobox')
        current_index = combobox.currentIndex()
        if current_index >= 0:
            value = variant_to_py(combobox.itemData(combobox.currentIndex()))
        else:
            value = ValueLoading
        return super(ChoicesEditor, self).get_value() or value
