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
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading

class IntegerDelegate(CustomDelegate):
    """Custom delegate for integer values"""
  
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.IntegerEditor
  
    def __init__(self,
                 parent=None,
                 unicode_format = None,
                 **kwargs):
  
        CustomDelegate.__init__(self, parent=parent, **kwargs)
        self.unicode_format = unicode_format
        self.locale = QtCore.QLocale()
        
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject(index.model().data(index, Qt.EditRole))
          
        if value in (None, ValueLoading):
            value_str = ''
        else:
            value_str = self.locale.toString( long(value) )

        if self.unicode_format is not None:
            value_str = self.unicode_format(value)
        
        self.paint_text( painter, option, index, value_str, horizontal_align=Qt.AlignRight )
        painter.restore()
