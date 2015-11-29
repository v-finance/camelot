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

from ....core.qt import QtGui, QtCore, QtWidgets, Qt
from .customeditor import CustomEditor, set_background_color_palette
from camelot.view.art import Icon
from camelot.view.controls.decorated_line_edit import DecoratedLineEdit
import camelot.types

# older versions of PyQt dont allow passing the regesp in the constructor
# of the validator
email_validator = QtGui.QRegExpValidator()
email_validator.setRegExp(QtCore.QRegExp(r'^\S+\@\S+\.\S+$'))
phone_validator = QtGui.QRegExpValidator()
phone_validator.setRegExp(QtCore.QRegExp(r'^\+?[0-9\s]+$'))
any_character_validator =  QtGui.QRegExpValidator()
any_character_validator.setRegExp(QtCore.QRegExp(r'^.+$'))

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
                 field_name = 'virtual_address',
                 **kwargs):
        """
        :param address_type: limit the allowed address to be entered to be
            of a certain time, can be 'phone', 'fax', 'email', 'mobile', 'pager'.
            If set to None, all types are allowed.
            
        Upto now, the corrected address returned by the address validator is
        not yet taken into account.
        """
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtGui.QSizePolicy.Preferred,
                            QtGui.QSizePolicy.Fixed )
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
        nullIcon = Icon('tango/16x16/apps/internet-mail.png').getQIcon()
        self.label = QtWidgets.QToolButton()
        self.label.setIcon(nullIcon)
        self.label.setAutoRaise(True)
        self.label.setEnabled(False)
        self.label.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.label.setFocusPolicy(Qt.ClickFocus)
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
        value = CustomEditor.set_value(self, value)
        if value is None:
            self.editor.setText('')
        else:
            self.editor.setText(value[1])
            idx = camelot.types.VirtualAddress.virtual_address_types.index(self._address_type or value[0])
            self.combo.setCurrentIndex(idx)
            icon = Icon('tango/16x16/devices/printer.png').getQIcon()
            if six.text_type(self.combo.currentText()) == 'fax':
                icon = Icon('tango/16x16/devices/printer.png').getQIcon()
            if six.text_type(self.combo.currentText()) == 'email':
                icon = Icon('tango/16x16/apps/internet-mail.png').getQIcon()
                self.label.setIcon(icon)
                self.label.show()
            else:
                self.label.hide()
                self.label.setIcon(icon)
                self.label.setToolButtonStyle(Qt.ToolButtonIconOnly)
            self.update_validator()

    def get_value(self):
        address_value = six.text_type(self.editor.text())
        if not len(address_value):
            value = None
        else:
            value = (six.text_type(self.combo.currentText()), address_value)
        return CustomEditor.get_value(self) or value

    def set_enabled(self, editable=True):
        self.combo.setEnabled(editable)
        self.editor.setEnabled(editable)
        if not editable:
            self.label.setEnabled(False)
        else:
            if self.combo.currentText() == 'email':
                self.label.setEnabled(True)

    def update_validator(self):
        address_type = six.text_type(self.combo.currentText())
        validator = validators.get(address_type, any_character_validator)
        # change the validator instead of the regexp of the validator to inform
        # the editor it needs to update its background color
        self.editor.setValidator(validator)

    @QtCore.qt_slot()
    def mail_click(self):
        address = self.editor.text()
        url = QtCore.QUrl()
        url.setUrl( u'mailto:%s?subject=Subject'%six.text_type(address) )
        QtGui.QDesktopServices.openUrl(url)

    def emit_editing_finished(self):
        self.value = []
        self.value.append(six.text_type(self.combo.currentText()))
        self.value.append(six.text_type(self.editor.text()))
        self.set_value(self.value)
        # emiting editingFinished without a value for the mechanism itself will lead to
        # integrity errors
        if self.value[1]:
            self.editingFinished.emit()

    def set_background_color(self, background_color):
        set_background_color_palette( self.editor, background_color )
            
    def set_field_attributes(self, **kwargs):
        super(VirtualAddressEditor, self).set_field_attributes(**kwargs)
        self.set_enabled(kwargs.get('editable', False))
        self.setToolTip(six.text_type(kwargs.get('tooltip') or ''))



