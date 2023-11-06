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



from ....core.qt import QtCore, QtGui, QtWidgets
from camelot.view.validator import AbstractValidator
from camelot.view.completer import AbstractCompleter

from .customeditor import (CustomEditor, set_background_color_palette)
from ..decorated_line_edit import DecoratedLineEdit


class TextLineEditor(CustomEditor):

    def __init__(self,
                 parent,
                 length=20,
                 echo_mode=None,
                 column_width=None,
                 action_routes=[],
                 validator_type=None,
                 completer_type=None,
                 field_name='text_line'):
        CustomEditor.__init__(self, parent, column_width=column_width)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                           QtWidgets.QSizePolicy.Policy.Fixed)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        # Search input
        text_input = DecoratedLineEdit(self)
        text_input.setObjectName('text_input')
        text_input.editingFinished.connect(self.text_input_editing_finished)
        if echo_mode is not None:
            text_input.setEchoMode(QtWidgets.QLineEdit.EchoMode(echo_mode))
        else:
            text_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
        validator = AbstractValidator.get_validator(validator_type, self)
        if validator is not None:
            validator.setObjectName('validator')
            text_input.setValidator(validator)
        completer = AbstractCompleter.get_completer(completer_type, self)
        if completer is not None:
            completer.setObjectName('completer')
            text_input.setCompleter(completer)
        layout.addWidget(text_input)
        if length:
            text_input.setMaxLength(length)
        self.setFocusProxy(text_input)
        self.setObjectName(field_name)
        self._value = None
        self.add_actions(action_routes, layout)
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
                text_input.setText(str(value))
            else:
                text_input.setText('')
        return value

    def get_value(self):
        value_loading = CustomEditor.get_value(self)
        if value_loading is not None:
            return value_loading

        text_input = self.findChild(QtWidgets.QLineEdit, 'text_input')
        if text_input is not None:
            value = str(text_input.text())
            if len(value) == 0:
                # convert an empty string to None, but not if the original
                # value itself was an empty string
                if (self._value is not None) and (len(self._value) == 0):
                    return self._value
                return None
            return value

    value = QtCore.qt_property(str, get_value, set_value)

    def set_validator_state(self, validator_state):
        validator = self.findChild(QtGui.QValidator, 'validator')
        if validator is not None:
            validator.set_state(validator_state)

    def set_tooltip(self, tooltip):
        super().set_tooltip(tooltip)
        text_input = self.findChild(QtWidgets.QLineEdit, 'text_input')
        if text_input is not None:
            text_input.setToolTip(str(tooltip or ''))

    def set_background_color(self, background_color):
        super().set_background_color(background_color)
        text_input = self.findChild(QtWidgets.QLineEdit, 'text_input')
        if text_input is not None:
            set_background_color_palette(text_input, background_color)

    def set_completer_state(self, completer_state):
        completer = self.findChild(QtWidgets.QCompleter, 'completer')
        if completer is not None:
            completer.set_state(completer_state)

    def set_editable(self, editable):
        text_input = self.findChild(QtWidgets.QLineEdit, 'text_input')
        if text_input is not None:
            value = text_input.text()
            text_input.setReadOnly(not editable)
            text_input.setText(value)
