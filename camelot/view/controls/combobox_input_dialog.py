#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QComboBox
from PyQt4.QtGui import QBoxLayout
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QPushButton


logger = logging.getLogger('camelot.view.controls.combobox_input_dialog')


class ComboBoxInputDialog(QDialog):

    def __init__(self, parent=None):
        super(ComboBoxInputDialog, self).__init__(parent)
        self._layout = QVBoxLayout()
        self._set_buttons()
        self.setLayout(self._layout)

    def set_label_text(self, text):
        self.label = QLabel(text)
        self._layout.insertWidget(0, self.label)

    def set_items(self, items):
        self.combobox = QComboBox()
        self.combobox.addItems(items)
        self._layout.insertWidget(1, self.combobox)

        self.registered_functions = {}
        self.combobox.activated[int].connect(self._make_call_if_registered)

    def count(self):
        return self.combobox.count()

    def set_item_font(self, index, qfont=None):
        combobox_model = self.combobox.model()
        model_index = combobox_model.index(index, 0)
        combobox_model.setData(model_index, qfont, Qt.FontRole)

    def get_text(self):
        return self.combobox.currentText()

    def _set_buttons(self):
        self.ok_button = QPushButton('OK')
        self.cancel_button = QPushButton('Cancel')

        self.ok_button.pressed.connect(self.accept)
        self.cancel_button.pressed.connect(self.reject)

        self.button_layout = QBoxLayout(QBoxLayout.RightToLeft)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.ok_button)

        self._layout.insertLayout(2, self.button_layout)

    def set_ok_button_default(self):
        self.ok_button.setFocus()

    def set_cancel_button_default(self):
        self.cancel_button.setFocus()

    def set_ok_button_text(self, text):
        self.ok_button.setText(text)

    def set_cancel_button_text(self, text):
        self.cancel_button.setText(text)

    def set_window_title(self, title):
        self.setWindowTitle(title)

    def register_on_index(self, index, func, *a, **kw):
        self.registered_functions[index] = lambda: func(*a, **kw)

    def _make_call_if_registered(self, index):
        if self.registered_functions and index in self.registered_functions:
            self.registered_functions[index]()
