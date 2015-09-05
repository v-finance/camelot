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

import six

from ....core.qt import QtCore, QtGui, QtWidgets

from .customeditor import (CustomEditor, set_background_color_palette)
from ..decorated_line_edit import DecoratedLineEdit


class TextLineEditor(CustomEditor):

    def __init__(self,
                 parent,
                 length=20,
                 echo_mode=None,
                 field_name='text_line',
                 actions=[],
                 column_width=None,
                 **kwargs):
        CustomEditor.__init__(self, parent, column_width=column_width)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred,
                           QtGui.QSizePolicy.Fixed)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        # Search input
        text_input = DecoratedLineEdit(self)
        text_input.setObjectName('text_input')
        text_input.editingFinished.connect(self.text_input_editing_finished)
        text_input.setEchoMode(echo_mode or QtWidgets.QLineEdit.Normal)
        layout.addWidget(text_input)
        if length:
            text_input.setMaxLength(length)
        self.setFocusProxy(text_input)
        self.setObjectName(field_name)
        self._value = None
        self.add_actions(actions, layout)
        self.setLayout(layout)

    @QtCore.qt_slot()
    def text_input_editing_finished(self):
        self.editingFinished.emit()

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        self._value = value
        text_input = self.findChild(QtWidgets.QLineEdit, 'text_input')
        if text_input is not None:
            if value is not None:
                text_input.setText(six.text_type(value))
            else:
                text_input.setText('')
        return value

    def get_value(self):
        value_loading = CustomEditor.get_value(self)
        if value_loading is not None:
            return value_loading

        text_input = self.findChild(QtWidgets.QLineEdit, 'text_input')
        if text_input is not None:
            value = six.text_type(text_input.text())
            if len(value) == 0:
                # convert an empty string to None, but not if the original
                # value itself was an empty string
                if (self._value is not None) and (len(self._value) == 0):
                    return self._value
                return None
            return value

    value = QtCore.qt_property(six.text_type, get_value, set_value)

    def set_field_attributes(self, **kwargs):
        super(TextLineEditor, self).set_field_attributes(**kwargs)
        text_input = self.findChild(QtWidgets.QLineEdit, 'text_input')
        validator = kwargs.get('validator')
        if text_input is not None:
            editable = kwargs.get('editable', False)
            value = text_input.text()
            text_input.setEnabled(editable)
            text_input.setText(value)
            text_input.setToolTip(six.text_type(kwargs.get('tooltip') or ''))
            set_background_color_palette(text_input,
                                         kwargs.get('background_color'))
            text_input.setValidator(validator)
