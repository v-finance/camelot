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

from customeditor import CustomEditor
from camelot.core import constants


class BoolEditor(CustomEditor):
    """Widget for editing a boolean field"""
  
    def __init__(self,
                 parent=None,
                 minimum=constants.camelot_minint,
                 maximum=constants.camelot_maxint,
                 editable=True,
                 **kwargs):
        CustomEditor.__init__(self, parent)
        self.checkBox = QtGui.QCheckBox()
        self.checkBox.setEnabled(editable)
    
        layout = QtGui.QHBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addWidget(self.checkBox)
        self.setFocusProxy(self.checkBox)
        self.setLayout(layout)


    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value:
            self.checkBox.setCheckState(Qt.Checked)
        else:
            self.checkBox.setCheckState(Qt.Unchecked)


    def get_value(self):
        value = self.checkBox.isChecked()
        return CustomEditor.get_value(self) or value


    def editingFinished(self, value=None):
        if value == None:
            value = self.checkBox.isChecked()
        self.emit(QtCore.SIGNAL('editingFinished()'), value)

      
    def set_enabled(self, editable=True):
        value = self.get_value()
        self.checkBox.setDisabled(not editable)
        self.set_value(value)


    def sizeHint(self):
        size = QtGui.QComboBox().sizeHint()
        return size
