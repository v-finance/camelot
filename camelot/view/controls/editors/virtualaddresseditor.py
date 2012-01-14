#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
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
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

import re

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from customeditor import CustomEditor, set_background_color_palette
from camelot.view.art import Icon
from camelot.view.controls.decorated_line_edit import DecoratedLineEdit
import camelot.types

email_expression = re.compile('^\S+@\S+\.\S+$')
phone_expression = re.compile('^[0-9 ]+$')
any_character_expression =  re.compile('^.+$')

def default_address_validator( address_type, address ):
    """Validates wether a virtual address is valid and
    correct it if possible.
    :param address_type: the type of address to validate, eg 'phone'
    :param address: the address itself
    :return: (valid, corrected_address) a tuple with a :type:`boolean`
        indicating if the address is valid and a string with the corrected
        address.
    """
    if not address:
        return ( True, address )
    if address_type == 'email':
        return ( email_expression.match( address ), address )
    if address_type in ('phone', 'pager', 'fax', 'mobile'):
        return ( phone_expression.match( address ), address )
    return ( any_character_expression.match( address ), address )
                
class VirtualAddressEditor(CustomEditor):

    def __init__(self, 
                 parent = None, 
                 editable = True, 
                 address_type = None, 
                 address_validator = default_address_validator,
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
        self.setObjectName( field_name )
        self._address_type = address_type
        self._address_validator = address_validator
        self.layout = QtGui.QHBoxLayout()
        self.layout.setContentsMargins( 0, 0, 0, 0)
        self.combo = QtGui.QComboBox()
        self.combo.addItems(camelot.types.VirtualAddress.virtual_address_types)
        self.combo.setEnabled(editable)
        if address_type:
            self.combo.setVisible(False)
        self.layout.addWidget(self.combo)
        self.editor = DecoratedLineEdit( self )
        self.editor.setEnabled(editable)
        self.editor.set_minimum_width( 30 )
        self.layout.addWidget(self.editor)
        self.setFocusProxy(self.editor)
        self.editable = editable
        nullIcon = Icon('tango/16x16/apps/internet-mail.png').getQIcon()
        self.label = QtGui.QToolButton()
        self.label.setIcon(nullIcon)
        self.label.setAutoRaise(True)
        self.label.setEnabled(False)
        self.label.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.label.setFocusPolicy(Qt.ClickFocus)
        self.label.clicked.connect( self.mail_click )
        self.label.hide()

        self.layout.addWidget(self.label)
        self.editor.editingFinished.connect(self.emit_editing_finished)
        self.editor.textEdited.connect(self.editorValueChanged)
        self.combo.currentIndexChanged.connect(self.comboIndexChanged)

        self.setLayout(self.layout)
        self.checkValue(self.editor.text())

    @QtCore.pyqtSlot()
    def comboIndexChanged(self):
        self.checkValue(self.editor.text())
        self.emit_editing_finished()

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value:
            self.editor.setText(value[1])
            idx = camelot.types.VirtualAddress.virtual_address_types.index(self._address_type or value[0])
            self.combo.setCurrentIndex(idx)
            icon = Icon('tango/16x16/devices/printer.png').getQIcon()
# These icons don't exist any more in the new tango icon set
#            if str(self.combo.currentText()) == 'phone':
#                icon = Icon('tango/16x16/devices/phone.png').getQIcon()
            if str(self.combo.currentText()) == 'fax':
                icon = Icon('tango/16x16/devices/printer.png').getQIcon()
#            if str(self.combo.currentText()) == 'mobile':
#                icon = Icon('tango/16x16/devices/mobile.png').getQIcon()
#            if str(self.combo.currentText()) == 'im':
#                icon = Icon('tango/16x16/places/instant-messaging.png').getQIcon()
#            if str(self.combo.currentText()) == 'pager':
#                icon = Icon('tango/16x16/devices/pager.png').getQIcon()
            if str(self.combo.currentText()) == 'email':
                icon = Icon('tango/16x16/apps/internet-mail.png').getQIcon()
                #self.label.setFocusPolicy(Qt.StrongFocus)
                #self.label.setAutoFillBackground(True)
                self.label.setIcon(icon)
                self.label.setEnabled( self.editable )
                self.label.show()
            else:
                self.label.hide()
                self.label.setIcon(icon)
                self.label.setEnabled(self.editable)
                self.label.setToolButtonStyle(Qt.ToolButtonIconOnly)

#      self.update()
#      self.label.update()
#      self.layout.update()


            self.checkValue(value[1])

    def get_value(self):
        value = (unicode(self.combo.currentText()), unicode(self.editor.text()))
        return CustomEditor.get_value(self) or value

    def set_enabled(self, editable=True):
        self.combo.setEnabled(editable)
        self.editor.setEnabled(editable)
        if not editable:
            self.label.setEnabled(False)
        else:
            if self.combo.currentText() == 'email':
                self.label.setEnabled(True)

    def checkValue(self, text):
        address_type = unicode( self.combo.currentText() )
        valid, _corrected = self._address_validator( address_type, unicode( text ) )
        self.editor.set_valid( valid )

    def editorValueChanged(self, text):
        self.checkValue(text)

    @QtCore.pyqtSlot()
    def mail_click(self):
        address = self.editor.text()
        url = QtCore.QUrl()
        url.setUrl( u'mailto:%s?subject=Subject'%unicode(address) )
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
            
    def set_field_attributes(self, editable = True,
                                   background_color = None,
                                   tooltip = None, **kwargs):
        self.set_enabled(editable)
        self.set_background_color(background_color)
        self.setToolTip(unicode(tooltip or ''))


