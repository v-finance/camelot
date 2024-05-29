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



from ....core.qt import QtGui, QtCore, QtWidgets, Qt
from .customeditor import CustomEditor, set_background_color_palette
from camelot.view.art import FontIcon
from camelot.view.controls.decorated_line_edit import DecoratedLineEdit
import camelot.types

# older versions of PyQt dont allow passing the regesp in the constructor
# of the validator
email_validator = QtGui.QRegularExpressionValidator()
email_validator.setRegularExpression(QtCore.QRegularExpression(r'^\S+\@\S+\.\S+$'))
phone_validator = QtGui.QRegularExpressionValidator()
phone_validator.setRegularExpression(QtCore.QRegularExpression(r'^\+?[0-9\s]+$'))
any_character_validator =  QtGui.QRegularExpressionValidator()
any_character_validator.setRegularExpression(QtCore.QRegularExpression(r'^.+$'))

validators = {
    'email': email_validator,
    'phone': phone_validator,
    'pager': phone_validator,
    'fax': phone_validator,
    'mobile': phone_validator
    }

class VirtualAddressEditor(CustomEditor):

    def __init__(self,
                 parent = None,
                 address_type = None,
                 field_name = 'virtual_address'):
        """
        :param address_type: limit the allowed address to be entered to be
            of a certain time, can be 'phone', 'fax', 'email', 'mobile', 'pager'.
            If set to None, all types are allowed.
            
        Upto now, the corrected address returned by the address validator is
        not yet taken into account.
        """
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtWidgets.QSizePolicy.Policy.Preferred,
                            QtWidgets.QSizePolicy.Policy.Fixed )
        self.setObjectName( field_name )
        self._address_type = address_type
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins( 0, 0, 0, 0)
        self.combo = QtWidgets.QComboBox()
        self.combo.addItems(camelot.types.VirtualAddress.virtual_address_types)
        self.layout.addWidget(self.combo)
        self.editor = DecoratedLineEdit(self)
        self.editor.set_minimum_width(30)
        if address_type:
            self.combo.setVisible(False)
            idx = camelot.types.VirtualAddress.virtual_address_types.index(address_type)
            self.combo.setCurrentIndex(idx)
        self.layout.addWidget(self.editor)
        self.setFocusProxy(self.editor)
        nullIcon = FontIcon('envelope-open').getQIcon() # 'tango/16x16/apps/internet-mail.png'
        self.label = QtWidgets.QToolButton()
        self.label.setIcon(nullIcon)
        self.label.setAutoRaise(True)
        self.label.setEnabled(False)
        self.label.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.label.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.label.clicked.connect( self.mail_click )
        self.label.hide()
        self.layout.addWidget(self.label)
        self.editor.editingFinished.connect(self.emit_editing_finished)
        self.combo.currentIndexChanged.connect(self.comboIndexChanged)
        self.setLayout(self.layout)
        self.update_validator()

    @QtCore.qt_slot()
    def comboIndexChanged(self):
        self.update_validator()
        self.emit_editing_finished()

    def set_value(self, value):
        if value is None:
            self.editor.setText('')
        else:
            self.editor.setText(value[1])
            idx = camelot.types.VirtualAddress.virtual_address_types.index(self._address_type or value[0])
            self.combo.setCurrentIndex(idx)
            icon = FontIcon('print').getQIcon() # 'tango/16x16/devices/printer.png'
            if str(self.combo.currentText()) == 'fax':
                icon = FontIcon('fax').getQIcon() # 'tango/16x16/devices/printer.png'
            if str(self.combo.currentText()) == 'email':
                icon = FontIcon('envelope-open').getQIcon() # 'tango/16x16/apps/internet-mail.png'
                self.label.setIcon(icon)
                self.label.show()
            else:
                self.label.hide()
                self.label.setIcon(icon)
                self.label.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            self.update_validator()

    def get_value(self):
        address_value = str(self.editor.text())
        if not len(address_value):
            value = None
        else:
            value = (str(self.combo.currentText()), address_value)
        return value

    def set_enabled(self, editable=True):
        self.combo.setEnabled(editable)
        self.editor.setEnabled(editable)
        if not editable:
            self.label.setEnabled(False)
        else:
            if self.combo.currentText() == 'email':
                self.label.setEnabled(True)

    def update_validator(self):
        address_type = str(self.combo.currentText())
        validator = validators.get(address_type, any_character_validator)
        # change the validator instead of the regexp of the validator to inform
        # the editor it needs to update its background color
        self.editor.setValidator(validator)

    @QtCore.qt_slot()
    def mail_click(self):
        address = self.editor.text()
        url = QtCore.QUrl()
        url.setUrl( u'mailto:%s?subject=Subject'%str(address) )
        QtGui.QDesktopServices.openUrl(url)

    def emit_editing_finished(self):
        self.value = []
        self.value.append(str(self.combo.currentText()))
        self.value.append(str(self.editor.text()))
        self.set_value(self.value)
        # emiting editingFinished without a value for the mechanism itself will lead to
        # integrity errors
        if self.value[1]:
            self.editingFinished.emit()

    def set_background_color(self, background_color):
        set_background_color_palette( self.editor, background_color )

    def set_editable(self, editable):
        self.set_enabled(editable)
