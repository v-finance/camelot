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
from camelot.core.constants import camelot_small_icon_width
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading
from camelot.view.utils import local_date_format

class DateDelegate(CustomDelegate):
    """Custom delegate for date values"""
  
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.DateEditor
    
    def __init__(self, parent=None, **kwargs):
        CustomDelegate.__init__(self, parent, **kwargs)
        self.date_format = local_date_format()
        self._width = self._font_metrics.averageCharWidth() * (len(self.date_format) + 2)  + (camelot_small_icon_width*2)
    
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject( index.model().data( index, Qt.EditRole ) )
        
        value_str = u''
        if value not in (None, ValueLoading):
            value_str = QtCore.QDate(value).toString(self.date_format)
            
        self.paint_text(painter, option, index, value_str, horizontal_align=Qt.AlignRight )
        painter.restore()


