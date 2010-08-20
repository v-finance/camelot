#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4 import QtGui

from customeditor import AbstractCustomEditor

class TextLineEditor(QtGui.QLineEdit, AbstractCustomEditor):

    def __init__(self, parent, length=20, editable=True, **kwargs):
        QtGui.QLineEdit.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        if length:
            self.setMaxLength(length)
        if not editable:
            self.setEnabled(False)

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value is not None:
            self.setText(unicode(value))
        else:
            self.setText('')
        return value

    def get_value(self):
        val = AbstractCustomEditor.get_value(self)
        if val is not None:
            return val
        val = unicode(self.text())
        if not val and self.value_is_none:
            return None
        return val

    def set_enabled(self, editable=True):
        value = self.text()
        self.setEnabled(editable)
        self.setText(value)
