#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================
from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading

class FileDelegate(CustomDelegate):
    """Delegate for :class:`camelot.types.File` columns.  Expects values of type 
    :class:`camelot.core.files.storage.StoredFile`.
    """
    
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.FileEditor
    
    def paint(self, painter, option, index, background_color=QtGui.QColor("white")):
        value = variant_to_pyobject(index.model().data(index, Qt.EditRole))
        text = ''
        if value not in (None, ValueLoading):
            text = value.verbose_name
        self.paint_text(painter, option, index, text)





