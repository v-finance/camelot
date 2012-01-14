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


import logging

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QBoxLayout
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QPushButton

logger = logging.getLogger('camelot.view.controls.combobox_input_dialog')

class ComboBoxInputDialog(QDialog):

    def __init__(self, autoaccept=False, parent=None):
        """
        :param autoaccept: if True, the value of the ComboBox is immediately
        accepted after selecting it.
        """
        super(ComboBoxInputDialog, self).__init__(parent)
        self._autoaccept = autoaccept
        layout = QVBoxLayout()
        label = QtGui.QLabel()
        label.setObjectName( 'label' )
        combobox = QtGui.QComboBox()
        combobox.setObjectName( 'combobox' )
        combobox.activated.connect( self._combobox_activated )
        ok_button = QPushButton('OK')
        ok_button.setObjectName( 'ok' )
        cancel_button = QPushButton('Cancel')
        cancel_button.setObjectName( 'cancel' )
        ok_button.pressed.connect(self.accept)
        cancel_button.pressed.connect(self.reject)
        button_layout = QBoxLayout(QBoxLayout.RightToLeft)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addWidget( label )
        layout.addWidget( combobox )
        layout.addLayout( button_layout )
        self.setLayout( layout )

    @QtCore.pyqtSlot(int)
    def _combobox_activated(self, index):
        if self._autoaccept:
            self.accept()
        print index
        
    def set_label_text(self, text):
        label = self.findChild( QtGui.QWidget, 'label' )
        if label != None:
            label.setText( text )

    def set_items(self, items):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            combobox.addItems(items)

    def count(self):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            return combobox.count()
        return 0

    def set_data(self, index, data, role):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            combobox_model = combobox.model()
            model_index = combobox_model.index(index, 0)
            combobox_model.setData(model_index, data, role)

    def get_text(self):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            return combobox.currentText()

    def set_ok_button_default(self):
        ok = self.findChild( QtGui.QWidget, 'ok' )
        if ok != None:
            ok.setFocus()

    def set_cancel_button_default(self):
        cancel = self.findChild( QtGui.QWidget, 'cancel' )
        if cancel != None:
            cancel.setFocus()

    def set_ok_button_text(self, text):
        ok = self.findChild( QtGui.QWidget, 'ok' )
        if ok != None:
            ok.setText(text)

    def set_cancel_button_text(self, text):
        cancel = self.findChild( QtGui.QWidget, 'cancel' )
        if cancel != None:
            cancel.setText(text)

    def set_window_title(self, title):
        self.setWindowTitle(title)
    
    def set_choice_by_text(self, text):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            index = combobox.findText(text)
            self.set_choice_by_index(index)
    
    def set_choice_by_index(self, index):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            combobox.setCurrentIndex(index)
        else:
            raise Exception('No combobox to set the choice')
