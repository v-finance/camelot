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

from customdelegate import CustomDelegate, DocumentationMetaclass
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QComboBox, QItemDelegate
from PyQt4.QtCore import QVariant, QString, Qt

from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading

class EnumerationDelegate(CustomDelegate):
    """Contrary to the comboboxdelegate, the enumeration delegate does not support dynamic
    choices"""

    __metaclass__ = DocumentationMetaclass
    editor = editors.ChoicesEditor

    def __init__(self, parent, choices, editable=True, **kwargs):
        CustomDelegate.__init__(self, parent, editable=editable, **kwargs)
        self.choices = choices
        self._choices_dict = dict(choices)
        
    def createEditor(self, parent, option, index):
        editor = super(EnumerationDelegate, self).createEditor(parent, option, index)
        editor.set_choices(self.choices)
        return editor

    def paint(self, painter, option, index):
        value = variant_to_pyobject(index.data(Qt.EditRole))
        if value in (None, ValueLoading):
            value = ''        
        painter.save()
        self.paint_text(painter, option, index, unicode(self._choices_dict.get(value, '...')))
        painter.restore()
