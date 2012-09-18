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

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from customeditor import AbstractCustomEditor
from camelot.core import constants
from camelot.core.utils import ugettext

class BoolEditor(QtGui.QCheckBox, AbstractCustomEditor):
    """Widget for editing a boolean field"""

    editingFinished = QtCore.pyqtSignal()
    
    def __init__(self,
                 parent=None,
                 minimum=constants.camelot_minint,
                 maximum=constants.camelot_maxint,
                 nullable=True,
                 field_name = 'boolean',
                 **kwargs):
        QtGui.QCheckBox.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setObjectName( field_name )
        self._nullable = nullable
        self.clicked.connect( self._state_changed )

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value:
            self.setCheckState(Qt.Checked)
        else:
            self.setCheckState(Qt.Unchecked)

    def get_value(self):
        value_loading = AbstractCustomEditor.get_value(self)
        if value_loading is not None:
            return value_loading
        state = self.checkState()
        if state==Qt.Unchecked:
            return False
        return True

    def set_field_attributes( self, editable = True, **kwargs ):
        AbstractCustomEditor.set_field_attributes( self, **kwargs )
        self.setDisabled( not editable )
        
    @QtCore.pyqtSlot( bool )
    def _state_changed(self, value=None):
        self.editingFinished.emit()

    def sizeHint(self):
        size = QtGui.QComboBox().sizeHint()
        return size

class TextBoolEditor(QtGui.QLabel, AbstractCustomEditor):
    """
    :Parameter:
        color_yes: string
            text-color of the True representation
        color_no: string
            text-color of the False representation
    """
    editingFinished = QtCore.pyqtSignal()
    
    def __init__(self,
                 parent=None,
                 yes="Yes",
                 no="No",
                 color_yes=None,
                 color_no=None,
                 **kwargs):
        QtGui.QLabel.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setEnabled(False)
        self.yes = ugettext(yes)
        self.no = ugettext(no)
        self.color_yes = color_yes
        self.color_no = color_no

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value:
            self.setText(self.yes)
            if self.color_yes:
                selfpalette = self.palette()
                selfpalette.setColor(QtGui.QPalette.WindowText, self.color_yes)
                self.setPalette(selfpalette)
        else:
            self.setText(self.no)
            if self.color_no:
                selfpalette = self.palette()
                selfpalette.setColor(QtGui.QPalette.WindowText, self.color_no)
                self.setPalette(selfpalette)
