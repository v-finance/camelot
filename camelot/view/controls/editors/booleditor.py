#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customeditor import AbstractCustomEditor
from camelot.core import constants
from camelot.core.utils import ugettext

class BoolEditor(QtGui.QCheckBox, AbstractCustomEditor):
    """Widget for editing a boolean field"""
  
    def __init__(self,
                 parent=None,
                 minimum=constants.camelot_minint,
                 maximum=constants.camelot_maxint,
                 editable=True,
                 **kwargs):
        QtGui.QCheckBox.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setEnabled(editable)
        self.connect(self,
                     QtCore.SIGNAL('stateChanged(int)'),
                     self.editingFinished)

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value:
            self.setCheckState(Qt.Checked)
        else:
            self.setCheckState(Qt.Unchecked)

    def get_value(self):
        value = self.isChecked()
        return AbstractCustomEditor.get_value(self) or value

    def editingFinished(self, value=None):
        self.emit(QtCore.SIGNAL('editingFinished()'))

    def set_enabled(self, editable=True):
        value = self.get_value()
        self.setDisabled(not editable)
        self.set_value(value)

    def sizeHint(self):
        size = QtGui.QComboBox().sizeHint()
        return size

class TextBoolEditor(QtGui.QLabel, AbstractCustomEditor):
    def __init__(self,
                 parent=None,
                 yes=ugettext("Yes"),
                 no=ugettext("No"),
                 **kwargs):
        QtGui.QTextEdit.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setEnabled(False)
        self.yes = yes
        self.no = no

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value:
            self.setText(self.yes)
        else:
            self.setText(self.no)
