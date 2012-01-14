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
from PyQt4 import QtCore

from wideeditor import WideEditor
from customeditor import AbstractCustomEditor, QtGui

class TextEditEditor(QtGui.QTextEdit, AbstractCustomEditor, WideEditor):

    editingFinished = QtCore.pyqtSignal()
 
    def __init__(self, 
                 parent, 
                 length=20, 
                 editable=True, 
                 field_name = 'text',
                 **kwargs):
        QtGui.QTextEdit.__init__(self, parent)
        self.setObjectName( field_name )
        AbstractCustomEditor.__init__(self)
        self.setReadOnly(not editable)

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        #if value:
        #    self.setText(unicode(value))
        #else:
        #    self.setText('')
        self.setText(unicode(value))
        return value

    def get_value(self):
        val = AbstractCustomEditor.get_value(self)
        if val is not None: # we need to distinguish between None
            return val      # and other falsy values
        return unicode(self.toPlainText())


    def set_enabled(self, editable=True):
        self.setEnabled(editable)



