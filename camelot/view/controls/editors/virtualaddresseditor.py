#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

from customeditor import CustomEditor
from camelot.view.art import Icon
import camelot.types

class VirtualAddressEditor(CustomEditor):

    def __init__(self, parent=None, editable=True, address_type=None, **kwargs):
        CustomEditor.__init__(self, parent)
        self._address_type = address_type
        self.layout = QtGui.QHBoxLayout()
        self.layout.setMargin(0)
        self.combo = QtGui.QComboBox()
        self.combo.addItems(camelot.types.VirtualAddress.virtual_address_types)
        self.combo.setEnabled(editable)
        if address_type:
            self.combo.setVisible(False)
        self.layout.addWidget(self.combo)
        self.editor = QtGui.QLineEdit()
        self.editor.setEnabled(editable)
        self.layout.addWidget(self.editor)
        self.setFocusProxy(self.editor)
        self.editable = editable
        nullIcon = Icon('tango/16x16/apps/internet-mail.png').getQIcon()
        self.label = QtGui.QToolButton()
        self.label.setIcon(nullIcon)
        self.label.setAutoFillBackground(False)
        self.label.setAutoRaise(True)
        self.label.setEnabled(False)
        self.label.setToolButtonStyle(Qt.ToolButtonIconOnly)

        self.layout.addWidget(self.label)
        self.editor.editingFinished.connect(self.emit_editing_finished)
        self.editor.textEdited.connect(self.editorValueChanged)
        self.combo.currentIndexChanged.connect(self.comboIndexChanged)

        self.setLayout(self.layout)
        self.setAutoFillBackground(True)
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
                self.label.setAutoRaise(True)
                #self.label.setAutoFillBackground(True)
                self.label.setIcon(icon)
                self.label.setEnabled(self.editable)
                self.label.clicked.connect(
                    lambda:self.mailClick(self.editor.text())
                )
            else:
                self.label.setIcon(icon)
                #self.label.setAutoFillBackground(False)
                self.label.setAutoRaise(True)
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
        if self.combo.currentText() == 'email':
            email = unicode(text)
            mailCheck = re.compile('^\S+@\S+\.\S+$')
            if not mailCheck.match(email):
                palette = self.editor.palette()
                palette.setColor(QtGui.QPalette.Active,
                                 QtGui.QPalette.Base,
                                 QtGui.QColor(255, 0, 0))
                self.editor.setPalette(palette)
            else:
                palette = self.editor.palette()
                palette.setColor(QtGui.QPalette.Active,
                                 QtGui.QPalette.Base,
                                 QtGui.QColor(255, 255, 255))
                self.editor.setPalette(palette)

        elif self.combo.currentText() == 'phone' \
         or self.combo.currentText() == 'pager' \
         or self.combo.currentText() == 'fax' \
         or self.combo.currentText() == 'mobile':

            number = unicode(text)
            numberCheck = re.compile('^[0-9 ]+$')

            if not numberCheck.match(number):
                palette = self.editor.palette()
                palette.setColor(QtGui.QPalette.Active,
                                 QtGui.QPalette.Base,
                                 QtGui.QColor(255, 0, 0))
                self.editor.setPalette(palette)
            else:
                palette = self.editor.palette()
                palette.setColor(QtGui.QPalette.Active,
                                 QtGui.QPalette.Base,
                                 QtGui.QColor(255, 255, 255))
                self.editor.setPalette(palette)

        else:
            Check = re.compile('^.+$')
            if not Check.match(unicode(text)):
                palette = self.editor.palette()
                palette.setColor(QtGui.QPalette.Active,
                                 QtGui.QPalette.Base,
                                  QtGui.QColor(255, 0, 0))
                self.editor.setPalette(palette)
            else:
                palette = self.editor.palette()
                palette.setColor(QtGui.QPalette.Active,
                                  QtGui.QPalette.Base,
                                  QtGui.QColor(255, 255, 255))
                self.editor.setPalette(palette)

    def editorValueChanged(self, text):
        self.checkValue(text)

    def mailClick(self, adress):
        url = QtCore.QUrl()
        url.setUrl('mailto:%s?subject=Subject'%str(adress))
        QtGui.QDesktopServices.openUrl(url)

    def emit_editing_finished(self):
        self.value = []
        self.value.append(str(self.combo.currentText()))
        self.value.append(str(self.editor.text()))
        self.set_value(self.value)
        self.label.setFocus()
        # emiting editingFinished without a value for the mechanism itself will lead to
        # integrity errors
        if self.value[1]:
            self.editingFinished.emit()

    def set_background_color(self, background_color):
        if background_color:
            palette = self.editor.palette()
            palette.setColor(self.backgroundRole(), background_color)
            self.editor.setPalette(palette)
        else:
            return False
            
    def set_field_attributes(self, editable=True, background_color=None, tooltip = '', **kwargs):
        self.set_enabled(editable)
        self.set_background_color(background_color)
        
        if tooltip:
            '''self.editor.setStyleSheet("""QLineEdit {
                                              background-image: url(:/tooltip_visualization_7x7_glow.png);
                                              background-position: top left;
                                              background-repeat: no-repeat; }""")'''
            self.editor.setToolTip(unicode(tooltip))

