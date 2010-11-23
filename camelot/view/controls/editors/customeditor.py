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

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.core.constants import *
from camelot.view.proxy import ValueLoading
from camelot.core.utils import create_constant_function

class AbstractCustomEditor(object):
    """Helper class to be used to build custom editors.  This class provides
  functionality to store and retrieve `ValueLoading` as an editor's value.
  """

    def __init__(self):
        self._value_loading = True
        self.value_is_none = False

    def set_value(self, value):
        if value == ValueLoading:
            self._value_loading = True
            return None
        else:
            self._value_loading = False
            if value is None:
                self.value_is_none = True
            else:
                self.value_is_none = False
            return value

    def get_value(self):
        if self._value_loading:
            return ValueLoading
        return None

    def set_field_attributes(self, editable=True, background_color=None, **kwargs):
        self.setEnabled(editable)
        self.set_background_color(background_color)

    """
    Get the 'standard' height for a cell
    """
    def get_height(self):

        height = [QtGui.QLineEdit().sizeHint().height(),
               QtGui.QDateEdit().sizeHint().height(),
               QtGui.QDateTimeEdit().sizeHint().height(),
               QtGui.QSpinBox().sizeHint().height(),
               QtGui.QDateEdit().sizeHint().height(),
               QtGui.QComboBox().sizeHint().height()]

        finalHeight = max(height)

        return finalHeight

    def set_background_color(self, background_color):
        if background_color not in (None, ValueLoading):
            palette = self.palette()
            for x in [QtGui.QPalette.Active, QtGui.QPalette.Inactive, QtGui.QPalette.Disabled]:
                for y in [self.backgroundRole(), QtGui.QPalette.Window]:
                    palette.setColor(x, y, background_color)
            self.setPalette(palette)
        else:
            return False

class CustomEditor(QtGui.QWidget, AbstractCustomEditor):
    """Base class for implementing custom editor widgets.  This class provides
  dual state functionality.  Each editor should have the posibility to have as
  its value `ValueLoading` specifying that no value has been set yet.
  """

    editingFinished = QtCore.pyqtSignal()
    valueChanged = QtCore.pyqtSignal()

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        AbstractCustomEditor.__init__(self)

